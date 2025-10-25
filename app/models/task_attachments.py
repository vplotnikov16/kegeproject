from app.extensions import db


class TaskAttachment(db.Model):
    __tablename__ = 'task_attachments'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    task_id = db.Column(
        db.Integer,
        db.ForeignKey('tasks.id', ondelete='CASCADE'),
        nullable=False,
    )
    path = db.Column(
        db.String,
        nullable=False,
    )

    # passive_deletes=True для доверия физическому каскаду СУБД
    task = db.relationship(
        'Task',
        back_populates='attachments',
        passive_deletes=True,
    )
