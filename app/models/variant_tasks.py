from app.extensions import db


class VariantTask(db.Model):
    __tablename__ = 'variant_tasks'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('variants.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    task_id = db.Column(
        db.Integer,
        db.ForeignKey('tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    order = db.Column(
        db.Integer,
        default=0,
        nullable=True,
    )
    answer_type = db.Column(
        db.String(50),
        default='single',
        nullable=True,
        comment='single, double, или table'
    )
    answer_count = db.Column(
        db.Integer,
        default=1,
        nullable=True,
        comment='Число колонок в таблице'
    )

    variant = db.relationship(
        'Variant',
        back_populates='tasks',
        # passive_deletes=True нужен для доверия алхимии к физическому каскаду СУБД
        passive_deletes=True,
    )
    task = db.relationship(
        'Task',
        back_populates='variant_links',
        # passive_deletes=True нужен для доверия алхимии к физическому каскаду СУБД
        passive_deletes=True,
    )
    attempt_answers = db.relationship(
        'AttemptAnswer',
        back_populates='variant_task',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    __table_args__ = (
        db.UniqueConstraint('variant_id', 'task_id', name='uq_variant_task'),
        db.Index('ix_variant_tasks_order', 'variant_id', 'order'),
    )
