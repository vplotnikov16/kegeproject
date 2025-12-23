from typing import Dict

from app.extensions import db
from app.models.model_abc import IModel
from app.utils.date_utils import utcnow


class Variant(IModel):
    __tablename__ = 'variants'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    source = db.Column(
        db.String(255),
        nullable=True,
    )
    created_at = db.Column(
        db.DateTime,
        default=utcnow,
    )
    duration = db.Column(
        db.Integer,
        nullable=False,
        default=14100,
    )

    author_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    author = db.relationship('User', back_populates='variants', lazy='joined')

    # при удалении варианта удаляются записи в variant_tasks, но не в Attempts
    tasks = db.relationship(
        'VariantTask',
        back_populates='variant',
        cascade='all, delete-orphan',
        # passive_deletes=True нужен для доверия алхимии к физическому каскаду СУБД
        passive_deletes=True,
    )
    attempts = db.relationship(
        'Attempt',
        back_populates='variant',
    )

    @classmethod
    def view_name(cls) -> str:
        return "Варианты"

    @property
    def as_dict(self) -> Dict:
        from flask_login import current_user
        from flask import url_for

        can_edit = False
        if current_user.is_authenticated:
            can_edit = current_user.is_admin or current_user.id == self.author_id

        return {
            "id": self.id,
            "source": self.source,
            "created_at": self.created_at.strftime("%d.%m.%Y"),
            "duration": self.duration,
            "tasks_count": len(self.tasks),
            "can_edit": can_edit,
            "author_username": self.author.username if self.author else None,
            "author_avatar_url": url_for('profile.get_avatar', user_id=self.author.id if self.author else -1),
            "view_url": url_for('variants.view_variant', variant_id=self.id),
            "edit_url": url_for('variants.edit_variant', variant_id=self.id),
            "delete_url": url_for('variants_api.delete_variant', variant_id=self.id),
        }

    def __repr__(self) -> str:
        return f'Variant(id={self.id}, author={self.author})'
