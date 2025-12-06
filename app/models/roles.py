from typing import Iterable, Tuple

from app.extensions import db


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    name = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
    )

    # при удалении роли строки в user_roles удалятся сами из-за FK ondelete, пользователи при этом сохранятся
    users = db.relationship('User', secondary='user_roles', back_populates='roles', passive_deletes=True)


def _default_roles() -> Iterable[Tuple[int, str]]:
    roles = (
        (0, 'admin'),
        (1, 'guest'),
        (2, 'user'),
    )
    return roles


def ensure_default_roles(app=None) -> None:
    from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError
    ctx_entered = False
    if app is not None:
        ctx = app.app_context()
        ctx.push()
        ctx_entered = True

    try:
        for role_id, role_name in _default_roles():
            existing = Role.query.filter_by(name=role_name).first()
            if existing:
                continue

            id_taken = Role.query.get(role_id)
            if id_taken is None:
                role = Role(id=role_id, name=role_name)
            else:
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
