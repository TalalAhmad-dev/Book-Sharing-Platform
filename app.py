from flask import Flask
from config import Config
from extensions import db, login_manager, migrate
from models import *

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

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(borrow_bp, url_prefix='/borrow')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
