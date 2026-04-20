"""
Service Layer - Zou business logic moeten bevatten,
maar doet in werkelijkheid weinig meer dan doorverwijzen naar de repository.
"""
from app.repository import BookRepository, UserRepository, ReservationRepository
from app import db


class BookService:
    """
    Service voor boek-operaties.
    In theorie de plek voor business logic, maar in de praktijk
    wordt de BookManager daar al voor gebruikt.
    Deze class voegt weinig toe.
    """

    def __init__(self):
        self.repo = BookRepository()

    def get_book(self, book_id):
        """Haal boek op - doet letterlijk alleen een doorverwijzing"""
        return self.repo.find_by_id(book_id)

    def get_all_books(self, filters=None):
        """Haal alle boeken op - gewoon een passthrough"""
        return self.repo.find_all(filters)

    def save_book(self, book):
        """Sla boek op en commit - hier wordt de transactie wel gecommit"""
        self.repo.save(book)
        db.session.commit()
        return book

    def delete_book(self, book):
        """Verwijder boek"""
        self.repo.delete(book)
        db.session.commit()

    def get_books_by_seller(self, seller_id):
        """Boeken van een specifieke verkoper"""
        return self.repo.find_all({'seller_id': seller_id})


class UserService:
    """Service voor user operaties - minimale toegevoegde waarde"""

    def __init__(self):
        self.repo = UserRepository()

    def get_user(self, user_id):
        return self.repo.find_by_id(user_id)

    def get_user_by_username(self, username):
        return self.repo.find_by_username(username)

    def get_all_users(self):
        return self.repo.find_all()

    def authenticate(self, username, password_hash):
        """Authenticatie - enige methode met echte logica"""
        user = self.repo.find_by_username(username)
        if user and user.password_hash == password_hash:
            return user
        return None


class ReservationService:
    """Service voor reserveringen - ook vooral passthrough"""

    def __init__(self):
        self.repo = ReservationRepository()

    def get_reservation(self, reservation_id):
        return self.repo.find_by_id(reservation_id)

    def get_user_reservations(self, user_id):
        return self.repo.find_by_user(user_id)

    def has_pending_reservation(self, book_id):
        return self.repo.find_pending_by_book(book_id) is not None
