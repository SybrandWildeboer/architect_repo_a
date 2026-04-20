"""
Routes - Mix van class-based en function-based views.
Geen consistente pattern, deels door verschillende developers geschreven.
"""
import os
from datetime import datetime
from flask import (render_template, request, redirect, url_for, flash,
                   session, jsonify, g)
from flask.views import MethodView
from app import db, SESSION_DATA
from app.models import Book, User, Reservation
from app.book_manager import book_manager
from app.utils import (login_required, hash_password, verify_password,
                       format_date, validate_email, sanitize_input,
                       validate_price, get_categories, get_conditions,
                       get_pagination_info, time_ago, truncate_text)


def register_routes(app):
    """Registreer alle routes op de app"""

    @app.route('/')
    def index():
        """Homepage met featured boeken"""
        featured = book_manager.get_featured_books(limit=6)
        stats = book_manager.get_dashboard_stats()
        return render_template('book_list.html',
                             books=featured,
                             stats=stats,
                             page_title='Welcome to BookNook',
                             is_home=True)

    @app.route('/books')
    def book_list():
        """Boeken overzicht met zoek- en filtermogelijkheden"""
        query = request.args.get('q', '')
        category = request.args.get('category', '')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        condition = request.args.get('condition', '')
        sort_by = request.args.get('sort', 'created_at')
        page = request.args.get('page', 1, type=int)

        # Directe gebruik van book_manager (god-class) in route handler
        books = book_manager.search_books(
            query=query or None,
            category=category or None,
            min_price=min_price,
            max_price=max_price,
            condition=condition or None,
            sort_by=sort_by,
            page=page
        )

        return render_template('book_list.html',
                             books=books.items,
                             pagination=get_pagination_info(books),
                             query=query,
                             category=category,
                             categories=get_categories(),
                             conditions=get_conditions(),
                             page_title='Browse Books')

    @app.route('/books/<int:book_id>')
    def book_detail(book_id):
        """Boek detail pagina"""
        # Dit verhoogt ook views_count (side effect in getter!)
        book = book_manager.get_book(book_id)
        if not book:
            flash('Book not found', 'danger')
            return redirect(url_for('book_list'))

        # Haal seller rating op
        seller_rating = book_manager.get_seller_rating(book.seller_id)

        # Check of huidige user dit boek al gereserveerd heeft
        has_reservation = False
        if g.current_user:
            has_reservation = Reservation.query.filter_by(
                book_id=book_id,
                user_id=g.current_user.id,
                status='pending'
            ).first() is not None

        # Aanbevelingen - meer queries
        recommendations = book_manager.get_recommendations(
            g.current_user.id if g.current_user else 0, limit=4
        )

        return render_template('book_detail.html',
                             book=book,
                             seller_rating=seller_rating,
                             has_reservation=has_reservation,
                             recommendations=recommendations,
                             time_ago=time_ago)

    @app.route('/books/new', methods=['GET', 'POST'])
    @login_required
    def create_book():
        """Nieuw boek aanmaken"""
        if request.method == 'POST':
            title = sanitize_input(request.form.get('title', ''))
            author = sanitize_input(request.form.get('author', ''))
            isbn = request.form.get('isbn', '').strip()
            description = sanitize_input(request.form.get('description', ''))
            price_str = request.form.get('price', '')
            condition = request.form.get('condition', '')
            category = request.form.get('category', '')

            # Validatie in de route handler (verkeerde laag!)
            price, error = validate_price(price_str)
            if error:
                flash(error, 'danger')
                return render_template('book_detail.html',
                                     editing=True,
                                     categories=get_categories(),
                                     conditions=get_conditions())

            # ISBN validatie ook hier (en ook in BookManager...)
            if isbn and not book_manager.validate_isbn(isbn):
                flash('Invalid ISBN', 'danger')
                return render_template('book_detail.html',
                                     editing=True,
                                     categories=get_categories(),
                                     conditions=get_conditions())

            book, error = book_manager.create_book(
                title=title,
                author=author,
                isbn=isbn,
                description=description,
                price=price,
                condition=condition,
                category=category,
                seller_id=session['user_id']
            )

            if error:
                flash(error, 'danger')
                return render_template('book_detail.html',
                                     editing=True,
                                     categories=get_categories(),
                                     conditions=get_conditions())

            flash('Book listed successfully!', 'success')
            return redirect(url_for('book_detail', book_id=book.id))

        return render_template('book_detail.html',
                             editing=True,
                             categories=get_categories(),
                             conditions=get_conditions())

    @app.route('/books/<int:book_id>/reserve', methods=['POST'])
    @login_required
    def reserve_book(book_id):
        """Reserveer een boek"""
        reservation, error = book_manager.reserve_book(book_id, session['user_id'])
        if error:
            flash(error, 'danger')
        else:
            flash('Book reserved! You have 48 hours to complete the purchase.', 'success')
        return redirect(url_for('book_detail', book_id=book_id))

    @app.route('/reservations')
    @login_required
    def my_reservations():
        """Overzicht van mijn reserveringen"""
        reservations = book_manager.get_user_reservations(session['user_id'])
        return render_template('book_list.html',
                             reservations=reservations,
                             page_title='My Reservations',
                             show_reservations=True)

    @app.route('/reservations/<int:res_id>/cancel', methods=['POST'])
    @login_required
    def cancel_reservation(res_id):
        """Annuleer een reservering"""
        success, error = book_manager.cancel_reservation(res_id, session['user_id'])
        if error:
            flash(error, 'danger')
        else:
            flash('Reservation cancelled', 'info')
        return redirect(url_for('my_reservations'))

    # ===================== AUTH ROUTES =====================

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login pagina"""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Please fill in all fields', 'danger')
                return render_template('base.html', show_login=True)

            # Directe DB query in route handler
            user = User.query.filter_by(username=username).first()

            if user and verify_password(password, user.password_hash):
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_admin'] = user.is_admin

                # Update last login - timezone inconsistentie
                user.last_login = datetime.now()  # Lokale tijd
                db.session.commit()

                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'danger')

        return render_template('base.html', show_login=True)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Registratie pagina"""
        if request.method == 'POST':
            username = sanitize_input(request.form.get('username', ''))
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')

            # Validatie verspreid - deels hier, deels in utils
            errors = []
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters')
            if not validate_email(email):
                errors.append('Invalid email address')
            if len(password) < 6:
                errors.append('Password must be at least 6 characters')
            if password != password_confirm:
                errors.append('Passwords do not match')

            # Check bestaande user - directe DB query
            if User.query.filter_by(username=username).first():
                errors.append('Username already taken')
            if User.query.filter_by(email=email).first():
                errors.append('Email already registered')

            if errors:
                for e in errors:
                    flash(e, 'danger')
                return render_template('base.html', show_register=True)

            # Maak user aan - directe DB operatie in route
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                created_at=datetime.now()
            )
            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = False

            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))

        return render_template('base.html', show_register=True)

    @app.route('/logout')
    def logout():
        """Uitloggen"""
        user_id = session.get('user_id')
        session.clear()
        if user_id:
            SESSION_DATA.pop(f'user_{user_id}', None)
        flash('You have been logged out', 'info')
        return redirect(url_for('index'))

    @app.route('/profile')
    @login_required
    def profile():
        """Profiel pagina"""
        user = g.current_user
        my_books = Book.query.filter_by(seller_id=user.id).all()
        my_reservations = Reservation.query.filter_by(user_id=user.id).all()
        seller_rating = book_manager.get_seller_rating(user.id)

        return render_template('base.html',
                             show_profile=True,
                             user=user,
                             my_books=my_books,
                             my_reservations=my_reservations,
                             seller_rating=seller_rating)

    # ===================== API ENDPOINTS (class-based) =====================
    # Inconsistentie: sommige routes zijn function-based, deze zijn class-based

    class BookAPIView(MethodView):
        """API endpoint voor boeken - class-based view"""

        def get(self, book_id=None):
            if book_id:
                book = book_manager.get_book(book_id)
                if not book:
                    return jsonify({'error': 'Not found'}), 404
                return jsonify({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'price': book.price,
                    'condition': book.condition,
                    'status': book.status
                })
            else:
                page = request.args.get('page', 1, type=int)
                books = book_manager.search_books(page=page, per_page=10)
                return jsonify({
                    'books': [{
                        'id': b.id,
                        'title': b.title,
                        'author': b.author,
                        'price': b.price
                    } for b in books.items],
                    'total': books.total
                })

        def post(self):
            """Maak boek via API - duplicate validatie logica"""
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            book, error = book_manager.create_book(
                title=data.get('title', ''),
                author=data.get('author', ''),
                isbn=data.get('isbn', ''),
                description=data.get('description', ''),
                price=float(data.get('price', 0)),
                condition=data.get('condition', 'good'),
                category=data.get('category', 'other'),
                seller_id=session['user_id']
            )

            if error:
                return jsonify({'error': error}), 400
            return jsonify({'id': book.id, 'title': book.title}), 201

        def delete(self, book_id):
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            success, error = book_manager.delete_book(book_id, session['user_id'])
            if error:
                return jsonify({'error': error}), 400
            return jsonify({'message': 'Deleted'}), 200

    # Register class-based view
    book_api = BookAPIView.as_view('book_api')
    app.add_url_rule('/api/books', view_func=book_api, methods=['GET', 'POST'])
    app.add_url_rule('/api/books/<int:book_id>', view_func=book_api,
                     methods=['GET', 'DELETE'])

    # Maar de search API is weer function-based...
    @app.route('/api/search')
    def api_search():
        """Zoek API - function-based, inconsistent met BookAPIView"""
        q = request.args.get('q', '')
        if len(q) < 2:
            return jsonify({'results': []})

        books = book_manager.search_books(query=q, per_page=5)
        results = [{
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'price': format_price_raw(b.price)
        } for b in books.items]
        return jsonify({'results': results})


def format_price_raw(price):
    """Helper die hier staat i.p.v. in utils (inconsistentie)"""
    return f"€{price:.2f}"
