from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.utils.date_utils import utcnow
from app.utils.name_utils import get_username


class User(UserMixin, db.Model):
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

    @property
    def is_admin(self) -> bool:
        """
        Проверка, является ли пользователь администратором.
        Предполагаем, что роль администратора имеет id = 0.
        """
        # FIXME: с id == 0 такой костыль, надо однажды это как-нибудь исправить
        return any(role.id == 0 for role in self.roles)
