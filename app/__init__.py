from flask import Flask

from .cli import seed
from .config import Config
from .extensions import db, migrate, login_manager
from .models import User


def _register_blueprints(flask_app):
    from app.routes.auth import auth_bp
    flask_app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.pages import pages_bp
    flask_app.register_blueprint(pages_bp, url_prefix='/')

    from app.routes.tasks import tasks_bp
    flask_app.register_blueprint(tasks_bp, url_prefix='/tasks')

    from app.routes.attachments import attachments_bp
    flask_app.register_blueprint(attachments_bp, url_prefix='/attachments')

    from app.routes.profile import profile_bp
    flask_app.register_blueprint(profile_bp, url_prefix='/profile')


def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    login_manager.init_app(flask_app)
    login_manager.login_view = 'pages.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app import models

    # регистрация blueprint'ов
    _register_blueprints(flask_app)

    # регистрация cli
    flask_app.cli.add_command(seed)

    return flask_app
