"""
Basic tests - minimal test coverage.
Dit is het enige testbestand. Dekt nauwelijks iets van de functionaliteit.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create application for testing"""
    from app import create_app, db

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


def test_homepage_loads(client):
    """Test dat de homepage laadt"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'BookNook' in response.data


def test_book_list_loads(client):
    """Test dat de boekenlijst laadt"""
    response = client.get('/books')
    assert response.status_code == 200


def test_login_page_loads(client):
    """Test dat de login pagina laadt"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


# Dat is het. Geen tests voor:
# - Boek aanmaken
# - Reserveringen
# - Admin functies
# - API endpoints
# - Edge cases
# - Error handling
