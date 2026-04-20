from app import create_app
from extensions import db
from models import User

app = create_app()

with app.app_context():
    if not User.query.filter(User.email.like('%@admin.com')).first():
        admin = User()
        admin.name='Talal Ahmad (Admin)'
        admin.email='talal.ahmad@admin.com'
        admin.role='admin'
        admin.set_password('admin123')
        
        db.session.add(admin)
        print("Admin user created.")

    db.session.commit()
    print("Seeding complete.")
