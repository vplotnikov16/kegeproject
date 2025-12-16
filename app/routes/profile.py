import os
from io import BytesIO

from flask import Blueprint, render_template, url_for, request, redirect, flash, jsonify, abort, send_file, current_app
from flask_login import login_required, current_user

from app.forms.generic import ConfirmForm
from app.models import Task, Variant, UserAvatar, Attempt
from app.forms.profile import AvatarUploadForm
from app import db
from app.services.task_services import TaskService
from app.services.variant_services import VariantService
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
    from app.services.user_stats_service import UserStatsService

    # Получить все попытки пользователя
    attempts = UserStatsService.get_user_attempts(current_user.id, limit=100)
    summary = UserStatsService.get_summary_stats(current_user.id)
    task_performance = UserStatsService.get_performance_by_task_number(current_user.id)
    speed_trends = UserStatsService.get_solving_speed_trends(current_user.id)

    return render_template('profile/stats.html',
                           user=current_user,
                           attempts=attempts,
                           summary=summary,
                           task_performance=task_performance,
                           speed_trends=speed_trends
                           )


@profile_bp.route('/attempt/<int:attempt_id>')
@login_required
def attempt_details(attempt_id: int):
    from app.services.user_stats_service import UserStatsService

    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        abort(404)
    if attempt.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    details = UserStatsService.get_attempt_details_with_scoring(attempt_id, current_user.id)
    if not details:
        abort(404)

    return render_template('profile/attempt_details.html',
                           user=current_user,
                           attempt_details=details
                           )


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
    variants = VariantService.get_by_author(current_user.id)
    prepared = [v.as_dict for v in variants]

    delete_form = ConfirmForm()

    return render_template('profile/my_variants.html', variants=prepared, delete_form=delete_form)
