from io import BytesIO

from flask import Blueprint, send_file, abort, flash, redirect, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.forms.generic import ConfirmForm
from app.models import TaskAttachment

attachments_bp = Blueprint('attachments', __name__)


@attachments_bp.route('/<int:attachment_id>/download')
def download_attachment(attachment_id):
    attachment = TaskAttachment.query.get_or_404(attachment_id)
    if not attachment.data:
        abort(404)

    # создаем in-memory файл
    file_data = BytesIO(attachment.data)
    # используем оригинальное имя или id
    filename = attachment.filename or f'attachment_{attachment.id}'

    return send_file(
        file_data,
        as_attachment=True,
        download_name=filename,
        mimetype=attachment.content_type or 'application/octet-stream'
    )


@attachments_bp.route('/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    """
    Удаление отдельного вложения (POST). Возвращаемся на страницу редактирования задачи.
    """
    attachment = TaskAttachment.query.get_or_404(attachment_id)
    task = attachment.task

    can_delete = current_user.is_authenticated
    can_delete &= current_user.is_admin or task.author is not None and current_user.id == task.author.id

    if not can_delete:
        abort(403)

    form = ConfirmForm()
    if not form.validate_on_submit():
        flash("Неверный запрос при удалении вложения.", "warning")
        return redirect(url_for('tasks.edit_task', task_id=task.id))

    db.session.delete(attachment)
    db.session.commit()
    flash("Вложение удалено.", "success")
    return redirect(url_for('tasks.edit_task', task_id=task.id))
