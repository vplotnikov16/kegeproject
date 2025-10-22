from app.extensions import db


class VariantTask(db.Model):
    __tablename__ = 'variant_tasks'

    variant_id = db.Column(db.Integer, db.ForeignKey('variants.id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), primary_key=True)

    variant = db.relationship('Variant', back_populates='tasks')
    task = db.relationship('Task', back_populates='variant_links')
