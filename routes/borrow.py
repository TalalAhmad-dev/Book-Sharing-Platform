import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Book, BorrowRequest, User
from datetime import datetime, timezone
from routes.books import books_bp

borrow_bp = Blueprint('borrow', __name__)

# TODO: When request borrow or suggest alternative, make sure that the meeting time is in the future and not in the past.
@books_bp.route('/<int:book_id>/borrow', methods=['GET', 'POST'])
@login_required
def request_borrow(book_id):
    try:
        book = Book.query.get_or_404(book_id)
        
        active_request = BorrowRequest.query.filter_by(
            book_id=book_id,
            borrower_id=current_user.id
        ).filter(BorrowRequest.status.in_(['pending', 'accepted', 'borrowed', 'suggested'])).first()
        
        if active_request:
            flash("You already have an active request for this book.", "warning")
            return redirect(url_for('dashboard.borrowed'))

        if book.owner_id == current_user.id:
            flash("You can't borrow your own book.", "error")
            return redirect(url_for('books.detail', book_id=book_id))
        
        if book.book_type == 'physical' and book.status != 'available':
            flash("This book is currently borrowed by someone else.", "error")
            return redirect(url_for('books.detail', book_id=book_id))

        if request.method == 'POST':
            if book.book_type == 'digital':
                new_request = BorrowRequest()
                new_request.book_id = book.id
                new_request.borrower_id = current_user.id
                new_request.status = 'pending'
                
                db.session.add(new_request)
                db.session.commit()
                flash("Borrow request sent to owner. Once accepted, you can download the book.", "success")
                return redirect(url_for('dashboard.borrowed'))

            proposed_date_str = request.form.get('proposed_date')
            proposed_time_str = request.form.get('proposed_time')
            location = request.form.get('location')
            message = request.form.get('message')

            if not proposed_date_str or not proposed_time_str or not location:
                flash("Please fill in all required fields.", "danger")
                return redirect(url_for('borrow.request_borrow', book_id=book_id))

            if proposed_time_str and len(proposed_time_str.split(':')) == 3:
                proposed_time_str = ':'.join(proposed_time_str.split(':')[:2])

            try:
                proposed_date = datetime.strptime(proposed_date_str, '%Y-%m-%d').date()
                proposed_time = datetime.strptime(proposed_time_str, '%H:%M').time()
                
                proposed_datetime = datetime.combine(proposed_date, proposed_time)
                if proposed_datetime < datetime.now():
                    flash("Meeting time must be in the future.", "danger")
                    return redirect(url_for('borrow.request_borrow', book_id=book_id))
            except ValueError:
                flash(f"Invalid date or time format.", "danger")
                return redirect(url_for('borrow.request_borrow', book_id=book_id))

            new_request = BorrowRequest()
            new_request.book_id = book.id
            new_request.borrower_id = current_user.id
            new_request.status = 'pending'
            new_request.proposed_date = proposed_date
            new_request.proposed_time = proposed_time
            new_request.location = location
            
            msg_data = {"borrower": message, "owner": ""}
            new_request.message = json.dumps(msg_data)
            
            db.session.add(new_request)
            db.session.commit()
            flash("Borrow request sent to owner.", "success")
            return redirect(url_for('dashboard.borrowed'))

        return render_template('borrow/request.html', book=book)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error in request_borrow for book {book_id}: {e}")
        flash("An error occurred while processing your borrow request.", "danger")
        return redirect(url_for('books.detail', book_id=book_id))

@borrow_bp.route('/<int:req_id>/accept', methods=['POST'])
@login_required
def accept(req_id):
    try:
        borrow_req = BorrowRequest.query.get_or_404(req_id)
        is_owner = borrow_req.book.owner_id == current_user.id
        is_borrower = borrow_req.borrower_id == current_user.id

        if is_owner:
            if borrow_req.status not in ('pending', 'suggested'):
                flash("Invalid request status for acceptance.", "danger")
                return redirect(url_for('dashboard.my_books'))
        elif is_borrower:
            if borrow_req.status != 'suggested':
                flash("You can't accept your own borrow request.", "danger")
                return redirect(url_for('dashboard.borrowed'))
        else:
            abort(403)
        
        if borrow_req.book.book_type == 'physical':
            active_borrow = BorrowRequest.query.filter_by(book_id=borrow_req.book_id, status='borrowed').first()
            if active_borrow:
                flash("This book is currently borrowed. You cannot accept another request until it is returned.", "danger")
                return redirect(url_for('dashboard.my_books'))
                
            accepted_req = BorrowRequest.query.filter_by(book_id=borrow_req.book_id, status='accepted').first()
            if accepted_req and accepted_req.id != borrow_req.id:
                flash("You have already accepted another request for this book. Complete or cancel that one first.", "warning")
                return redirect(url_for('dashboard.my_books'))

        borrow_req.status = 'accepted'
        
        if borrow_req.book.book_type == 'digital':
            borrow_req.status = 'borrowed'
            borrow_req.borrowed_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash("Request accepted.", "success")
        return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error accepting request {req_id}: {e}")
        flash("An error occurred while accepting the request.", "danger")
        return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))

