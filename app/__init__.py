from flask import Flask

from .config import Config
from .extensions import db, migrate, login_manager
from .models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'pages.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app import models

    # регистрация blueprint'ов
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.pages import pages_bp
    app.register_blueprint(pages_bp, url_prefix='/')

    return app
