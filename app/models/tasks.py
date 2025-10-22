from app.extensions import db
from app.utils.date_utils import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    statement_html = db.Column(db.Text, nullable=False)
    answer = db.Column(db.String, nullable=False)
    published_at = db.Column(db.DateTime, default=utcnow)
    source = db.Column(db.String(255), nullable=True)

    attachments = db.relationship('TaskAttachment', back_populates='task')
    variant_links = db.relationship('VariantTask', back_populates='task')
