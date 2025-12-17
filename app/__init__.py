from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme

from .cli import seed
from .config import Config
from .extensions import db, migrate, login_manager
from .models import User, Task, Variant, Attempt, AttemptAnswer


def _register_entities_views(admin):
    from app.admin import get_model_view
    for model in models.models:  # pylint: disable=E0602
        view = get_model_view(model)
        admin.add_view(view(model, db.session, name=model.view_name()))


def _register_blueprints(flask_app):
    from app.routes.error_handlers import error_bp
    flask_app.register_blueprint(error_bp, url_prefix='/error')

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

    from app.routes.users import users_bp
    flask_app.register_blueprint(users_bp, url_prefix='/users')

    from app.routes.variants import variants_bp
    flask_app.register_blueprint(variants_bp, url_prefix='/variants')

    from app.routes.attempts import attempts_bp
    flask_app.register_blueprint(attempts_bp, url_prefix='/attempts')


def _register_api_blueprints(flask_app):
    from app.routes.api.tasks_api import tasks_api_bp
    flask_app.register_blueprint(tasks_api_bp, url_prefix='/api/tasks')

    from app.routes.api.profile_api import profile_api_bp
    flask_app.register_blueprint(profile_api_bp, url_prefix='/api/profile')

    from app.routes.api.variant_api import variants_api_bp
    flask_app.register_blueprint(variants_api_bp, url_prefix='/api/variants')


def _register_error_handlers(flask_app):
    from app.routes.error_handlers import register_error_handlers
    register_error_handlers(flask_app)


def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    login_manager.init_app(flask_app)
    login_manager.login_view = 'pages.login'

    # регистрация моделей в админке
    admin = Admin(flask_app, name='Тайная комната', theme=Bootstrap4Theme())
    _register_entities_views(admin)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app import models

    # регистрация blueprint'ов
    _register_blueprints(flask_app)

    # регистрация api blueprint'ов
    _register_api_blueprints(flask_app)

    # регистрация обработчиков ошибок
    _register_error_handlers(flask_app)

    # регистрация cli
    flask_app.cli.add_command(seed)

    return flask_app
