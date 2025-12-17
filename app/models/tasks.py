from typing import Dict

from flask_login import current_user

from app.extensions import db
from app.utils.date_utils import utcnow
from app.utils.text_utils import make_snippet


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    number = db.Column(
        db.Integer,
        nullable=False,
    )
    statement_html = db.Column(
        db.Text,
        nullable=False,
    )
    answer = db.Column(
        db.String,
        nullable=False,
    )
    published_at = db.Column(
        db.DateTime,
        default=utcnow,
    )
    source = db.Column(
        db.String(255),
        nullable=True,
    )

    author_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,  # сначала делаем nullable, чтобы миграция не ломала старые строки
        index=True,
    )
    author = db.relationship('User', back_populates='tasks', lazy='joined')

    # при удалении задачи удаляются вложения, связи с вариантами, ответы в попытках
    attachments = db.relationship(
        'TaskAttachment',
        back_populates='task',
        cascade='all, delete-orphan',
        # passive_deletes=True для доверия физическому каскаду СУБД
        passive_deletes=True,
    )
    variant_links = db.relationship(
        'VariantTask',
        back_populates='task',
        cascade='all, delete-orphan',
        # passive_deletes=True для доверия физическому каскаду СУБД
        passive_deletes=True,
    )

    @property
    def as_dict(self) -> Dict:
        from flask import url_for

        author_data = None
        if self.author:
            author_data = {
                "id": self.author.id,
                "first_name": self.author.first_name,
                "last_name": self.author.last_name,
                "username": self.author.username,
            }

        variant_links_data = {
            "variant_links_count": len(self.variant_links),
            "variant_links_ids": [vl.variant_id for vl in self.variant_links],
        }

        can_edit = False
        if current_user.is_authenticated:
            can_edit = current_user.is_admin or self.author is not None and current_user.id == self.author.id
        return {
            "id": self.id,
            "number": self.number,
            "statement_html": self.statement_html,
            "statement_html_snippet": make_snippet(self.statement_html),
            "answer": self.answer,
            "published_at": self.published_at.strftime("%d.%m.%Y") if self.published_at else None,
            "source": self.source,
            "author": author_data,
            "author_username": self.author.username if self.author else None,
            "author_avatar_url": url_for('profile.get_avatar', user_id=self.author.id if self.author else -1),
            "variant_links": variant_links_data,
            "can_edit": can_edit,
            "view_url": url_for('tasks.view_task', task_id=self.id),
            "edit_url": url_for('tasks.edit_task', task_id=self.id),
            "delete_url": url_for('tasks.delete_task', task_id=self.id),
            'attachments': [a.as_dict for a in self.attachments],
        }

    @classmethod
    def view_name(cls) -> str:
        return "Задачи"
