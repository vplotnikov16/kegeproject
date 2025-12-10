from app.extensions import db
from app.utils.date_utils import utcnow


class Variant(db.Model):
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

    author_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,  # сначала делаем nullable, чтобы миграция не ломала старые строки
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
