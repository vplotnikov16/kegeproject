from app.extensions import db
from app.utils.date_utils import utcnow


class Attempt(db.Model):
    __tablename__ = 'attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variants.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='attempts')
    variant = db.relationship('Variant', back_populates='attempts')
    answers = db.relationship('AttemptAnswer', back_populates='attempt')

    __table_args__ = (
        db.UniqueConstraint('id', 'variant_id', name='uq_attempt_variant'),
    )
