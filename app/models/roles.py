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
