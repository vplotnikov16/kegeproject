from flask import Blueprint, render_template, url_for
from flask_login import login_required, current_user

from app.forms.generic import ConfirmForm
from app.models import Task
from app.utils.text_utils import make_snippet

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('')
@login_required
def profile():
    return render_template('profile/profile.html', user=current_user)


@profile_bp.route('/stats')
@login_required
def stats():
    return render_template('profile/stats.html', user=current_user)


@profile_bp.route('/my_tasks')
@login_required
def my_tasks():
    q = Task.query.filter_by(author_id=current_user.id).order_by(Task.published_at.desc())
    tasks = q.all()

    prepared = []
    for t in tasks:
        prepared.append({
            'id': t.id,
            'number': t.number,
            'source': t.source,
            'published_at': t.published_at,
            'variant_links': t.variant_links,  # в шаблоне взяли длину
            'answer': t.answer,
            'statement_html_snippet': make_snippet(t.statement_html, max_chars=800),
            'can_edit': True,
            'author_username': current_user.username,
            'author_avatar_url': current_user.avatar_url if hasattr(current_user, 'avatar_url') else None,
            'view_url': url_for('tasks.view_task', task_id=t.id),
            'edit_url': url_for('tasks.edit_task', task_id=t.id),
            'delete_url': url_for('tasks.delete_task', task_id=t.id),
        })

    delete_form = ConfirmForm()
    return render_template('profile/my_tasks.html', tasks=prepared, delete_form=delete_form)


@profile_bp.route('/my_variants')
@login_required
def my_variants():
    return render_template('profile/my_variants.html', user=current_user)
