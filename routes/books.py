from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from extensions import db
from models import Book, User, DownloadLog, BorrowRequest, Favorite
from markupsafe import escape
from datetime import datetime, timezone
import os
from werkzeug.utils import secure_filename

books_bp = Blueprint('books', __name__)

def _redirect_back_or(endpoint, **values):
    return redirect(request.referrer or url_for(endpoint, **values))

@books_bp.route('/')
@login_required
def catalog():
    try:
        search = escape(request.args.get('search', ''))
        category = escape(request.args.get('category', 'All'))
        book_type = escape(request.args.get('type', 'All'))
        page = request.args.get('page', 1, type=int)
        per_page = 9

        query = Book.query.filter(Book.deleted_at.is_(None))

        if search:
            query = query.filter(Book.title.contains(search) | Book.author.contains(search))
        if category != 'All':
            query = query.filter_by(category=category)
        if book_type != 'All':
            query = query.filter_by(book_type=book_type.lower())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        books = pagination.items

        if request.headers.get('HX-Request'):
            return render_template('books/_book_cards.html', books=books, pagination=pagination)

        return render_template('books/catalog.html', books=books, pagination=pagination)
    except Exception as e:
        current_app.logger.exception(f'Error loading book catalog: {e}')
        flash('Unable to load the catalog at this time. Please try again later.', 'danger')
        return render_template('books/catalog.html', books=[], pagination=None)

@books_bp.route('/<int:book_id>')
@login_required
def detail(book_id):
    try:
        book = Book.query.filter(
            Book.id == book_id,
            Book.deleted_at.is_(None)
        ).first_or_404()
        
        active_request = BorrowRequest.query.filter_by(
            book_id=book_id,
            borrower_id=current_user.id
        ).filter(BorrowRequest.status.in_(['pending', 'accepted', 'borrowed'])).first()

        is_favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            book_id=book_id
        ).first() is not None
        
        return render_template(
            'books/detail.html',
            book=book,
            active_request=active_request,
            is_favorite=is_favorite
        )
    except Exception as e:
        current_app.logger.exception(f'Error loading book detail for ID {book_id}: {e}')
        flash('An error occurred while loading book details.', 'danger')
        return _redirect_back_or('books.catalog')

@books_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            author = request.form.get('author')
            category = request.form.get('category')
            book_type = request.form.get('book_type')
            description = request.form.get('description')
            location_notes = request.form.get('location_notes')
            
            if not title or not author or not category or not book_type:
                flash('Please provide the required fields', 'danger')
                return _redirect_back_or('books.add')
            
            new_book = Book()
            new_book.title = escape(title)
            new_book.author = escape(author)
            new_book.category = escape(category)
            new_book.book_type = escape(book_type)
            new_book.description = escape(description)
            new_book.owner_id = current_user.id
            
            cover_file = request.files.get('cover_image')
            if cover_file and cover_file.filename:
                cover_filename = secure_filename(cover_file.filename)
                cover_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'covers', str(current_user.id))
                os.makedirs(cover_dir, exist_ok=True)
                cover_path = os.path.join('covers', str(current_user.id), cover_filename)
                cover_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], cover_path))
                new_book.cover_image = cover_path
                
            if book_type == 'digital':
                file = request.files.get('file')
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if not filename.lower().endswith(('.pdf', '.epub', '.txt')):
                        flash('Invalid file type. Only PDF, EPUB, and TXT files are allowed.', 'danger')
                        return _redirect_back_or('books.add')
                    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'books', str(current_user.id))
                    os.makedirs(upload_dir, exist_ok=True)
                    file_path = os.path.join('books', str(current_user.id), filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_path))
                    new_book.file_path = file_path
                elif not new_book.file_path:
                    flash('Please upload a file for digital books.', 'danger')
                    return _redirect_back_or('books.add')                
                
            elif book_type == 'physical':
                condition = request.form.get('condition')
                if not condition or not condition.strip():
                    flash('Please select a condition for physical books.', 'danger')
                    return _redirect_back_or('books.add')
                
                new_book.condition = escape(condition)
                new_book.location_notes = escape(location_notes)
                
            else:
                flash('Invalid book type. Please select a valid type.', 'danger')
                return _redirect_back_or('books.add')            

            db.session.add(new_book)
            db.session.commit()
            
            flash('Book Added Successfully!', 'success')
            return _redirect_back_or('books.catalog')
        except Exception as e:
            db.session.rollback()

            try:
                if 'cover_path' in locals() and cover_path:
                    full_cover_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cover_path)
                    if os.path.exists(full_cover_path):
                        os.remove(full_cover_path)
                        
                if 'file_path' in locals() and file_path:
                    full_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
                    if os.path.exists(full_file_path):
                        os.remove(full_file_path)
            except Exception as e:
                current_app.logger.error(f'Error cleaning up files after failed book add: {e}')

            current_app.logger.exception(f'Error adding book: {e}')
            flash('An error occurred while adding the book.', 'danger')
            return _redirect_back_or('books.add')
        
    return render_template('books/add.html')

