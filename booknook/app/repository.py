"""
Repository layer - Abstractie over de database.
Zou domain objects moeten teruggeven, maar geeft ORM objecten terug.
"""
from app import db
from app.models import Book, User, Reservation, Review


class BookRepository:
    """
    Repository voor boek-operaties.
    PROBLEEM: Geeft SQLAlchemy model objecten terug i.p.v. domain objects.
    De caller moet weten hoe SQLAlchemy werkt (lazy loading, session scope, etc.)
    """

    def find_all(self, filters=None):
        """Vind alle boeken met optionele filters"""
        query = Book.query
        if filters:
            if 'status' in filters:
                query = query.filter_by(status=filters['status'])
            if 'category' in filters:
                query = query.filter_by(category=filters['category'])
            if 'seller_id' in filters:
                query = query.filter_by(seller_id=filters['seller_id'])
        return query.all()  # Returns ORM objects, niet domain objects

    def find_by_id(self, book_id):
        """Vind boek op ID - geeft ORM object terug"""
        return db.session.get(Book, book_id)

    def save(self, book):
        """Sla boek op - de transactie lekt naar de caller"""
        db.session.add(book)
        # Geen commit hier! Caller moet zelf committen.
        # Dit lekt transactie-verantwoordelijkheid naar de view laag.
        return book

    def delete(self, book):
        """Verwijder boek"""
        db.session.delete(book)
        # Weer geen commit

    def find_by_isbn(self, isbn):
        """Zoek boek op ISBN"""
        return Book.query.filter_by(isbn=isbn).first()

    def count_by_seller(self, seller_id):
        """Tel boeken van een verkoper"""
        return Book.query.filter_by(seller_id=seller_id).count()


class UserRepository:
    """Repository voor user operaties"""

    def find_by_id(self, user_id):
        return db.session.get(User, user_id)

    def find_by_username(self, username):
        return User.query.filter_by(username=username).first()

    def find_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def save(self, user):
        db.session.add(user)
        return user

    def find_all(self):
        return User.query.all()


class ReservationRepository:
    """Repository voor reservering operaties"""

    def find_by_id(self, reservation_id):
        return db.session.get(Reservation, reservation_id)

    def find_by_user(self, user_id):
        return Reservation.query.filter_by(user_id=user_id).all()

    def find_pending_by_book(self, book_id):
        return Reservation.query.filter_by(
            book_id=book_id, status='pending'
        ).first()

    def save(self, reservation):
        db.session.add(reservation)
        return reservation

    def count_pending_by_user(self, user_id):
        return Reservation.query.filter_by(
            user_id=user_id, status='pending'
        ).count()
