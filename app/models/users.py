from typing import Dict

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.model_abc import IModel
from app.models.roles import DefaultRoles
from app.utils.date_utils import utcnow
from app.utils.name_utils import get_username


class User(UserMixin, IModel):
    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    username = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
    )
    first_name = db.Column(
        db.String(20),
        nullable=False,
    )
    last_name = db.Column(
        db.String(40),
        nullable=False,
    )
    middle_name = db.Column(
        db.String(20),
        nullable=True,
    )
    password_hash = db.Column(
        db.String(256),
        nullable=False,
    )
    registered_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
    )

    # при удалении пользователя строки в user_roles удалятся (работает через FK ondelete)
    roles = db.relationship(
        'Role',
        secondary='user_roles',
        back_populates='users',
        # passive_deletes=True нужен для доверия алхимии к физическому каскаду СУБД
        passive_deletes=True,
    )
    tasks = db.relationship(
        'Task',
        back_populates='author',
        passive_deletes=True
    )
    avatar = db.relationship(
        'UserAvatar',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    variants = db.relationship(
        'Variant',
        back_populates='author',
        passive_deletes=True
    )
    attempts = db.relationship(
        'Attempt',
        back_populates='examinee',
        passive_deletes=True
    )

    @classmethod
    def view_name(cls) -> str:
        return "Пользователи"

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @classmethod
    def generate_username(cls, first_name: str, last_name: str, middle_name: str | None = None) -> str:
        """
        Генерация уникального имени пользователя на основе ФИО.
        Пример: vv_plotnikov или vv_plotnikov2, если vv_plotnikov уже существует
        :param first_name: имя
        :param last_name: фамилия
        :param middle_name: отчество
        :return: имя пользователя
        """

        base_username = get_username(first_name, last_name, middle_name)
        username = base_username
        count = 1
        while cls.query.filter_by(username=username).first() is not None:
            count += 1
            username = f'{base_username}{count}'

        return username

    def has_role(self, role_name: str) -> bool:
        """
        Проверка, есть ли у пользователя указанная роль.

        :param role_name: Имя роли (например, 'admin', 'user', 'guest')
        :return: True, если роль найдена
        """
        return any(role.name == role_name for role in self.roles)

    @property
    def is_admin(self) -> bool:
        """
        Проверка, является ли пользователь администратором.
        Предполагаем, что роль администратора имеет id = 0.
        """
        # FIXME: с id == 0 такой костыль, надо однажды это как-нибудь исправить
        return self.has_role(DefaultRoles.admin)

    @property
    def as_dict(self) -> Dict:
        from flask import url_for
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'middle_name': self.middle_name or '',
            'registered_at': self.registered_at.strftime("%d.%m.%Y"),
            'avatar': url_for('profile.get_avatar', user_id=self.id),
        }

    def __repr__(self) -> str:
        return f'User(id={self.id} username={self.username} fullname={self.last_name} {self.first_name} {self.middle_name})'


def ensure_default_admin_account(app=None) -> None:
    from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError

    ctx_entered = False
    if app is not None:
        ctx = app.app_context()
        ctx.push()
        ctx_entered = True

    try:
        # Проверяем, есть ли уже администратор
        admin_user = User.query.filter_by(username='admin').first()

        if admin_user:
            # Администратор уже существует
            if not admin_user.is_admin:
                # Если существует но не админ - добавляем роль админа
                from app.models.roles import Role
                admin_role = Role.query.filter_by(name='admin').first()
                if admin_role and admin_role not in admin_user.roles:
                    admin_user.roles.append(admin_role)
                    db.session.commit()
        else:
            # Создаём нового администратора
            from app.models.roles import Role

            admin_user = User(
                username='admin',
                first_name='Админ',
                last_name='Админов',
                middle_name='Админович',
            )
            admin_user.set_password('admin')

            # Добавляем роль админа
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role:
                admin_user.roles.append(admin_role)

            db.session.add(admin_user)
            db.session.commit()

    except (OperationalError, ProgrammingError):
        # Таблицы могут ещё не существовать (до миграций)
        db.session.rollback()
    except IntegrityError:
        # Может быть race condition если несколько процессов создают одновременно
        db.session.rollback()
    except Exception:
        # На всякий случай откатим и пробросим ошибку дальше
        db.session.rollback()
        raise
    finally:
        if ctx_entered:
            ctx.pop()
