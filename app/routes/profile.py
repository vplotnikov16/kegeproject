import os
from io import BytesIO

from flask import Blueprint, render_template, url_for, request, redirect, flash, jsonify, abort, send_file, current_app
from flask_login import login_required, current_user

from app.forms.generic import ConfirmForm
from app.models import Task, Variant, UserAvatar
from app.forms.profile import AvatarUploadForm
from app import db
from app.services.task_services import TaskService
from app.utils.date_utils import utcnow

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('')
@login_required
def profile():
    avatar_form = AvatarUploadForm()
    my_tasks = Task.query.filter_by(author_id=current_user.id).order_by(Task.published_at.desc()).limit(5).all()
    my_variants = Variant.query.filter_by(author_id=current_user.id).order_by(Variant.created_at.desc()).limit(5).all()
    return render_template('profile/profile.html', user=current_user, avatar_form=avatar_form,
                           my_tasks=my_tasks, my_variants=my_variants)


@profile_bp.get("/avatar/<int:user_id>")
def get_avatar(user_id):
    avatar = UserAvatar.query.filter_by(user_id=user_id).first()
    if not avatar:
        default_path = os.path.join(current_app.root_path, "static", "img", "ava.png")
        if not os.path.exists(default_path):
            abort(404)
        return send_file(default_path, mimetype="image/png")
    return send_file(
        BytesIO(avatar.data),
        mimetype=avatar.content_type,
        download_name=f"avatar_{user_id}.png"
    )


@profile_bp.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    f = request.files.get('avatar_file')
    if not f:
        flash('Файл не выбран', 'warning')
        return redirect(url_for('profile.profile'))

    data = f.read()
    ua = current_user.avatar
    if ua is None:
        ua = UserAvatar(user_id=current_user.id)
    ua.filename = f.filename
    ua.content_type = f.mimetype
    ua.size = len(data)
    ua.data = data
    ua.uploaded_at = utcnow()
    db.session.add(ua)
    db.session.commit()
    flash('Аватар обновлён', 'success')
    return redirect(url_for('profile.profile'))


@profile_bp.route('/stats')
@login_required
def stats():
    return render_template('profile/stats.html', user=current_user)


@profile_bp.route('/my_tasks')
@login_required
def my_tasks():
    tasks = TaskService.get_by_author(current_user.id)

    prepared = [t.as_dict for t in tasks[-5:]]

    delete_form = ConfirmForm()
    return render_template('profile/my_tasks.html', tasks=prepared, delete_form=delete_form)


@profile_bp.route('/my_variants')
@login_required
def my_variants():
    return render_template('profile/my_variants.html', user=current_user)
