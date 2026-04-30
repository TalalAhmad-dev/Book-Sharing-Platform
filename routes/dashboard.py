from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
import json
from models import Book, BorrowRequest, Favorite

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    try:
        my_books_count = Book.query.filter(
            Book.owner_id == current_user.id,
            Book.deleted_at.is_(None)
        ).count()
        borrowed_count = BorrowRequest.query.filter_by(borrower_id=current_user.id, status='borrowed').count()
        pending_requests_count = BorrowRequest.query.join(Book).filter(
            Book.owner_id == current_user.id,
            Book.deleted_at.is_(None),
            BorrowRequest.status == 'pending'
        ).count()
        favorites_count = Favorite.query.join(Book).filter(
            Favorite.user_id == current_user.id,
            Book.deleted_at.is_(None)
        ).count()
        
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
        my_books = Book.query.filter(
            Book.owner_id == current_user.id,
            Book.deleted_at.is_(None)
        ).all()
        incoming_requests = BorrowRequest.query.join(Book).filter(
            Book.owner_id == current_user.id,
            Book.deleted_at.is_(None)
        ).all()
        return render_template('dashboard/my_books.html', my_books=my_books, incoming_requests=incoming_requests)
    except Exception as e:
        current_app.logger.exception(f"Error loading my books dashboard: {e}")
        flash("An error occurred while loading your books.", "danger")
        return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/borrowed')
@login_required
def borrowed():
    try:
        my_borrows = (
            BorrowRequest.query.options(
                joinedload(BorrowRequest.book).joinedload(Book.owner),
                joinedload(BorrowRequest.borrower)
            )
            .filter(BorrowRequest.borrower_id == current_user.id)
            .order_by(BorrowRequest.created_at.desc())
            .all()
        )

        borrow_messages = {}
        borrow_summary = {
            'total': len(my_borrows),
            'active': 0,
            'returned': 0,
            'digital': 0,
            'physical': 0
        }

        for borrow_request in my_borrows:
            message_data = {'borrower': '', 'owner': ''}
            if borrow_request.message:
                try:
                    parsed = json.loads(borrow_request.message)
                    if isinstance(parsed, dict):
                        message_data['borrower'] = parsed.get('borrower', '') or ''
                        message_data['owner'] = parsed.get('owner', '') or ''
                    else:
                        message_data['borrower'] = str(parsed)
                except (ValueError, TypeError):
                    message_data['borrower'] = str(borrow_request.message)
            borrow_messages[borrow_request.id] = message_data

            if borrow_request.status in ('pending', 'accepted', 'suggested', 'borrowed'):
                borrow_summary['active'] += 1
            if borrow_request.status == 'returned':
                borrow_summary['returned'] += 1

            if borrow_request.book.book_type == 'digital':
                borrow_summary['digital'] += 1
            else:
                borrow_summary['physical'] += 1

        return render_template(
            'dashboard/borrowed.html',
            my_borrows=my_borrows,
            borrow_messages=borrow_messages,
            borrow_summary=borrow_summary
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading borrowed books dashboard: {e}")
        flash("An error occurred while loading your borrowed books.", "danger")
        return redirect(url_for('dashboard.index'))
