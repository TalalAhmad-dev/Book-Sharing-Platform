from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Book, User
import os
from werkzeug.utils import secure_filename

books_bp = Blueprint('books', __name__)

@books_bp.route('/')
@login_required
def catalog():
    q = request.args.get('q', '')
    category = request.args.get('category', 'All')
    book_type = request.args.get('type', 'All')
    
    query = Book.query
    
    if q:
        query = query.filter(Book.title.contains(q) | Book.author.contains(q) | Book.category.contains(q))
    if category != 'All':
        query = query.filter_by(category=category)
    if book_type != 'All':
        query = query.filter_by(book_type=book_type.lower())
        
    books = query.all()
    return render_template('books/catalog.html', books=books)

@books_bp.route('/<int:book_id>')
@login_required
def detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('books/detail.html', book=book)

@books_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        category = request.form.get('category')
        book_type = request.form.get('book_type')
        description = request.form.get('description')
        location_notes = request.form.get('location_notes')
        
        new_book = Book()
        new_book.title = title
        new_book.author = author
        new_book.category = category
        new_book.book_type = book_type
        new_book.description = description
        new_book.location_notes = location_notes
        new_book.owner_id = current_user.id
        
        if book_type == 'digital':
            file = request.files.get('file')
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Ensure directory exists
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'books', str(current_user.id))
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join('books', str(current_user.id), filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_path))
                new_book.file_path = file_path
        
        db.session.add(new_book)
        db.session.commit()
        
        flash('Book added successfully!', 'success')
        return redirect(url_for('books.catalog'))
        
    return render_template('books/add.html')

@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(book_id):
    book = Book.query.get_or_404(book_id)
    if book.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)
        
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.category = request.form.get('category')
        book.description = request.form.get('description')
        book.location_notes = request.form.get('location_notes')
        
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books.detail', book_id=book.id))
        
    return render_template('books/edit.html', book=book)

@books_bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
def delete(book_id):
    book = Book.query.get_or_404(book_id)
    if book.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)
        
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted.', 'success')
    return redirect(url_for('dashboard.my_books'))
