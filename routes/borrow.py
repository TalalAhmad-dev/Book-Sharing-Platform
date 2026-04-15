from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Book, BorrowRequest, User
from datetime import datetime, timezone
from routes.books import books_bp

borrow_bp = Blueprint('borrow', __name__)

@books_bp.route('/<int:book_id>/borrow', methods=['GET', 'POST'])
@login_required
def request_borrow(book_id):
    book = Book.query.get_or_404(book_id)
    if book.owner_id == current_user.id:
        flash("You can't borrow your own book.", "error")
        return redirect(url_for('books.detail', book_id=book_id))
    
    if book.status != 'available':
        flash("Book is not available.", "error")
        return redirect(url_for('books.detail', book_id=book_id))

    if request.method == 'POST':
        if book.book_type == 'digital':
            new_request = BorrowRequest()
            new_request.book_id = book.id
            new_request.borrower_id = current_user.id
            new_request.status = 'pending'
            
            db.session.add(new_request)
            db.session.commit()
            flash("Digital book borrowed successfully! You can now download it after the owner confirms your request.", "success")
            return redirect(url_for('dashboard.borrowed'))

        proposed_date_str = request.form.get('proposed_date')
        proposed_time_str = request.form.get('proposed_time')
        location = request.form.get('location')
        message = request.form.get('message')

        if not proposed_date_str or not proposed_time_str or not location:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('borrow.request_borrow', book_id=book_id))

        try:
            proposed_date = datetime.strptime(proposed_date_str, '%Y-%m-%d').date()
            proposed_time = datetime.strptime(proposed_time_str, '%H:%M').time()
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('borrow.request_borrow', book_id=book_id))

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
        return redirect(url_for('dashboard.borrowed'))

    return render_template('borrow/request.html', book=book)

@borrow_bp.route('/<int:req_id>/accept', methods=['POST'])
@login_required
def accept(req_id):
    borrow_req = BorrowRequest.query.get_or_404(req_id)
    if borrow_req.book.owner_id != current_user.id:
        abort(403)
    
    borrow_req.status = 'accepted'
    db.session.commit()
    flash("Request accepted.", "success")
    
    if borrow_req.book.book_type == 'digital':
        mark_borrowed(req_id)
        flash("Digital book borrowed successfully! The borrower can now download it.", "success")
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
    if borrow_req.book.book_type == 'physical':
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
    
    if borrow_req.book.book_type == 'digital' and borrow_req.book.owner_id == current_user.id:
        flash("Digital book borrowings can only be marked as returned by the borrower or will be marked as returned automatically after 7 days.", "danger") 
        return redirect(url_for('dashboard.my_books'))       
    
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