@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(book_id):
    try:
        book = Book.query.filter(
            Book.id == book_id,
            Book.deleted_at.is_(None)
        ).first_or_404()
        if book.owner_id != current_user.id and current_user.role != 'admin':
            abort(403)
            
        if request.method == 'POST':
            book.title = escape(request.form.get('title'))
            book.author = escape(request.form.get('author'))
            book.category = escape(request.form.get('category'))
            book.description = escape(request.form.get('description'))
            book.location_notes = escape(request.form.get('location_notes'))
            book.condition = escape(request.form.get('condition'))

            cover_file = request.files.get('cover_image')
            if cover_file and cover_file.filename:
                cover_filename = secure_filename(cover_file.filename)
                cover_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'covers', str(current_user.id))
                os.makedirs(cover_dir, exist_ok=True)
                cover_path = os.path.join('covers', str(current_user.id), cover_filename)
                cover_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], cover_path))
                book.cover_image = cover_path
            
            db.session.commit()
            flash('Book Updated Successfully!', 'success')
            return _redirect_back_or('books.detail', book_id=book.id)
            
        return render_template('books/edit.html', book=book)
    except Exception as e:
        db.session.rollback()
        
        try:
            if 'cover_path' in locals() and cover_path:
                full_cover_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cover_path)
                if os.path.exists(full_cover_path):
                    os.remove(full_cover_path)
        except Exception as e:
            current_app.logger.error(f'Error cleaning up cover image after failed book edit: {e}')

        current_app.logger.exception(f'Error editing book {book_id}: {e}')
        flash('An error occurred while updating the book.', 'danger')
        return _redirect_back_or('books.catalog')

@books_bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
def delete(book_id):
    fallback_endpoint = 'admin.books' if current_user.role == 'admin' else 'dashboard.my_books'
    try:
        book = Book.query.filter(
            Book.id == book_id,
            Book.deleted_at.is_(None)
        ).first_or_404()
        if book.owner_id != current_user.id and current_user.role != 'admin':
            abort(403)

        if book.deleted_at is not None:
            flash('Book is already deleted.', 'info')
            return _redirect_back_or(fallback_endpoint)

        book.deleted_at = datetime.now(timezone.utc)
        db.session.commit()
        flash('Book deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error deleting book {book_id}: {e}')
        flash('An error occurred while deleting the book.', 'danger')
        
    return _redirect_back_or(fallback_endpoint)

@books_bp.route('/<int:book_id>/download')
@login_required
def download(book_id):
    try:
        book = Book.query.filter(
            Book.id == book_id,
            Book.deleted_at.is_(None)
        ).first_or_404()

        if book.book_type != 'digital':
            flash('This book is not available for digital download.', 'danger')
            return _redirect_back_or('books.detail', book_id=book_id)

        borrow_req = BorrowRequest.query.filter_by(
            book_id=book_id, 
            borrower_id=current_user.id
        ).filter(BorrowRequest.status.in_(['accepted', 'borrowed'])).first()

        if not borrow_req and book.owner_id != current_user.id and current_user.role != 'admin':
            flash('You do not have permission to download this book.', 'danger')
            return _redirect_back_or('dashboard.borrowed')

        log = DownloadLog()
        log.book_id = book_id
        log.user_id = current_user.id
        db.session.add(log)
        db.session.commit()

        directory = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.dirname(book.file_path))
        filename = os.path.basename(book.file_path)

        return send_from_directory(directory, filename, as_attachment=True)

    except Exception as e:
        current_app.logger.exception(f'Error downloading book {book_id}: {e}')
        flash('An error occurred while trying to download the book.', 'danger')
        return _redirect_back_or('dashboard.borrowed')
