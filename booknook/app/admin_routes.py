"""
Admin Routes - Beheerderspaneel
Bevat duplicate logica t.o.v. routes.py en book_manager.py
"""
import os
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, jsonify)
from app import db
from app.models import Book, User, Reservation, ActivityLog, Review
from app.book_manager import book_manager
from app.utils import admin_required, format_date, get_categories

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    stats = book_manager.get_dashboard_stats()
    category_breakdown = book_manager.get_category_breakdown()
    top_sellers = book_manager.get_top_sellers()

    # Payment summary - gebruikt de LEGACY processor
    from app.LEGACY_payment_processor import get_payment_summary
    payment_info = get_payment_summary()

    # Recente activiteit
    recent_activity = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()

    return render_template('admin/dashboard.html',
                         stats=stats,
                         categories=category_breakdown,
                         top_sellers=top_sellers,
                         payment_info=payment_info,
                         recent_activity=recent_activity)


@admin_bp.route('/books')
@admin_required
def manage_books():
    """Boeken beheren - duplicate query logica"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')

    # Duplicate query logica - dit zou via book_manager moeten
    query = Book.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)

    query = query.order_by(Book.created_at.desc())
    books = query.paginate(page=page, per_page=25, error_out=False)

    return render_template('admin/dashboard.html',
                         books=books,
                         show_books=True,
                         categories=get_categories(),
                         current_status=status_filter,
                         current_category=category_filter)


@admin_bp.route('/books/<int:book_id>/toggle-featured', methods=['POST'])
@admin_required
def toggle_featured(book_id):
    """Toggle featured status - directe DB operatie"""
    book = db.session.get(Book, book_id)
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('admin.manage_books'))

    book.featured = not book.featured
    book.updated_at = datetime.now()
    db.session.commit()

    status = 'featured' if book.featured else 'unfeatured'
    flash(f'Book {status}: {book.title}', 'success')
    return redirect(url_for('admin.manage_books'))


@admin_bp.route('/books/<int:book_id>/delete', methods=['POST'])
@admin_required
def delete_book(book_id):
    """Verwijder boek - duplicate van book_manager.delete_book"""
    book = db.session.get(Book, book_id)
    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('admin.manage_books'))

    # Duplicate logica: check reserveringen (ook in book_manager)
    pending = Reservation.query.filter_by(
        book_id=book_id, status='pending'
    ).first()
    if pending:
        flash('Cannot delete book with pending reservations', 'warning')
        return redirect(url_for('admin.manage_books'))

    title = book.title
    db.session.delete(book)
    db.session.commit()

    flash(f'Book deleted: {title}', 'success')
    return redirect(url_for('admin.manage_books'))


@admin_bp.route('/users')
@admin_required
def manage_users():
    """Gebruikers beheren"""
    users = User.query.order_by(User.created_at.desc()).all()

    # Voor elke user extra info ophalen - potentieel N+1
    user_data = []
    for user in users:
        book_count = Book.query.filter_by(seller_id=user.id).count()
        res_count = Reservation.query.filter_by(user_id=user.id).count()
        user_data.append({
            'user': user,
            'book_count': book_count,
            'reservation_count': res_count
        })

    return render_template('admin/dashboard.html',
                         users=user_data,
                         show_users=True)


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Toggle admin status"""
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.manage_users'))

    # Voorkom dat je jezelf deadmin maakt
    if user.id == session.get('user_id'):
        flash('Cannot change your own admin status', 'warning')
        return redirect(url_for('admin.manage_users'))

    user.is_admin = not user.is_admin
    db.session.commit()

    status = 'admin' if user.is_admin else 'regular user'
    flash(f'{user.username} is now a {status}', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/reservations')
@admin_required
def manage_reservations():
    """Reserveringen beheren"""
    status_filter = request.args.get('status', '')

    query = Reservation.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    reservations = query.order_by(Reservation.created_at.desc()).all()

    # Check voor verlopen reserveringen
    expired_count = book_manager.check_expired_reservations()
    if expired_count > 0:
        flash(f'{expired_count} reservations expired', 'info')

    return render_template('admin/dashboard.html',
                         reservations=reservations,
                         show_reservations=True,
                         current_status=status_filter)


@admin_bp.route('/reservations/<int:res_id>/confirm', methods=['POST'])
@admin_required
def confirm_reservation(res_id):
    """Bevestig reservering"""
    success, error = book_manager.confirm_reservation(res_id)
    if error:
        flash(error, 'danger')
    else:
        flash('Reservation confirmed', 'success')
    return redirect(url_for('admin.manage_reservations'))


@admin_bp.route('/stats')
@admin_required
def stats():
    """Statistieken pagina"""
    stats = book_manager.get_dashboard_stats()
    categories = book_manager.get_category_breakdown()

    # Omzet per maand - complexe query direct in route
    from sqlalchemy import extract, func
    monthly_revenue = db.session.query(
        extract('month', Reservation.created_at).label('month'),
        func.count(Reservation.id).label('count')
    ).filter(
        Reservation.status == 'confirmed'
    ).group_by('month').all()

    return render_template('admin/dashboard.html',
                         stats=stats,
                         categories=categories,
                         monthly_revenue=monthly_revenue,
                         show_stats=True)


@admin_bp.route('/activity')
@admin_required
def activity_log():
    """Activiteiten log"""
    page = request.args.get('page', 1, type=int)
    logs = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)

    return render_template('admin/dashboard.html',
                         logs=logs,
                         show_activity=True)
