"""
Seed script - Vult de database met testdata.
Draai met: python seed.py

fixed by @jaap - 2023-03-15
patch by contractor - added more test books
"""
import os
import sys

# Zorg dat we in de juiste directory zitten
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Book, User, Reservation, Review, ActivityLog
from app.utils import hash_password
from datetime import datetime, timedelta
import random


def seed_database():
    """Vul de database met testdata"""
    app = create_app()

    with app.app_context():
        # Maak tabellen aan
        db.create_all()

        # Check of er al data is
        if User.query.first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # ==================== USERS ====================
        users = [
            User(username='admin', email='admin@booknook.nl',
                 password_hash=hash_password('admin123'),
                 is_admin=True, created_at=datetime(2021, 1, 15)),
            User(username='jan', email='jan@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2021, 3, 10)),
            User(username='marie', email='marie@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2021, 5, 22)),
            User(username='pieter', email='pieter@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2021, 8, 1)),
            User(username='sophie', email='sophie@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2022, 1, 14)),
            User(username='thomas', email='thomas@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2022, 4, 3)),
            User(username='emma', email='emma@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2022, 7, 19)),
            User(username='lucas', email='lucas@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2022, 11, 5)),
            User(username='lisa', email='lisa@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2023, 2, 28)),
            User(username='daan', email='daan@example.com',
                 password_hash=hash_password('password'),
                 created_at=datetime(2023, 6, 12)),
        ]

        for user in users:
            db.session.add(user)
        db.session.commit()

        print(f"  Created {len(users)} users")

        # ==================== BOOKS ====================
        # Realistisch aanbod van tweedehands boeken
        books_data = [
            # Fiction
            ("De Ontdekking van de Hemel", "Harry Mulisch", "978-0140285192", "fiction", 8.50, "good"),
            ("Het Diner", "Herman Koch", "978-9041413093", "fiction", 6.00, "fair"),
            ("The Great Gatsby", "F. Scott Fitzgerald", "978-0743273565", "fiction", 5.50, "good"),
            ("1984", "George Orwell", "978-0451524935", "fiction", 7.00, "new"),
            ("Norwegian Wood", "Haruki Murakami", "978-0375704024", "fiction", 9.00, "good"),
            ("The Midnight Library", "Matt Haig", "978-0525559474", "fiction", 11.50, "new"),
            ("Piranesi", "Susanna Clarke", "978-1635575941", "fiction", 10.00, "good"),
            ("Klara and the Sun", "Kazuo Ishiguro", "978-0571364879", "fiction", 12.00, "new"),
            ("De Avonden", "Gerard Reve", "978-9023478584", "fiction", 4.50, "poor"),
            ("Turks Fruit", "Jan Wolkers", "978-9029092333", "fiction", 5.00, "fair"),
            # Non-fiction
            ("Sapiens", "Yuval Noah Harari", "978-0062316097", "non-fiction", 12.00, "good"),
            ("Thinking, Fast and Slow", "Daniel Kahneman", "978-0374533557", "non-fiction", 10.50, "good"),
            ("Educated", "Tara Westover", "978-0399590504", "non-fiction", 9.50, "fair"),
            ("Atomic Habits", "James Clear", "978-0735211292", "non-fiction", 13.00, "new"),
            ("The Body", "Bill Bryson", "978-0385539302", "non-fiction", 11.00, "good"),
            # Textbooks
            ("Introduction to Algorithms", "Thomas Cormen", "978-0262033848", "textbook", 45.00, "good"),
            ("Clean Code", "Robert C. Martin", "978-0132350884", "textbook", 25.00, "fair"),
            ("Design Patterns", "Gang of Four", "978-0201633610", "textbook", 30.00, "good"),
            ("The Pragmatic Programmer", "David Thomas", "978-0135957059", "textbook", 28.00, "new"),
            ("Structure and Interpretation", "Abelson & Sussman", "978-0262510875", "textbook", 35.00, "fair"),
            ("Database Systems", "Ramez Elmasri", "978-0133970777", "textbook", 40.00, "poor"),
            ("Operating Systems", "Andrew Tanenbaum", "978-0133591620", "textbook", 38.00, "fair"),
            # Children
            ("Harry Potter and the Philosopher's Stone", "J.K. Rowling", "978-0747532699", "children", 6.00, "fair"),
            ("Matilda", "Roald Dahl", "978-0142410370", "children", 5.50, "good"),
            ("The BFG", "Roald Dahl", "978-0142410387", "children", 5.00, "good"),
            ("Jip en Jansen", "Annie M.G. Schmidt", "978-9045115580", "children", 7.50, "new"),
            ("Pluk van de Petteflet", "Annie M.G. Schmidt", "978-9045103051", "children", 8.00, "good"),
            # Comics
            ("Maus", "Art Spiegelman", "978-0394747231", "comics", 15.00, "good"),
            ("Persepolis", "Marjane Satrapi", "978-0375714832", "comics", 12.00, "fair"),
            ("Watchmen", "Alan Moore", "978-1401245252", "comics", 18.00, "good"),
            ("V for Vendetta", "Alan Moore", "978-1401208417", "comics", 14.00, "fair"),
            ("Asterix in Britain", "René Goscinny", "978-0752866185", "comics", 8.00, "good"),
            # Science
            ("A Brief History of Time", "Stephen Hawking", "978-0553380163", "science", 8.50, "good"),
            ("The Selfish Gene", "Richard Dawkins", "978-0198788607", "science", 9.00, "fair"),
            ("Cosmos", "Carl Sagan", "978-0345539434", "science", 10.00, "good"),
            ("The Double Helix", "James Watson", "978-0743216302", "science", 7.50, "poor"),
            ("Astrophysics for People in a Hurry", "Neil deGrasse Tyson", "978-0393609394", "science", 11.00, "new"),
            # History
            ("Guns, Germs, and Steel", "Jared Diamond", "978-0393354324", "history", 11.00, "good"),
            ("The Diary of Anne Frank", "Anne Frank", "978-0553296983", "history", 6.00, "fair"),
            ("A People's History", "Howard Zinn", "978-0062397348", "history", 12.00, "good"),
            ("Het Achterhuis", "Anne Frank", "978-9046706398", "history", 5.50, "fair"),
            # Cooking
            ("Salt, Fat, Acid, Heat", "Samin Nosrat", "978-1476753836", "cooking", 20.00, "new"),
            ("The Food Lab", "J. Kenji López-Alt", "978-0393081084", "cooking", 25.00, "good"),
            ("Ottolenghi Simple", "Yotam Ottolenghi", "978-1785031168", "cooking", 18.00, "good"),
            ("Plenty", "Yotam Ottolenghi", "978-1452101248", "cooking", 15.00, "fair"),
            # Travel
            ("In Patagonia", "Bruce Chatwin", "978-0142437193", "travel", 8.00, "fair"),
            ("The Alchemist", "Paulo Coelho", "978-0062315007", "travel", 7.50, "good"),
            ("Into the Wild", "Jon Krakauer", "978-0385486804", "travel", 9.00, "good"),
            # Other
            ("The Art of War", "Sun Tzu", "978-1599869773", "other", 5.00, "good"),
            ("Zen and the Art of Motorcycle Maintenance", "Robert Pirsig", "978-0060839871", "other", 8.00, "fair"),
            ("Meditations", "Marcus Aurelius", "978-0140449334", "other", 6.50, "good"),
        ]

        books = []
        for i, (title, author, isbn, category, price, condition) in enumerate(books_data):
            seller_id = random.choice([u.id for u in users if not u.is_admin])
            days_ago = random.randint(1, 365)
            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                category=category,
                price=price,
                condition=condition,
                seller_id=seller_id,
                status='available',
                description=f"A {condition} condition copy of {title} by {author}. "
                           f"Well-maintained and ready for a new reader.",
                created_at=datetime.now() - timedelta(days=days_ago),
                views_count=random.randint(0, 150),
                featured=(i < 6)  # Eerste 6 boeken zijn featured
            )
            books.append(book)
            db.session.add(book)

        db.session.commit()
        print(f"  Created {len(books)} books")

        # ==================== RESERVERINGEN ====================
        # Maak wat reserveringen aan
        reservation_data = [
            (books[0].id, users[4].id, 'confirmed'),
            (books[5].id, users[3].id, 'pending'),
            (books[10].id, users[6].id, 'pending'),
            (books[15].id, users[7].id, 'cancelled'),
            (books[20].id, users[2].id, 'confirmed'),
            (books[25].id, users[8].id, 'pending'),
            (books[30].id, users[5].id, 'expired'),
        ]

        for book_id, user_id, status in reservation_data:
            res = Reservation(
                book_id=book_id,
                user_id=user_id,
                status=status,
                created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                expires_at=datetime.now() + timedelta(hours=48) if status == 'pending' else None
            )
            db.session.add(res)

            # Update boek status
            book = db.session.get(Book, book_id)
            if status == 'pending':
                book.status = 'reserved'
            elif status == 'confirmed':
                book.status = 'sold'

        db.session.commit()
        print(f"  Created {len(reservation_data)} reservations")

        # ==================== REVIEWS ====================
        reviews_data = [
            (users[4].id, users[1].id, 5, "Great seller, book in perfect condition!"),
            (users[3].id, users[2].id, 4, "Good communication, fast shipping."),
            (users[6].id, users[1].id, 4, "Book was as described."),
            (users[7].id, users[3].id, 3, "Took a while to ship but book was fine."),
            (users[2].id, users[5].id, 5, "Excellent! Would buy again."),
            (users[8].id, users[4].id, 4, "Very good condition, recommended."),
        ]

        for reviewer_id, seller_id, rating, comment in reviews_data:
            review = Review(
                reviewer_id=reviewer_id,
                seller_id=seller_id,
                rating=rating,
                comment=comment,
                created_at=datetime.now() - timedelta(days=random.randint(1, 60))
            )
            db.session.add(review)

        db.session.commit()
        print(f"  Created {len(reviews_data)} reviews")

        # ==================== ACTIVITY LOG ====================
        activities = [
            (users[1].id, 'book_created', 'Created book: De Ontdekking van de Hemel'),
            (users[2].id, 'book_created', 'Created book: The Great Gatsby'),
            (users[4].id, 'book_reserved', 'Reserved: De Ontdekking van de Hemel'),
            (users[0].id, 'admin_action', 'Featured book: 1984'),
            (users[3].id, 'book_reserved', 'Reserved: The Midnight Library'),
        ]

        for user_id, action, details in activities:
            log = ActivityLog(
                user_id=user_id,
                action=action,
                details=details,
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            db.session.add(log)

        db.session.commit()
        print(f"  Created {len(activities)} activity logs")

        print("\nSeeding complete!")
        print("\nTest accounts:")
        print("  Admin: admin / admin123")
        print("  User:  jan / password")
        print("  User:  marie / password")
        print("  User:  sophie / password")


if __name__ == '__main__':
    seed_database()
