from app.extensions import db


class UserRole(db.Model):
    __tablename__ = 'user_roles'

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
    )
    role_id = db.Column(
        db.Integer,
        db.ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True,
    )

    user = db.relationship('User', foreign_keys=[user_id], lazy='joined', overlaps='roles,users')
    role = db.relationship('Role', foreign_keys=[role_id], lazy='joined', overlaps='roles,users')

    @classmethod
    def view_name(cls):
        return "Роли пользователей"
