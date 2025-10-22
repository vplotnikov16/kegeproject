from app.extensions import db
from app.utils.date_utils import utcnow


class Variant(db.Model):
    __tablename__ = 'variants'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship('VariantTask', back_populates='variant')
    attempts = db.relationship('Attempt', back_populates='variant')
