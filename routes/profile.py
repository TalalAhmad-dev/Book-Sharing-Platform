from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import User, Book
from extensions import db
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/<int:user_id>')
@login_required
def view(user_id):
    user = User.query.get_or_404(user_id)
    user_books = Book.query.filter(
        Book.owner_id == user.id,
        Book.deleted_at.is_(None)
    ).all()
    return render_template('profile/view.html', user=user, books=user_books)

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
