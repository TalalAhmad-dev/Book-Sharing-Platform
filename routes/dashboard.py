from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Book, BorrowRequest, Favorite

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    my_books_count = Book.query.filter_by(owner_id=current_user.id).count()
    borrowed_count = BorrowRequest.query.filter_by(borrower_id=current_user.id, status='borrowed').count()
    pending_requests_count = BorrowRequest.query.join(Book).filter(Book.owner_id == current_user.id, BorrowRequest.status == 'pending').count()
    favorites_count = Favorite.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard/index.html', 
                           my_books_count=my_books_count,
                           borrowed_count=borrowed_count,
                           pending_requests_count=pending_requests_count,
                           favorites_count=favorites_count)

@dashboard_bp.route('/my-books')
@login_required
def my_books():
    my_books = Book.query.filter_by(owner_id=current_user.id).all()
    incoming_requests = BorrowRequest.query.join(Book).filter(Book.owner_id == current_user.id).all()
    return render_template('dashboard/my_books.html', my_books=my_books, incoming_requests=incoming_requests)

@dashboard_bp.route('/borrowed')
@login_required
def borrowed():
    my_borrows = BorrowRequest.query.filter_by(borrower_id=current_user.id).all()
    return render_template('dashboard/borrowed.html', my_borrows=my_borrows)
