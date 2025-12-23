from app.extensions import db
from app.models.model_abc import IModel
from app.utils.date_utils import utcnow


class AttemptAnswer(IModel):
    __tablename__ = 'attempt_answers'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey('attempts.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    variant_task_id = db.Column(
        db.Integer,
        db.ForeignKey('variant_tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    answer_text = db.Column(
        db.String(255),
        nullable=True,
    )
    is_correct = db.Column(
        db.Boolean,
        nullable=True,
    )
    updated_at = db.Column(
        db.DateTime,
        default=utcnow,
        onupdate=utcnow,
    )

    attempt = db.relationship(
        'Attempt',
        back_populates='answers',
    )
    variant_task = db.relationship(
        'VariantTask',
        back_populates='attempt_answers',
    )

    __table_args__ = (
        db.UniqueConstraint('attempt_id', 'variant_task_id', name='uq_attempt_variant_task'),
        db.Index('ix_attempt_answers_attempt', 'attempt_id'),
    )

    @classmethod
    def view_name(cls) -> str:
        return "Ответы в попытке"

    def __repr__(self) -> str:
        return f'AttemptAnswer(attempt={self.attempt_id}, variant_task={self.variant_task})'
