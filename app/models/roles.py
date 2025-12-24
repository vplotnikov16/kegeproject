from enum import Enum

from app.extensions import db
from app.models.model_abc import IModel


class DefaultRoles(str, Enum):
    guest = 'guest'
    admin = 'admin'
    user = 'user'


class Role(IModel):
    __tablename__ = 'roles'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    name = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
    )

    # при удалении роли строки в user_roles удалятся сами из-за FK ondelete, пользователи при этом сохранятся
    users = db.relationship('User', secondary='user_roles', back_populates='roles', passive_deletes=True)

    @classmethod
    def view_name(cls) -> str:
        return "Роли"

    def __repr__(self) -> str:
        return f"Role(id={self.id} name={self.name})"


def ensure_default_roles(app=None) -> None:
    from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError
    ctx_entered = False
    if app is not None:
        ctx = app.app_context()
        ctx.push()
        ctx_entered = True

    try:
        for role_enum in DefaultRoles:
            role_name = role_enum.value
            existing = Role.query.filter_by(name=role_name).first()
            if existing:
                continue

            role = Role(name=role_name)
            db.session.add(role)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    except (OperationalError, ProgrammingError):
        # таблицы могут ещё не существовать (например, до миграций) - просто ничего не делаем
        db.session.rollback()
    except Exception:
        # на всякий случай откатим и пробросим ошибку дальше
        db.session.rollback()
        raise
    finally:
        if ctx_entered:
            ctx.pop()
