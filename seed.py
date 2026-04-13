from app import create_app
from extensions import db
from models import User, Book

app = create_app()

with app.app_context():
    # Create admin
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(name='Admin User', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print("Admin user created.")

    # Create dummy member
    if not User.query.filter_by(email='member@example.com').first():
        member = User(name='Regular Member', email='member@example.com', role='member')
        member.set_password('member123')
        db.session.add(member)
        db.session.flush() # Get member ID
        
        # Add a book for member
        book = Book(
            title='The Flask Mega-Tutorial',
            author='Miguel Grinberg',
            category='Programming',
            book_type='physical',
            location_notes='Library Hall A',
            owner_id=member.id
        )
        db.session.add(book)
        print("Member user and dummy book created.")

    db.session.commit()
    print("Seeding complete.")