@borrow_bp.route('/<int:req_id>/suggest', methods=['POST'])
@login_required
def suggest(req_id):
    try:
        borrow_req = BorrowRequest.query.get_or_404(req_id)
        is_owner = borrow_req.book.owner_id == current_user.id
        is_borrower = borrow_req.borrower_id == current_user.id

        if not (is_owner or is_borrower):
            abort(403)
        
        if borrow_req.book.book_type != 'physical':
            flash("Suggestions are only available for physical books.", "warning")
            return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))
        
        if borrow_req.status not in ('pending', 'suggested'):
            if not is_owner and borrow_req.status == 'pending':
                flash("You can't suggest changes to a pending request. Please wait for the owner to respond first.", "warning")
                
            flash("Only pending or suggested requests can be updated with suggestions.", "danger")
            return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))

        proposed_date_str = request.form.get('proposed_date')
        proposed_time_str = request.form.get('proposed_time')
        location = request.form.get('location')
        message = request.form.get('message')

        if not proposed_date_str or not proposed_time_str or not location:
            flash("Date, time, and location are required for suggestions.", "danger")
            return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))
        
        if proposed_time_str and len(proposed_time_str.split(':')) == 3:
            proposed_time_str = ':'.join(proposed_time_str.split(':')[:2])

        try:
            proposed_date = datetime.strptime(proposed_date_str, '%Y-%m-%d').date()
            proposed_time = datetime.strptime(proposed_time_str, '%H:%M').time()
            
            proposed_datetime = datetime.combine(proposed_date, proposed_time)
            if proposed_datetime < datetime.now():
                flash("Meeting time must be in the future.", "danger")
                return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))

        try:
            msg_data = json.loads(borrow_req.message) if borrow_req.message else {"borrower": "", "owner": ""}
        except json.JSONDecodeError:
            msg_data = {"borrower": borrow_req.message, "owner": ""}

        if is_owner:
            msg_data["owner"] = message
        else:
            msg_data["borrower"] = message
            
        borrow_req.message = json.dumps(msg_data)
        borrow_req.proposed_date = proposed_date
        borrow_req.proposed_time = proposed_time
        borrow_req.location = location
        borrow_req.status = 'suggested'
        
        db.session.commit()
        flash("Suggestion sent successfully.", "success")
        return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error suggesting alternative for request {req_id}: {e}")
        flash("An error occurred while sending the suggestion.", "danger")
        return redirect(url_for('dashboard.my_books' if is_owner else 'dashboard.borrowed'))

@borrow_bp.route('/<int:req_id>/reject', methods=['POST'])
@login_required
def reject(req_id):
    try:
        borrow_req = BorrowRequest.query.get_or_404(req_id)
        if borrow_req.book.owner_id != current_user.id:
            abort(403)
        
        is_borrower = borrow_req.borrower_id == current_user.id
        is_owner = borrow_req.book.owner_id == current_user.id    
        
        if not (is_owner or is_borrower):
            flash("You don't have permission to reject this request.", "danger")
            abort(403)
            
        if not borrow_req.status == 'pending':
            flash("Only pending requests can be rejected.", "danger")
            return redirect(url_for('dashboard.my_books'))

        borrow_req.status = 'rejected'
        db.session.commit()
        flash("Request rejected.", "info")
        return redirect(url_for('dashboard.my_books'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error rejecting request {req_id}: {e}")
        flash("An error occurred while rejecting the request.", "danger")
        return redirect(url_for('dashboard.my_books'))

@borrow_bp.route('/<int:req_id>/mark-borrowed', methods=['POST'])
@login_required
def mark_borrowed(req_id):
    try:
        borrow_req = BorrowRequest.query.get_or_404(req_id)
        if borrow_req.book.owner_id != current_user.id:
            flash("Only the owner can mark the book as borrowed.", "danger")
            abort(403)
        
        if borrow_req.book.book_type == 'physical':
            if borrow_req.book.status != 'available':
                flash("This book is not available to be marked as borrowed.", "danger")
                return redirect(url_for('dashboard.my_books'))
            borrow_req.book.status = 'borrowed'
        
        borrow_req.status = 'borrowed'
        borrow_req.borrowed_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Book marked as borrowed.", "success")
        return redirect(url_for('dashboard.my_books'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error marking request {req_id} as borrowed: {e}")
        flash("An error occurred while updating the borrow status.", "danger")
        return redirect(url_for('dashboard.my_books'))

@borrow_bp.route('/<int:req_id>/mark-returned', methods=['POST'])
@login_required
def mark_returned(req_id):
    try:
        borrow_req = BorrowRequest.query.get_or_404(req_id)
        if borrow_req.book.owner_id != current_user.id and borrow_req.borrower_id != current_user.id:
            abort(403)
        
        if borrow_req.book.book_type == 'digital' and borrow_req.book.owner_id == current_user.id:
            flash("Digital book borrowings can only be marked as returned by the borrower or will be marked as returned automatically after 7 days.", "danger") 
            return redirect(url_for('dashboard.my_books'))
        
        if borrow_req.book.book_type == 'physical' and borrow_req.book.owner_id != current_user.id:
            flash("Only the owner can mark a physical book as returned.", "danger")
            return redirect(url_for('dashboard.borrowed'))
        
        if borrow_req.status in ('borrowed'):
            borrow_req.status = 'returned'
            borrow_req.returned_at = datetime.now(timezone.utc)
            if borrow_req.book.book_type == 'physical':
                borrow_req.book.status = 'available'
            db.session.commit()
            flash("Book marked as returned. Available again.", "success")
            return redirect(url_for('books.catalog'))
        else:
            flash("Invalid action. Only borrowed requests can be returned.", "danger")
            return redirect(url_for('dashboard.borrowed'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error marking request {req_id} as returned: {e}")
        flash("An error occurred while marking the book as returned.", "danger")
        return redirect(url_for('dashboard.borrowed'))
