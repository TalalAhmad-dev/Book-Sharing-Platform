from flask import Blueprint, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from notification_service import queue_notification
from extensions import db
from models import Book, Report, User

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/book/<int:book_id>', methods=['POST'])
@login_required
def report_book(book_id):
    try:
        book = Book.query.get_or_404(book_id)
        reason = (request.form.get('reason') or '').strip()

        if book.deleted_at is not None:
            flash('This book is no longer available for reporting.', 'warning')
            return redirect(request.referrer or url_for('books.catalog'))

        if current_user.role == 'admin':
            flash('Admins cannot submit reports.', 'warning')
            return redirect(request.referrer or url_for('books.detail', book_id=book_id))

        if not reason:
            flash('Please provide a reason to submit the report.', 'danger')
            return redirect(request.referrer or url_for('books.detail', book_id=book_id))

        if book.owner_id == current_user.id:
            flash('You cannot report your own book.', 'warning')
            return redirect(request.referrer or url_for('books.detail', book_id=book_id))

        existing_open_report = Report.query.filter_by(
            reporter_id=current_user.id,
            reported_book_id=book_id,
            status='open'
        ).first()
        if existing_open_report:
            flash('You already have an open report for this book.', 'info')
            return redirect(request.referrer or url_for('books.detail', book_id=book_id))

        report = Report()
        report.reporter_id = current_user.id
        report.reported_book_id = book_id
        report.reason = reason
        
        admin_user = User.query.filter_by(role='admin').first()
        if admin_user:
            notification = queue_notification(
                recipient_id=admin_user,
                title='New Book Report',
                message=f'User {current_user.username} has reported book "{book.title}" for: {reason}',
                category='book report',
                actor_id=current_user.id,
                entity_type='book_report',
                entity_id=report.id
            )

        db.session.add(report)
        if notification:
            db.session.add(notification)
        db.session.commit()
        flash('Book report submitted.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error creating report for book {book_id}: {e}')
        flash('Unable to submit this report right now.', 'danger')

    return redirect(request.referrer or url_for('books.detail', book_id=book_id))


@reports_bp.route('/user/<int:user_id>', methods=['POST'])
@login_required
def report_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        reason = (request.form.get('reason') or '').strip()

        if current_user.role == 'admin':
            flash('Admins cannot submit reports.', 'warning')
            return redirect(request.referrer or url_for('profile.view', user_id=user_id))
        
        if user.role == 'admin' and current_user.role != 'admin':
            flash("You don't have permission to report an admin user.", 'warning')
            return redirect(request.referrer or url_for('profile.view', user_id=user_id))

        if not reason:
            flash('Please provide a reason to submit the report.', 'danger')
            return redirect(request.referrer or url_for('profile.view', user_id=user_id))

        if user.id == current_user.id:
            flash('You cannot report yourself.', 'warning')
            return redirect(request.referrer or url_for('profile.view', user_id=user_id))

        existing_open_report = Report.query.filter_by(
            reporter_id=current_user.id,
            reported_user_id=user_id,
            status='open'
        ).first()
        if existing_open_report:
            flash('You already have an open report for this user.', 'info')
            return redirect(request.referrer or url_for('profile.view', user_id=user_id))

        report = Report()
        report.reporter_id = current_user.id
        report.reported_user_id = user_id
        report.reason = reason
        
        admin_user = User.query.filter_by(role='admin').first()
        if admin_user:
            notification = queue_notification(
                recipient_id=admin_user,
                title='New User Report',
                message=f'User {current_user.username} has reported user {user.username} for: {reason}',
                category='user report',
                actor_id=current_user.id,
                entity_type='user_report',
                entity_id=report.id
            )

        db.session.add(report)
        if notification:
            db.session.add(notification)
        db.session.commit()
        
        flash('User report submitted.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error creating report for user {user_id}: {e}')
        flash('Unable to submit this report right now.', 'danger')

    return redirect(request.referrer or url_for('profile.view', user_id=user_id))
