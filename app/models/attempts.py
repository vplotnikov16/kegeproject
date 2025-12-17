from typing import Dict

from app.extensions import db
from app.models.model_abc import IModel
from app.utils.date_utils import utcnow


class Attempt(IModel):
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

    examinee = db.relationship(
        'User',
        back_populates='attempts',
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

    @property
    def as_dict(self) -> Dict:
        return {
            'id': self.id,
            'variant_id': self.variant_id,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S'),
            'finished_at': self.finished_at.strftime('%Y-%m-%d %H:%M:%S') if self.finished_at else None,
            'duration': self.variant.duration,
        }

    @classmethod
    def view_name(cls) -> str:
        return "Попытки"

    def __repr__(self) -> str:
        return f"Attempt(examinee={self.examinee}, variant={self.variant})"
