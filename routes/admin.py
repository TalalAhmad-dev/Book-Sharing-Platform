from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from functools import wraps
from models import User, Book, Report, BorrowRequest
from extensions import db

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
    stats = {
        'users': User.query.count(),
        'books': Book.query.filter(Book.deleted_at.is_(None)).count(),
        'reports': Report.query.filter_by(status='open').count(),
        'borrows': BorrowRequest.query.filter_by(status='borrowed').count()
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/<int:user_id>/block', methods=['POST'])
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot block yourself.", "error")
        return redirect(url_for('admin.users'))
    
    user.status = 'blocked'
    db.session.commit()
    flash(f"User {user.name} blocked.", "success")
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/unblock', methods=['POST'])
@login_required
@admin_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'active'
    db.session.commit()
    flash(f"User {user.name} unblocked.", "success")
    return redirect(url_for('admin.users'))

@admin_bp.route('/books')
@login_required
@admin_required
def books():
    all_books = Book.query.filter(Book.deleted_at.is_(None)).all()
    return render_template('admin/books.html', books=all_books)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    all_reports = Report.query.all()
    return render_template('admin/reports.html', reports=all_reports)

@admin_bp.route('/reports/<int:report_id>/reviewed', methods=['POST'])
@login_required
@admin_required
def mark_report_reviewed(report_id):
    report = Report.query.get_or_404(report_id)
    if report.status != 'open':
        flash(f"Report has already been {report.status}. Can't mark as reviewed.", "warning")
        return redirect(url_for('admin.reports'))
    report.status = 'reviewed'
    db.session.commit()
    flash(f"Report marked as reviewed.", "success")
    return redirect(url_for('admin.reports'))


@admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.status != 'open':
        flash(f"Report has already been {report.status}. Can't dismiss.", "warning")
        return redirect(url_for('admin.reports'))
    report.status = 'dismissed'
    db.session.commit()
    flash(f"Report has been dismissed.", "info")
    return redirect(url_for('admin.reports'))
