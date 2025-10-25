from app.extensions import db


class VariantTask(db.Model):
    __tablename__ = 'variant_tasks'

    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('variants.id', ondelete='CASCADE'),
        primary_key=True,
    )
    task_id = db.Column(
        db.Integer,
        db.ForeignKey('tasks.id', ondelete='CASCADE'),
        primary_key=True,
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
