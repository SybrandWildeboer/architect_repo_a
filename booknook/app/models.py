"""
BookNook Models - SQLAlchemy database modellen
"""
from datetime import datetime
from app import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    # Naive datetime - geen timezone info
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)

    books = db.relationship('Book', backref='seller', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13))
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # new, good, fair, poor
    category = db.Column(db.String(50))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, reserved, sold
    # Naive datetime - soms UTC, soms lokaal
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    views_count = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)

    reservations = db.relationship('Reservation', backref='book', lazy='dynamic')

    def __repr__(self):
        return f'<Book {self.title}>'


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, expired
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime)
    payment_ref = db.Column(db.String(100))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Reservation {self.id} - {self.status}>'


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    seller_rel = db.relationship('User', foreign_keys=[seller_id])


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Deze gebruikt UTC!

    user = db.relationship('User')
