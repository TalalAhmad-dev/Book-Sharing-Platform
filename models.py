from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

#TODO(Done): Add updated_at to User model and update it on profile updates
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='member') # member | admin
    status = db.Column(db.String(20), default='active') # active | blocked
    bio = db.Column(db.Text)
    contact = db.Column(db.String(50))
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc), default=lambda: datetime.now(timezone.utc))

    # Relationships
    books = db.relationship('Book', backref='owner', lazy=True)
    borrow_requests = db.relationship('BorrowRequest', backref='borrower', foreign_keys='BorrowRequest.borrower_id', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    reports_submitted = db.relationship('Report', backref='reporter', foreign_keys='Report.reporter_id', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    book_type = db.Column(db.String(20), nullable=False) # physical | digital
    condition = db.Column(db.String(20)) # new | good | poor
    status = db.Column(db.String(20), default='available') # available | borrowed | returned
    location_notes = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    cover_image = db.Column(db.String(255))
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc), default=lambda: datetime.now(timezone.utc))

    # Relationships
    borrow_requests = db.relationship('BorrowRequest', backref='book', lazy=True)
    favorited_by = db.relationship('Favorite', backref='book', lazy=True)
    reports = db.relationship('Report', backref='reported_book', foreign_keys='Report.reported_book_id', lazy=True)

class BorrowRequest(db.Model):
    __tablename__ = 'borrow_requests'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending | accepted | rejected | suggested | borrowed | returned
    proposed_date = db.Column(db.Date)
    proposed_time = db.Column(db.Time)
    location = db.Column(db.String(255))
    message = db.Column(db.Text)
    borrowed_at = db.Column(db.DateTime)
    returned_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc), default=lambda: datetime.now(timezone.utc))

class Favorite(db.Model):
    __tablename__ = 'favorites'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_user_book_favorite'),)

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open') # open | reviewed | dismissed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship for users reported
    reported_user = db.relationship('User', foreign_keys=[reported_user_id], backref='reports_received')

class DownloadLog(db.Model):
    __tablename__ = 'download_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    downloaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
