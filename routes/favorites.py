from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from extensions import db
from models import Book, Favorite

favorites_bp = Blueprint('favorites', __name__)


@favorites_bp.route('/')
@login_required
def index():
    try:
        favorite_books = (
            Book.query
            .join(Favorite, Favorite.book_id == Book.id)
            .filter(
                Favorite.user_id == current_user.id,
                Book.deleted_at.is_(None)
            )
            .order_by(Favorite.created_at.desc())
            .all()
        )
        return render_template('favorites/wishlist.html', books=favorite_books)
    except Exception as e:
        current_app.logger.exception(f'Error loading favorites: {e}')
        flash('Unable to load favorites right now.', 'danger')
        return render_template('favorites/wishlist.html', books=[])


@favorites_bp.route('/<int:book_id>/add', methods=['POST'])
@login_required
def add(book_id):
    try:
        book = Book.query.get_or_404(book_id)
        if book.deleted_at is not None:
            flash('This book is no longer available.', 'warning')
            return redirect(request.referrer or url_for('books.catalog'))

        exists = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
        if exists:
            flash('Book is already in your favorites.', 'info')
            return redirect(request.referrer or url_for('books.detail', book_id=book_id))

        favorite = Favorite()
        favorite.user_id = current_user.id
        favorite.book_id = book_id

        db.session.add(favorite)
        db.session.commit()
        flash('Book added to favorites.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error adding favorite for book {book_id}: {e}')
        flash('Unable to add this book to favorites.', 'danger')

    return redirect(request.referrer or url_for('books.detail', book_id=book_id))


@favorites_bp.route('/<int:book_id>/remove', methods=['POST'])
@login_required
def remove(book_id):
    try:
        favorite = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
        if not favorite:
            flash('Book is not in your favorites.', 'info')
            return redirect(request.referrer or url_for('favorites.index'))

        db.session.delete(favorite)
        db.session.commit()
        flash('Book removed from favorites.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error removing favorite for book {book_id}: {e}')
        flash('Unable to remove this favorite.', 'danger')

    return redirect(request.referrer or url_for('favorites.index'))
