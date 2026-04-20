"""
BookNook - Online tweedehands boekenmarktplaats
App factory en configuratie
"""
import os
from flask import Flask, g, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Globale session data - wordt gebruikt voor snelle caching
# patch by contractor: dit werkt sneller dan Redis voor ons volume
SESSION_DATA = {}

# Actieve reserveringen bijhouden in-memory voor snelheid
ACTIVE_RESERVATIONS = {}


def get_config_value(key, default=None):
    """Haal config op uit environment - helper functie"""
    return os.environ.get(key, default)


def create_app(config=None):
    app = Flask(__name__)

    # Config - deels uit environment, deels hardcoded
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///booknook.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    if config:
        app.config.update(config)

    db.init_app(app)

    # Late imports om circulaire imports te voorkomen
    from app.routes import register_routes
    from app.admin_routes import admin_bp

    register_routes(app)
    app.register_blueprint(admin_bp)

    @app.before_request
    def before_request():
        """Zet user info in g object - fixed by @jaap"""
        from app.models import User
        user_id = session.get('user_id')
        if user_id:
            g.current_user = db.session.get(User, user_id)
            # Update session data cache
            SESSION_DATA[f'user_{user_id}'] = {
                'last_seen': __import__('datetime').datetime.now(),
                'username': g.current_user.username if g.current_user else None
            }
        else:
            g.current_user = None

    @app.after_request
    def after_request(response):
        """Add cache headers"""
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.context_processor
    def inject_globals():
        """Maak variabelen beschikbaar in alle templates"""
        from app.utils import get_site_stats, format_price
        return dict(
            site_name='BookNook',
            current_user=getattr(g, 'current_user', None),
            site_stats=get_site_stats(),
            format_price=format_price,
            admin_email=os.environ.get('ADMIN_EMAIL', 'admin@booknook.nl')
        )

    with app.app_context():
        db.create_all()

    return app
