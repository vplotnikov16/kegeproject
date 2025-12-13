from app.extensions import db
from app.utils.date_utils import utcnow


class Attempt(db.Model):
    __tablename__ = 'attempts'

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('variants.id'),
        nullable=False,
    )
    started_at = db.Column(
        db.DateTime,
        default=utcnow
    )
    finished_at = db.Column(
        db.DateTime,
        nullable=True
    )

    user = db.relationship(
        'User',
        # при удалении пользователя удаляются все связанные попытки (через FK ondelete и backref cascade)
        backref=db.backref('attempts', cascade='all, delete-orphan', passive_deletes=True),
    )
    variant = db.relationship(
        'Variant',
        back_populates='attempts'
    )
    answers = db.relationship(
        'AttemptAnswer',
        back_populates='attempt',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    __table_args__ = (
        db.UniqueConstraint('user_id', 'variant_id', name='uq_user_variant_attempt'),
    )
