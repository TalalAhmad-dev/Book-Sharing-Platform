from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Notification

inbox_bp = Blueprint('inbox', __name__)


def _redirect_back_or(endpoint, **values):
    return redirect(request.referrer or url_for(endpoint, **values))


@inbox_bp.route('/')
@login_required
def index():
    try:
        notifications = Notification.query.filter_by(
            recipient_id=current_user.id
        ).order_by(
            Notification.created_at.desc()
        ).all()
        return render_template('inbox/index.html', notifications=notifications)
    except Exception as e:
        current_app.logger.exception(f'Error loading inbox for user {current_user.id}: {e}')
        flash('Unable to load your inbox right now.', 'danger')
        return render_template('inbox/index.html', notifications=[])


@inbox_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            recipient_id=current_user.id
        ).first_or_404()

        if notification.is_read:
            return _redirect_back_or('inbox.index')

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error marking notification {notification_id} as read: {e}')
        flash('Unable to update this notification right now.', 'danger')

    return _redirect_back_or('inbox.index')


@inbox_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    try:
        Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).update(
            {
                Notification.is_read: True,
                Notification.read_at: datetime.now(timezone.utc)
            },
            synchronize_session=False
        )
        db.session.commit()
        flash('All notifications marked as read.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error marking all notifications as read for user {current_user.id}: {e}')
        flash('Unable to update notifications right now.', 'danger')

    return _redirect_back_or('inbox.index')


@inbox_bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete(notification_id):
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            recipient_id=current_user.id
        ).first_or_404()
        db.session.delete(notification)
        db.session.commit()
        flash('Notification removed.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f'Error deleting notification {notification_id}: {e}')
        flash('Unable to delete this notification right now.', 'danger')

    return _redirect_back_or('inbox.index')
