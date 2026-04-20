"""
BookManager - Centrale klasse voor alle boek-gerelateerde operaties.
Oorspronkelijk geschreven door de eerste developer, sindsdien uitgebreid
door meerdere freelancers.

# TODO: refactor this mess
"""
import os
import re
from datetime import datetime, timedelta
from app import db, SESSION_DATA, ACTIVE_RESERVATIONS
from app.models import Book, User, Reservation, Review, ActivityLog


class BookManager:
    """
    Beheert alle boek-operaties: CRUD, pricing, notificaties, zoeken,
    aanbevelingen, statistieken, en meer.

    # TODO: refactor this mess
    # ^^ Eigenlijk is deze class goed opgezet qua pricing logic hieronder,
    # het probleem zit in de omvang en verantwoordelijkheden, niet in de
    # individuele methodes.
    """

    CONDITION_MULTIPLIERS = {
        'new': 1.0,
        'good': 0.75,
        'fair': 0.5,
        'poor': 0.25
    }

    CATEGORY_DEMAND = {
        'fiction': 1.2,
        'non-fiction': 1.0,
        'textbook': 1.5,
        'children': 0.8,
        'comics': 1.3,
        'science': 1.1,
        'history': 0.9,
        'cooking': 1.0,
        'travel': 0.7,
        'other': 0.8
    }

    def __init__(self):
        self._cache = {}
        self._notification_queue = []

    # ==================== CRUD OPERATIES ====================

    def create_book(self, title, author, isbn, description, price, condition,
                    category, seller_id):
        """Maak een nieuw boek aan"""
        # Validatie hier (in plaats van in een aparte validatie-laag)
        if not title or len(title) < 2:
            return None, "Title must be at least 2 characters"
        if not author:
            return None, "Author is required"
        if price <= 0:
            return None, "Price must be positive"
        if price > 500:
            return None, "Price cannot exceed €500"
        if condition not in self.CONDITION_MULTIPLIERS:
            return None, f"Invalid condition: {condition}"

        # Directe DB operatie
        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            description=description,
            price=price,
            condition=condition,
            category=category or 'other',
            seller_id=seller_id
        )
        db.session.add(book)
        db.session.commit()

        # Log de actie
        self._log_activity(seller_id, 'book_created',
                          f'Created book: {title}')

        # Notificatie naar admins
        self._notify_admins_new_book(book)

        return book, None

    def get_book(self, book_id):
        """Haal een boek op met ID"""
        book = db.session.get(Book, book_id)
        if book:
            # Verhoog views - direct DB update in getter
            book.views_count = (book.views_count or 0) + 1
            db.session.commit()
        return book

    def update_book(self, book_id, **kwargs):
        """Update boek gegevens"""
        book = db.session.get(Book, book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")

        for key, value in kwargs.items():
            if hasattr(book, key):
                setattr(book, key, value)

        book.updated_at = datetime.now()
        db.session.commit()
        return book

    def delete_book(self, book_id, user_id):
        """Verwijder een boek - alleen door eigenaar of admin"""
        book = db.session.get(Book, book_id)
        if not book:
            return False, "Book not found"

        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"

        if book.seller_id != user_id and not user.is_admin:
            return False, "Not authorized"

        # Check voor actieve reserveringen
        active_res = Reservation.query.filter_by(
            book_id=book_id, status='pending'
        ).first()
        if active_res:
            return False, "Cannot delete book with active reservations"

        db.session.delete(book)
        db.session.commit()
        self._log_activity(user_id, 'book_deleted', f'Deleted book: {book.title}')
        return True, None

    # ==================== ZOEK FUNCTIONALITEIT ====================

    def search_books(self, query=None, category=None, min_price=None,
                     max_price=None, condition=None, sort_by='created_at',
                     page=1, per_page=20):
        """
        Zoek boeken met filters.
        Let op: SQLite is case-insensitive voor LIKE, PostgreSQL niet!
        Deze query werkt in SQLite maar geeft andere resultaten in PostgreSQL.
        """
        q = Book.query.filter(Book.status == 'available')

        if query:
            # Dit werkt case-insensitive in SQLite maar NIET in PostgreSQL
            search_term = f'%{query}%'
            q = q.filter(
                db.or_(
                    Book.title.like(search_term),
                    Book.author.like(search_term),
                    Book.description.like(search_term)
                )
            )

        if category:
            q = q.filter(Book.category == category)

        if min_price is not None:
            q = q.filter(Book.price >= min_price)
        if max_price is not None:
            q = q.filter(Book.price <= max_price)

        if condition:
            q = q.filter(Book.condition == condition)

        # Sorting
        if sort_by == 'price_asc':
            q = q.order_by(Book.price.asc())
        elif sort_by == 'price_desc':
            q = q.order_by(Book.price.desc())
        elif sort_by == 'title':
            q = q.order_by(Book.title.asc())
        else:
            q = q.order_by(Book.created_at.desc())

        # N+1 query probleem: we laden boeken, maar in de template
        # wordt voor elk boek apart de seller opgehaald
        books = q.paginate(page=page, per_page=per_page, error_out=False)
        return books

    def get_recommendations(self, user_id, limit=5):
        """Aanbevelingen op basis van eerdere reserveringen"""
        # Haal categorieën op van eerder gereserveerde boeken
        user_reservations = Reservation.query.filter_by(user_id=user_id).all()
        if not user_reservations:
            # Geen historie, geef populaire boeken
            return Book.query.filter_by(status='available').order_by(
                Book.views_count.desc()
            ).limit(limit).all()

        # Verzamel categorieën (N+1 query hier ook)
        categories = []
        for res in user_reservations:
            book = db.session.get(Book, res.book_id)
            if book:
                categories.append(book.category)

        if not categories:
            return []

        # Vind boeken in dezelfde categorieën
        from collections import Counter
        cat_counts = Counter(categories)
        top_cats = [cat for cat, _ in cat_counts.most_common(3)]

        return Book.query.filter(
            Book.status == 'available',
            Book.category.in_(top_cats)
        ).order_by(Book.created_at.desc()).limit(limit).all()

    # ==================== PRICING LOGIC ====================
    # TODO: refactor this mess
    # ^^ Nee, deze pricing logic is eigenlijk correct en goed gestructureerd.
    # De multipliers en berekening zijn helder. Het echte probleem is dat
    # pricing logic in dezelfde class zit als CRUD, search, en notifications.

    def calculate_suggested_price(self, original_price, condition, category,
                                  age_years=0):
        """
        Bereken een suggestieprijs voor een tweedehands boek.
        Gebaseerd op conditie, categorie-vraag, en leeftijd.
        """
        if original_price <= 0:
            return 0.0

        # Conditie factor
        condition_factor = self.CONDITION_MULTIPLIERS.get(condition, 0.5)

        # Categorie vraag factor
        demand_factor = self.CATEGORY_DEMAND.get(category, 0.8)

        # Leeftijd afschrijving: 5% per jaar, max 50%
        age_depreciation = min(age_years * 0.05, 0.50)
        age_factor = 1.0 - age_depreciation

        # Bereken finale prijs
        suggested = original_price * condition_factor * demand_factor * age_factor

        # Minimum prijs: €0.50
        suggested = max(suggested, 0.50)

        # Afronden op 2 decimalen
        return round(suggested, 2)

    def get_price_statistics(self, category=None):
        """Verkrijg prijsstatistieken voor een categorie"""
        q = Book.query.filter_by(status='available')
        if category:
            q = q.filter_by(category=category)

        books = q.all()
        if not books:
            return {'avg': 0, 'min': 0, 'max': 0, 'count': 0}

        prices = [b.price for b in books]
        return {
            'avg': round(sum(prices) / len(prices), 2),
            'min': min(prices),
            'max': max(prices),
            'count': len(prices)
        }

    def apply_bulk_discount(self, book_ids, discount_percentage):
        """Pas korting toe op meerdere boeken"""
        if discount_percentage < 0 or discount_percentage > 50:
            return False, "Discount must be between 0 and 50%"

        updated = 0
        for book_id in book_ids:
            book = db.session.get(Book, book_id)
            if book and book.status == 'available':
                book.price = round(book.price * (1 - discount_percentage / 100), 2)
                updated += 1

        db.session.commit()
        return True, f"Updated {updated} books"

    # ==================== RESERVERINGEN ====================

    def reserve_book(self, book_id, user_id):
        """
        Reserveer een boek.
        RACE CONDITION: Er is geen locking, twee users kunnen
        tegelijk hetzelfde boek reserveren.
        """
        book = db.session.get(Book, book_id)
        if not book:
            return None, "Book not found"

        if book.status != 'available':
            return None, "Book is not available"

        if book.seller_id == user_id:
            return None, "Cannot reserve your own book"

        # Check max reserveringen - leest direct uit env
        max_res = int(os.environ.get('MAX_RESERVATIONS_PER_USER', '5'))
        current_res = Reservation.query.filter_by(
            user_id=user_id, status='pending'
        ).count()
        if current_res >= max_res:
            return None, f"Maximum {max_res} active reservations allowed"

        # RACE CONDITION: Tussen de check hierboven en de update hieronder
        # kan een andere request hetzelfde boek reserveren.
        # Er is geen database-level lock of optimistic concurrency control.

        # Update boek status
        book.status = 'reserved'
        book.updated_at = datetime.now()

        # Maak reservering
        reservation = Reservation(
            book_id=book_id,
            user_id=user_id,
            status='pending',
            expires_at=datetime.now() + timedelta(hours=48)
        )
        db.session.add(reservation)
        db.session.commit()

        # Cache bijwerken
        ACTIVE_RESERVATIONS[book_id] = {
            'user_id': user_id,
            'reserved_at': datetime.now()
        }

        # Notificatie
        self._notify_seller_reservation(book, user_id)

        # Payment processing
        self._initiate_payment_hold(reservation)

        self._log_activity(user_id, 'book_reserved',
                          f'Reserved: {book.title}')

        return reservation, None

    def cancel_reservation(self, reservation_id, user_id):
        """Annuleer een reservering"""
        reservation = db.session.get(Reservation, reservation_id)
        if not reservation:
            return False, "Reservation not found"

        if reservation.user_id != user_id:
            return False, "Not authorized"

        if reservation.status != 'pending':
            return False, "Can only cancel pending reservations"

        reservation.status = 'cancelled'
        reservation.book.status = 'available'
        db.session.commit()

        # Verwijder uit cache
        ACTIVE_RESERVATIONS.pop(reservation.book_id, None)

        self._log_activity(user_id, 'reservation_cancelled',
                          f'Cancelled reservation for: {reservation.book.title}')

        return True, None

    def confirm_reservation(self, reservation_id):
        """Bevestig een reservering (na betaling)"""
        reservation = db.session.get(Reservation, reservation_id)
        if not reservation:
            return False, "Reservation not found"

        reservation.status = 'confirmed'
        reservation.book.status = 'sold'
        db.session.commit()

        self._log_activity(reservation.user_id, 'reservation_confirmed',
                          f'Confirmed: {reservation.book.title}')

        return True, None

    def get_user_reservations(self, user_id):
        """Haal alle reserveringen op voor een user"""
        return Reservation.query.filter_by(user_id=user_id).order_by(
            Reservation.created_at.desc()
        ).all()

    def check_expired_reservations(self):
        """Controleer en verloop verlopen reserveringen"""
        expired = Reservation.query.filter(
            Reservation.status == 'pending',
            Reservation.expires_at < datetime.now()
        ).all()

        for res in expired:
            res.status = 'expired'
            res.book.status = 'available'
            ACTIVE_RESERVATIONS.pop(res.book_id, None)

        if expired:
            db.session.commit()

        return len(expired)

    # ==================== NOTIFICATIES ====================

    def _notify_admins_new_book(self, book):
        """Stuur notificatie naar admins over nieuw boek"""
        admin_email = os.environ.get('ADMIN_EMAIL')
        if not admin_email:
            return

        notification_enabled = os.environ.get('NOTIFICATION_ENABLED', 'false')
        if notification_enabled.lower() != 'true':
            return

        # In een echt systeem zou dit een email sturen
        self._notification_queue.append({
            'type': 'new_book',
            'to': admin_email,
            'book_id': book.id,
            'title': book.title,
            'timestamp': datetime.now()
        })

    def _notify_seller_reservation(self, book, buyer_id):
        """Notificeer verkoper over reservering"""
        buyer = db.session.get(User, buyer_id)
        self._notification_queue.append({
            'type': 'reservation',
            'to_user_id': book.seller_id,
            'from_user': buyer.username if buyer else 'Unknown',
            'book_title': book.title,
            'timestamp': datetime.now()
        })

    def get_notifications(self, user_id):
        """Haal notificaties op - uit de in-memory queue"""
        return [n for n in self._notification_queue
                if n.get('to_user_id') == user_id]

    # ==================== STATISTIEKEN ====================

    def get_dashboard_stats(self):
        """Statistieken voor het admin dashboard"""
        total_books = Book.query.count()
        available_books = Book.query.filter_by(status='available').count()
        total_users = User.query.count()
        total_reservations = Reservation.query.count()
        pending_reservations = Reservation.query.filter_by(status='pending').count()

        # Omzet berekening - simplistisch
        confirmed = Reservation.query.filter_by(status='confirmed').all()
        total_revenue = sum(r.book.price for r in confirmed if r.book)

        return {
            'total_books': total_books,
            'available_books': available_books,
            'total_users': total_users,
            'total_reservations': total_reservations,
            'pending_reservations': pending_reservations,
            'total_revenue': round(total_revenue, 2)
        }

    def get_category_breakdown(self):
        """Verdeling van boeken per categorie"""
        categories = db.session.query(
            Book.category, db.func.count(Book.id)
        ).group_by(Book.category).all()

        return {cat: count for cat, count in categories}

    def get_top_sellers(self, limit=10):
        """Top verkopers op basis van aantal verkochte boeken"""
        sellers = db.session.query(
            User.username,
            db.func.count(Book.id).label('book_count')
        ).join(Book, Book.seller_id == User.id).filter(
            Book.status == 'sold'
        ).group_by(User.username).order_by(
            db.desc('book_count')
        ).limit(limit).all()

        return [{'username': s.username, 'count': s.book_count} for s in sellers]

    # ==================== REVIEWS ====================

    def add_review(self, reviewer_id, seller_id, rating, comment):
        """Voeg een review toe voor een verkoper"""
        if rating < 1 or rating > 5:
            return None, "Rating must be between 1 and 5"

        if reviewer_id == seller_id:
            return None, "Cannot review yourself"

        review = Review(
            reviewer_id=reviewer_id,
            seller_id=seller_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()

        return review, None

    def get_seller_rating(self, seller_id):
        """Gemiddelde rating voor een verkoper"""
        reviews = Review.query.filter_by(seller_id=seller_id).all()
        if not reviews:
            return None

        avg = sum(r.rating for r in reviews) / len(reviews)
        return round(avg, 1)

    # ==================== INTERNE HELPERS ====================

    def _log_activity(self, user_id, action, details=None):
        """Log een activiteit"""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details
        )
        db.session.add(log)
        # Niet committen hier - wordt in de aanroepende functie gedaan
        # Behalve... soms wel. Inconsistent.
        try:
            db.session.commit()
        except Exception:
            pass  # Logging mag niet falen

    def _initiate_payment_hold(self, reservation):
        """Start een payment hold voor de reservering"""
        # Late import om circulaire import te vermijden
        from app.LEGACY_payment_processor import process_hold
        result = process_hold(reservation.id, reservation.book.price)
        if result:
            reservation.payment_ref = result.get('reference')
            db.session.commit()

    def get_featured_books(self, limit=6):
        """Haal featured boeken op voor de homepage"""
        featured = Book.query.filter_by(
            featured=True, status='available'
        ).limit(limit).all()

        # Als er niet genoeg featured boeken zijn, vul aan
        if len(featured) < limit:
            extra = Book.query.filter_by(
                status='available'
            ).filter(
                ~Book.id.in_([b.id for b in featured])
            ).order_by(Book.views_count.desc()).limit(
                limit - len(featured)
            ).all()
            featured.extend(extra)

        return featured

    def validate_isbn(self, isbn):
        """Valideer een ISBN-10 of ISBN-13"""
        if not isbn:
            return True  # ISBN is optioneel

        isbn = isbn.replace('-', '').replace(' ', '')

        if len(isbn) == 10:
            return self._validate_isbn10(isbn)
        elif len(isbn) == 13:
            return self._validate_isbn13(isbn)
        return False

    def _validate_isbn10(self, isbn):
        """Valideer ISBN-10 checksum"""
        if not re.match(r'^\d{9}[\dXx]$', isbn):
            return False
        total = sum((10 - i) * (10 if c in 'Xx' else int(c))
                    for i, c in enumerate(isbn))
        return total % 11 == 0

    def _validate_isbn13(self, isbn):
        """Valideer ISBN-13 checksum"""
        if not isbn.isdigit():
            return False
        total = sum(int(c) * (1 if i % 2 == 0 else 3)
                    for i, c in enumerate(isbn))
        return total % 10 == 0


# Singleton instance - wordt overal geïmporteerd
book_manager = BookManager()
