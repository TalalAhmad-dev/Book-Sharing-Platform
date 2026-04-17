from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Book, BorrowRequest, Favorite

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    try:
        my_books_count = Book.query.filter_by(owner_id=current_user.id).count()
        borrowed_count = BorrowRequest.query.filter_by(borrower_id=current_user.id, status='borrowed').count()
        pending_requests_count = BorrowRequest.query.join(Book).filter(Book.owner_id == current_user.id, BorrowRequest.status == 'pending').count()
        favorites_count = Favorite.query.filter_by(user_id=current_user.id).count()
        
        return render_template('dashboard/index.html', 
                               my_books_count=my_books_count,
                               borrowed_count=borrowed_count,
                               pending_requests_count=pending_requests_count,
                               favorites_count=favorites_count)
    except Exception as e:
        current_app.logger.exception(f"Error loading dashboard index: {e}")
        flash("An error occurred while loading your dashboard.", "danger")
        return render_template('dashboard/index.html', 
                               my_books_count=0,
                               borrowed_count=0,
                               pending_requests_count=0,
                               favorites_count=0)

@dashboard_bp.route('/my-books')
@login_required
def my_books():
    try:
        my_books = Book.query.filter_by(owner_id=current_user.id).all()
        incoming_requests = BorrowRequest.query.join(Book).filter(Book.owner_id == current_user.id).all()
        return render_template('dashboard/my_books.html', my_books=my_books, incoming_requests=incoming_requests)
    except Exception as e:
        current_app.logger.exception(f"Error loading my books dashboard: {e}")
        flash("An error occurred while loading your books.", "danger")
        return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/borrowed')
@login_required
def borrowed():
    try:
        my_borrows = BorrowRequest.query.filter_by(borrower_id=current_user.id).all()
        return render_template('dashboard/borrowed.html', my_borrows=my_borrows)
    except Exception as e:
        current_app.logger.exception(f"Error loading borrowed books dashboard: {e}")
        flash("An error occurred while loading your borrowed books.", "danger")
        return redirect(url_for('dashboard.index'))
