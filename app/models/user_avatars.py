from app.extensions import db
from app.models.model_abc import Binary, IModel
from app.utils.date_utils import utcnow


class UserAvatar(IModel):
    __tablename__ = 'user_avatars'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True,
    )

    filename = db.Column(db.String(255), nullable=True)
    content_type = db.Column(db.String(120), nullable=True)
    size = db.Column(db.Integer, nullable=True)
    data = db.Column(Binary, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', back_populates='avatar', passive_deletes=True)

    @classmethod
    def view_name(cls) -> str:
        return "Аватарки пользователей"

    @property
    def url(self):
        from flask import url_for
        return url_for('profile.get_avatar', user_id=self.user_id)
