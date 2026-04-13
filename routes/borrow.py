from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Book, BorrowRequest, User
from datetime import datetime, timezone

borrow_bp = Blueprint('borrow', __name__)

@borrow_bp.route('/<int:book_id>/request', methods=['POST'])
@login_required
def request_borrow(book_id):
    book = Book.query.get_or_404(book_id)
    if book.owner_id == current_user.id:
        flash("You can't borrow your own book.", "error")
        return redirect(url_for('books.detail', book_id=book_id))
    
    if book.status != 'available':
        flash("Book is not available.", "error")
        return redirect(url_for('books.detail', book_id=book_id))

    # Digital auto-accept logic
    if book.book_type == 'digital':
        new_request = BorrowRequest()
        new_request.book_id = book.id
        new_request.borrower_id = current_user.id
        new_request.status = 'borrowed'
        new_request.borrowed_at = datetime.now(timezone.utc)
        
        db.session.add(new_request)
        db.session.commit()
        flash("Digital book borrowed successfully! You can now download it.", "success")
        return redirect(url_for('books.detail', book_id=book_id))

    # Physical book request
    proposed_date_str = request.form.get('proposed_date')
    proposed_time_str = request.form.get('proposed_time')
    location = request.form.get('location')
    message = request.form.get('message')

    proposed_date = datetime.strptime(proposed_date_str, '%Y-%m-%d').date() if proposed_date_str else None
    proposed_time = datetime.strptime(proposed_time_str, '%H:%M').time() if proposed_time_str else None

    new_request = BorrowRequest()
    new_request.book_id = book.id
    new_request.borrower_id = current_user.id
    new_request.status = 'pending'
    new_request.proposed_date = proposed_date
    new_request.proposed_time = proposed_time
    new_request.location = location
    new_request.message = message
    
    db.session.add(new_request)
    db.session.commit()
    flash("Borrow request sent to owner.", "success")
    return redirect(url_for('books.detail', book_id=book_id))

@borrow_bp.route('/<int:req_id>/accept', methods=['POST'])
@login_required
def accept(req_id):
    borrow_req = BorrowRequest.query.get_or_404(req_id)
    if borrow_req.book.owner_id != current_user.id:
        abort(403)
    
    borrow_req.status = 'accepted'
    db.session.commit()
    flash("Request accepted.", "success")
    return redirect(url_for('dashboard.my_books'))

@borrow_bp.route('/<int:req_id>/reject', methods=['POST'])
@login_required
def reject(req_id):
    borrow_req = BorrowRequest.query.get_or_404(req_id)
    if borrow_req.book.owner_id != current_user.id:
        abort(403)
    
    borrow_req.status = 'rejected'
    db.session.commit()
    flash("Request rejected.", "info")
    return redirect(url_for('dashboard.my_books'))

@borrow_bp.route('/<int:req_id>/mark-borrowed', methods=['POST'])
@login_required
def mark_borrowed(req_id):
    borrow_req = BorrowRequest.query.get_or_404(req_id)
    if borrow_req.book.owner_id != current_user.id:
        abort(403)
    
    borrow_req.status = 'borrowed'
    borrow_req.borrowed_at = datetime.now(timezone.utc)
    borrow_req.book.status = 'borrowed'
    db.session.commit()
    flash("Book marked as borrowed.", "success")
    return redirect(url_for('dashboard.my_books'))

@borrow_bp.route('/<int:req_id>/mark-returned', methods=['POST'])
@login_required
def mark_returned(req_id):
    borrow_req = BorrowRequest.query.get_or_404(req_id)
    if borrow_req.book.owner_id != current_user.id and borrow_req.borrower_id != current_user.id:
        abort(403)
    
    borrow_req.status = 'returned'
    borrow_req.returned_at = datetime.now(timezone.utc)
    borrow_req.book.status = 'available'
    db.session.commit()
    flash("Book marked as returned. Available again.", "success")
    return redirect(url_for('dashboard.my_books'))
