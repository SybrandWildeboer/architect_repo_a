"""
Utility functies - verzameling van ongerelateerde helpers.
Oorspronkelijk begonnen als 2-3 functies, uitgegroeid tot een grab-bag
van alles wat nergens anders paste.
"""
import os
import re
import hashlib
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash, request


# ===================== AUTHENTICATIE HELPERS =====================

def login_required(f):
    """Decorator om login te vereisen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator om admin rechten te vereisen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'warning')
            return redirect(url_for('login'))
        # Late import
        from app.models import User
        from app import db
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def hash_password(password):
    """Hash een wachtwoord - simpele SHA256 (niet veilig voor productie maar ok voor demo)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Verifieer een wachtwoord tegen een hash"""
    return hash_password(password) == password_hash


# ===================== FORMATTING HELPERS =====================

def format_price(price):
    """Formatteer prijs als euro bedrag"""
    if price is None:
        return "€0.00"
    return f"€{price:.2f}"


def format_date(dt):
    """Formatteer datetime voor weergave"""
    if not dt:
        return "Unknown"
    # Gebruikt lokale tijd zonder timezone conversie
    return dt.strftime("%d %b %Y, %H:%M")


def format_date_short(dt):
    """Korte datum formatting"""
    if not dt:
        return ""
    return dt.strftime("%d-%m-%Y")


def time_ago(dt):
    """Bereken 'X tijd geleden' string"""
    if not dt:
        return "unknown"

    # BUG: dt kan UTC zijn (ActivityLog) of lokaal (Book.created_at)
    # maar we vergelijken altijd met datetime.now() (lokaal)
    now = datetime.now()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


# ===================== VALIDATIE HELPERS =====================

def validate_email(email):
    """Valideer email adres"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_isbn(isbn):
    """Valideer ISBN - duplicaat van BookManager.validate_isbn"""
    if not isbn:
        return True
    isbn = isbn.replace('-', '').replace(' ', '')
    return len(isbn) in (10, 13)


def sanitize_input(text):
    """Basis input sanitization"""
    if not text:
        return text
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def validate_price(price_str):
    """Valideer en parse een prijs string"""
    try:
        price = float(price_str)
        if price <= 0:
            return None, "Price must be positive"
        if price > 500:
            return None, "Price too high"
        return price, None
    except (ValueError, TypeError):
        return None, "Invalid price format"


# ===================== STRING HELPERS =====================

def generate_reference(prefix='BN'):
    """Genereer een unieke referentie code"""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{random_part}"


def truncate_text(text, max_length=100):
    """Kort tekst in met ellipsis"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def slugify(text):
    """Maak een URL-friendly slug van tekst"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


# ===================== SITE HELPERS =====================

def get_site_stats():
    """Haal site statistieken op voor de footer"""
    # Late import vanwege circulaire dependencies
    from app.models import Book, User
    from app import db
    try:
        return {
            'total_books': Book.query.filter_by(status='available').count(),
            'total_users': User.query.count()
        }
    except Exception:
        return {'total_books': 0, 'total_users': 0}


def get_categories():
    """Beschikbare categorieën"""
    return [
        'fiction', 'non-fiction', 'textbook', 'children',
        'comics', 'science', 'history', 'cooking', 'travel', 'other'
    ]


def get_conditions():
    """Beschikbare condities"""
    return ['new', 'good', 'fair', 'poor']


# ===================== PAGINATION HELPER =====================

def get_pagination_info(pagination):
    """Helper om pagination info te extraheren"""
    return {
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num
    }


# ===================== DIVERSE HELPERS =====================

def is_valid_condition(condition):
    """Check of een conditie geldig is"""
    return condition in get_conditions()


def calculate_shipping_estimate(weight_grams=500):
    """Schat verzendkosten - hardcoded voor Nederland"""
    if weight_grams <= 100:
        return 1.59
    elif weight_grams <= 350:
        return 2.19
    elif weight_grams <= 2000:
        return 4.39
    else:
        return 6.95


def get_random_color():
    """Random kleur voor avatar placeholders"""
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
              '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    return random.choice(colors)


def mask_email(email):
    """Mask email voor privacy"""
    if not email or '@' not in email:
        return email
    local, domain = email.split('@')
    if len(local) <= 2:
        masked = local[0] + '*'
    else:
        masked = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked}@{domain}"


def days_until_expiry(expires_at):
    """Bereken dagen tot vervaldatum"""
    if not expires_at:
        return 0
    diff = expires_at - datetime.now()
    return max(0, diff.days)
