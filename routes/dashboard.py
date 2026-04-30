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

@dashboard_bp.route('/incoming-requests')
@login_required
def incoming_requests():
    try:
        incoming_requests = (
            BorrowRequest.query.options(
                joinedload(BorrowRequest.book).joinedload(Book.owner),
                joinedload(BorrowRequest.borrower)
            )
            .join(Book)
            .filter(
                Book.owner_id == current_user.id,
                Book.deleted_at.is_(None)
            )
            .order_by(BorrowRequest.created_at.desc())
            .all()
        )

        incoming_messages = {}
        incoming_summary = {
            'total': len(incoming_requests),
            'pending': 0,
            'actionable': 0,
            'borrowed': 0,
            'returned': 0
        }

        for borrow_request in incoming_requests:
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
            incoming_messages[borrow_request.id] = message_data

            if borrow_request.status == 'pending':
                incoming_summary['pending'] += 1
            if borrow_request.status in ('pending', 'suggested', 'accepted'):
                incoming_summary['actionable'] += 1
            if borrow_request.status == 'borrowed':
                incoming_summary['borrowed'] += 1
            if borrow_request.status == 'returned':
                incoming_summary['returned'] += 1

        return render_template(
            'dashboard/incoming_requests.html',
            incoming_requests=incoming_requests,
            incoming_messages=incoming_messages,
            incoming_summary=incoming_summary
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading incoming requests dashboard: {e}")
        flash("An error occurred while loading incoming requests.", "danger")
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
