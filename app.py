from flask import Flask, request, redirect, url_for, flash
from config import Config
from extensions import db, login_manager, migrate
from models import *
from datetime import datetime
import json
from flask_login import current_user, logout_user

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.books import books_bp
    from routes.borrow import borrow_bp
    from routes.dashboard import dashboard_bp
    from routes.admin import admin_bp
    from routes.profile import profile_bp
    from routes.favorites import favorites_bp
    from routes.reports import reports_bp
    from routes.inbox import inbox_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(borrow_bp, url_prefix='/borrow')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(favorites_bp, url_prefix='/favorites')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(inbox_bp, url_prefix='/inbox')

    @app.template_filter('fromjson')
    def fromjson(value):
        try:
            return json.loads(value) if value else value
        except (ValueError, TypeError):
            return value

    @app.template_filter('format_date')
    def format_date(value):
        if not value: return ""
        return value.strftime('%b %d, %Y')

    @app.template_filter('format_time')
    def format_time(value):
        if not value: return ""
        return value.strftime('%I:%M %p')

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    @app.context_processor
    def inject_unread_notification_count():
        unread_notifications_count = 0
        if current_user.is_authenticated:
            unread_notifications_count = Notification.query.filter_by(
                recipient_id=current_user.id,
                is_read=False
            ).count()
        return {'unread_notifications_count': unread_notifications_count}

    @app.before_request
    def enforce_blocked_user_logout():
        if not current_user.is_authenticated:
            return None
        if current_user.status != 'blocked':
            return None

        allowed_endpoints = {'auth.login', 'auth.logout', 'static'}
        if request.endpoint in allowed_endpoints:
            return None

        logout_user()
        flash('Your account has been blocked.', 'error')
        return redirect(url_for('auth.login'))

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
