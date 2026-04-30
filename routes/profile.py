from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import User, Book
from extensions import db
import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)


def _format_account_age(joined_at):
    if not joined_at:
        return "N/A"

    joined_utc = joined_at if joined_at.tzinfo else joined_at.replace(tzinfo=timezone.utc)
    now_utc = datetime.now(timezone.utc)

    months = (now_utc.year - joined_utc.year) * 12 + (now_utc.month - joined_utc.month)
    if now_utc.day < joined_utc.day:
        months -= 1
    months = max(months, 0)

    years, remaining_months = divmod(months, 12)
    if years and remaining_months:
        return f"{years}y {remaining_months}m"
    if years:
        return f"{years} year{'s' if years != 1 else ''}"
    if remaining_months:
        return f"{remaining_months} month{'s' if remaining_months != 1 else ''}"
    return "Less than a month"


@profile_bp.route('/<int:user_id>')
@login_required
def view(user_id):
    user = User.query.get_or_404(user_id)
    books_query = Book.query.filter(
        Book.owner_id == user.id,
        Book.deleted_at.is_(None)
    ).order_by(Book.updated_at.desc(), Book.created_at.desc())
    total_books_count = books_query.count()
    user_books = books_query.limit(5).all()

    profile_stats = {
        'member_since': user.created_at if user.created_at else None,
        'account_age': _format_account_age(user.created_at),
        'account_status': (user.status or 'unknown').capitalize(),
        'last_updated_at': user.updated_at or user.created_at
    }

    return render_template(
        'profile/view.html',
        user=user,
        books=user_books,
        profile_stats=profile_stats,
        total_books_count=total_books_count,
        has_more_books=total_books_count > len(user_books)
    )

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.bio = request.form.get('bio')
        current_user.contact = request.form.get('contact')
        
        file = request.files.get('profile_image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join('profiles', f"user_{current_user.id}_{filename}")
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_path))
            current_user.profile_image = file_path
            
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('profile.view', user_id=current_user.id))
        
    return render_template('profile/edit.html')
