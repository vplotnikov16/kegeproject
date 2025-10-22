from app.extensions import db


class AttemptAnswer(db.Model):
    __tablename__ = 'attempt_answers'

    attempt_id = db.Column(db.Integer, db.ForeignKey('attempts.id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), primary_key=True)
    answer_text = db.Column(db.String, nullable=True)
    is_correct = db.Column(db.Boolean, nullable=True)

    attempt = db.relationship('Attempt', back_populates='answers')
    task = db.relationship('Task')
