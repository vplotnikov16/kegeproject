from typing import Dict

from flask import url_for

from app.extensions import db
from app.utils.date_utils import utcnow


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

    filename = db.Column(db.String(32), nullable=False)
    content_type = db.Column(db.String(120), nullable=True)
    size = db.Column(db.Integer, nullable=True)
    data = db.Column(db.LargeBinary, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # passive_deletes=True для доверия физическому каскаду СУБД
    task = db.relationship(
        'Task',
        back_populates='attachments',
        passive_deletes=True,
    )

    @property
    def as_json(self) -> Dict:
        return {
            'id': self.id,
            'filename': self.filename,
            'content_type': self.content_type,
            'size': self.size,
            'uploaded_at': self.uploaded_at,
            'download_url': url_for('attachments.download_attachment', attachment_id=self.id),
        }
