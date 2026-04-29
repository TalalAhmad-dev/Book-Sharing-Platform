from flask import Blueprint, render_template, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy.orm import joinedload
from models import User, Book, Report, BorrowRequest
from extensions import db
from notification_service import queue_notification

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    try:
        stats = {
            'users': User.query.count(),
            'books': Book.query.filter(Book.deleted_at.is_(None)).count(),
            'reports': Report.query.filter_by(status='open').count(),
            'borrows': BorrowRequest.query.filter_by(status='borrowed').count()
        }

        open_reports = (
            Report.query.options(
                joinedload(Report.reporter),
                joinedload(Report.reported_book),
                joinedload(Report.reported_user)
            )
            .filter_by(status='open').order_by(Report.created_at.desc()).limit(5).all()
        )

        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

        recent_books = (
            Book.query.options(joinedload(Book.owner)).filter(Book.deleted_at.is_(None))
            .order_by(Book.created_at.desc())
            .limit(5).all()
            )
        

        return render_template(
            'admin/dashboard.html',
            stats=stats,
            open_reports=open_reports,
            recent_users=recent_users,
            recent_books=recent_books
        )
    except Exception as e:
        current_app.logger.exception(f'Error loading admin dashboard: {e}')
        flash('Unable to load the admin dashboard right now.', 'danger')
        return render_template(
            'admin/dashboard.html',
            stats={'users': 0, 'books': 0, 'reports': 0, 'borrows': 0},
            open_reports=[],
            recent_users=[],
            recent_books=[]
        )

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    try:
        all_users = User.query.all()
        return render_template('admin/users.html', users=all_users)
    except Exception as e:
        current_app.logger.exception(f'Error loading admin users list: {e}')
        flash('Unable to load users right now.', 'danger')
        return render_template('admin/users.html', users=[])

@admin_bp.route('/users/<int:user_id>/block', methods=['POST'])
@login_required
@admin_required
def block_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash("You cannot block yourself.", "error")
            return redirect(url_for('admin.users'))

        if user.status == 'blocked':
            flash(f"User {user.name} is already blocked.", "info")
            return redirect(url_for('admin.users'))

        user.status = 'blocked'
        notification = queue_notification(
            recipient_id=user.id,
            actor_id=current_user.id,
            category='admin',
            title='Account blocked',
            message='Your account has been blocked by an administrator.',
            entity_type='user',
            entity_id=user.id
        )
        if notification:
            db.session.add(notification)
        db.session.commit()
        flash(f"User {user.name} blocked.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error blocking user {user_id}: {e}')
        flash('Unable to block this user right now.', 'danger')

    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/unblock', methods=['POST'])
@login_required
@admin_required
def unblock_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        if user.status == 'active':
            flash(f"User {user.name} is already active.", "info")
            return redirect(url_for('admin.users'))

        user.status = 'active'
        notification = queue_notification(
            recipient_id=user.id,
            actor_id=current_user.id,
            category='admin',
            title='Account unblocked',
            message='Your account has been reactivated by an administrator.',
            entity_type='user',
            entity_id=user.id
        )
        if notification:
            db.session.add(notification)
        db.session.commit()
        flash(f"User {user.name} unblocked.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error unblocking user {user_id}: {e}')
        flash('Unable to unblock this user right now.', 'danger')

    return redirect(url_for('admin.users'))

@admin_bp.route('/books')
@login_required
@admin_required
def books():
    try:
        all_books = Book.query.filter(Book.deleted_at.is_(None)).all()
        return render_template('admin/books.html', books=all_books)
    except Exception as e:
        current_app.logger.exception(f'Error loading admin books list: {e}')
        flash('Unable to load books right now.', 'danger')
        return render_template('admin/books.html', books=[])

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    try:
        all_reports = Report.query.all()
        return render_template('admin/reports.html', reports=all_reports)
    except Exception as e:
        current_app.logger.exception(f'Error loading admin reports list: {e}')
        flash('Unable to load reports right now.', 'danger')
        return render_template('admin/reports.html', reports=[])

@admin_bp.route('/reports/<int:report_id>/reviewed', methods=['POST'])
@login_required
@admin_required
def mark_report_reviewed(report_id):
    try:
        report = Report.query.get_or_404(report_id)
        if report.status != 'open':
            flash(f"Report has already been {report.status}. Can't mark as reviewed.", "warning")
            return redirect(url_for('admin.reports'))

        report.status = 'reviewed'
        notification = queue_notification(
            recipient_id=report.reporter_id,
            actor_id=current_user.id,
            category='admin',
            title='Report reviewed',
            message='Your report has been reviewed by an administrator.',
            entity_type='report',
            entity_id=report.id
        )
        if notification:
            db.session.add(notification)
        db.session.commit()
        flash("Report marked as reviewed.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error marking report {report_id} as reviewed: {e}')
        flash('Unable to update this report right now.', 'danger')

    return redirect(url_for('admin.reports'))


@admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_report(report_id):
    try:
        report = Report.query.get_or_404(report_id)
        if report.status != 'open':
            flash(f"Report has already been {report.status}. Can't dismiss.", "warning")
            return redirect(url_for('admin.reports'))

        report.status = 'dismissed'
        notification = queue_notification(
            recipient_id=report.reporter_id,
            actor_id=current_user.id,
            category='admin',
            title='Report dismissed',
            message='Your report has been dismissed by an administrator.',
            entity_type='report',
            entity_id=report.id
        )
        if notification:
            db.session.add(notification)
        db.session.commit()
        flash("Report has been dismissed.", "info")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error dismissing report {report_id}: {e}')
        flash('Unable to update this report right now.', 'danger')

    return redirect(url_for('admin.reports'))
