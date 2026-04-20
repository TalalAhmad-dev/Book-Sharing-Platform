from email.utils import parseaddr
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('books.catalog'))
    
    if request.method == 'POST':
        try:
            name = (request.form.get('name') or '').strip()
            email = (request.form.get('email') or '').strip().lower()
            password = request.form.get('password') or ''
            confirm_password = request.form.get('confirm_password') or ''

            if not name or not email or not password or not confirm_password:
                flash('All fields are required.', 'error')
                return render_template('auth/register.html')

            if len(name) > 100:
                flash('Name cannot exceed 100 characters.', 'error')
                return render_template('auth/register.html')

            if len(email) > 120:
                flash('Email cannot exceed 120 characters.', 'error')
                return render_template('auth/register.html')

            parsed_email = parseaddr(email)[1]
            if not parsed_email or '@' not in parsed_email:
                flash('Please enter a valid email address.', 'error')
                return render_template('auth/register.html')

            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'error')
                return render_template('auth/register.html')

            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('auth/register.html')

            user_exists = User.query.filter_by(email=email).first()
            if user_exists:
                flash('Email already registered.', 'error')
                return render_template('auth/register.html')

            new_user = User()
            new_user.name = name
            new_user.email = email
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f'Error during registration: {e}')
            flash('Unable to complete registration right now. Please try again.', 'error')
            return render_template('auth/register.html')
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books.catalog'))
        
    if request.method == 'POST':
        try:
            email = (request.form.get('email') or '').strip().lower()
            password = request.form.get('password') or ''
            remember = True if request.form.get('remember') else False

            if not email or not password:
                flash('Email and password are required.', 'error')
                return render_template('auth/login.html')

            if len(email) > 120:
                flash('Invalid email or password.', 'error')
                return render_template('auth/login.html')

            user = User.query.filter_by(email=email).first()

            if not user or not user.check_password(password):
                flash('Invalid email or password.', 'error')
                return render_template('auth/login.html')

            if user.status == 'blocked':
                flash('Your account is blocked.', 'error')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            current_app.logger.exception(f'Error during login: {e}')
            flash('Unable to log in right now. Please try again.', 'error')
            return render_template('auth/login.html')
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        return redirect(url_for('auth.login'))
    except Exception as e:
        current_app.logger.exception(f'Error during logout: {e}')
        flash('Unable to log out right now. Please try again.', 'error')
        return redirect(url_for('dashboard.index'))
