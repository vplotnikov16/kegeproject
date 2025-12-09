from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.forms.generic import ConfirmForm
from app.forms.tasks import NewTaskForm
from app.models import Task, TaskAttachment
from app.extensions import db

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route('/api/by_numbers', methods=['POST'])
def api_by_numbers():
    payload = request.get_json(silent=True) or {}
    numbers = payload.get('numbers') or []
    try:
        nums = [int(n) for n in numbers]
    except Exception:
        return jsonify({"error": "invalid numbers"}), 400

    tasks = Task.query.filter(Task.number.in_(nums)).order_by(Task.number, Task.id).all()

    def to_short(t):
        snippet = (t.statement_html[:300] + '...') if t.statement_html and len(t.statement_html) > 300 else (t.statement_html or '')
        return {
            "id": t.id,
            "number": t.number,
            "statement_html_snippet": snippet,
            "published_at": t.published_at.strftime('%Y-%m-%d') if t.published_at else None,
            "view_url": url_for('tasks.view_task', task_id=t.id)
        }

    return jsonify({"tasks": [to_short(t) for t in tasks]})


@tasks_bp.route('/api/by_ids', methods=['POST'])
def api_by_ids():
    payload = request.get_json(silent=True) or {}
    ids = payload.get('ids') or []
    try:
        ids_clean = [int(i) for i in ids]
    except Exception:
        return jsonify({"error": "invalid ids"}), 400

    tasks = Task.query.filter(Task.id.in_(ids_clean)).all()

    def to_short(t):
        snippet = (t.statement_html[:300] + '...') if t.statement_html and len(t.statement_html) > 300 else (t.statement_html or '')
        return {
            "id": t.id,
            "number": t.number,
            "statement_html_snippet": snippet,
            "published_at": t.published_at.strftime('%Y-%m-%d') if t.published_at else None,
            "view_url": url_for('tasks.view_task', task_id=t.id)
        }

    return jsonify({"tasks": [to_short(t) for t in tasks]})


@tasks_bp.route('/')
def tasks():
    return render_template('tasks/tasks.html')


@tasks_bp.route('/new_task', methods=['GET', 'POST'])
@login_required
def new_task():
    form = NewTaskForm()

    if not form.validate_on_submit():
        return render_template('tasks/new_task.html', form=form)

    number = form.number.data
    statement_html = form.statement_html.data
    answer = form.answer.data
    files = form.attachments.data

    task = Task(
        number=number,
        statement_html=statement_html,
        answer=answer,
        source='kegeproject',
        author_id=current_user.id,
    )
    db.session.add(task)
    db.session.commit()

    saved = []
    files = files or []
    for fs in files:
        if not (fs and fs.filename):
            continue
        filename = secure_filename(fs.filename)
        data = fs.read()
        attachment = TaskAttachment(
            task_id=task.id,
            filename=filename,
            content_type=fs.mimetype,
            size=len(data),
            data=data,
        )
        db.session.add(attachment)
        saved.append(attachment)

    db.session.commit()
    flash('Сохраненные файлы: {", ".join(saved)}', 'info')
    return redirect(url_for('tasks.view_task', task_id=task.id))


@tasks_bp.route('/view_task/<int:task_id>')
def view_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        abort(404)

    can_edit = (current_user is not None) and (current_user.is_admin or task.author is not None and current_user.id == task.author.id)

    # Форма удаления (только если пользователь имеет право)
    delete_form = ConfirmForm() if can_edit else None

    return render_template(
        "tasks/view_task.html",
        task=task,
        can_edit=can_edit,
        delete_form=delete_form,
    )


@tasks_bp.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        abort(404)

    can_delete = (current_user is not None) and (current_user.is_admin or task.author is not None and current_user.id == task.author.id)

    if not can_delete:
        abort(403)

    form = ConfirmForm()
    if not form.validate_on_submit():
        flash("Неверный запрос при удалении.", "warning")
        return redirect(url_for("tasks.view_task", task_id=task.id))

    db.session.delete(task)
    db.session.commit()

    flash("Задача удалена.", "success")
    return redirect(url_for("tasks.tasks"))


@tasks_bp.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    can_edit = (current_user is not None) and (current_user.is_admin or task.author is not None and current_user.id == task.author.id)

    if not can_edit:
        abort(403)

    form = NewTaskForm()

    if request.method == 'GET':
        form.number.data = task.number
        form.statement_html.data = task.statement_html
        form.answer.data = task.answer
        return render_template('tasks/edit_task.html', form=form, task=task, delete_form=ConfirmForm(), can_edit=True)

    # сохраняем изменения
    if form.validate_on_submit():
        # обновляем поля задачи
        task.number = form.number.data
        task.statement_html = form.statement_html.data
        task.answer = form.answer.data

        db.session.add(task)
        db.session.commit()

        # обработка новых загруженных файлов (если есть)
        files = form.attachments.data or []
        saved = []
        for fs in files:
            if not (fs and fs.filename):
                continue
            filename = secure_filename(fs.filename)
            data = fs.read()
            attachment = TaskAttachment(
                task_id=task.id,
                filename=filename,
                content_type=fs.mimetype,
                size=len(data),
                data=data,
            )
            db.session.add(attachment)
            saved.append(filename)

        if saved:
            db.session.commit()
            flash(f'Добавлены вложения: {", ".join(saved)}', 'success')

        flash('Задача обновлена.', 'success')
        return redirect(url_for('tasks.view_task', task_id=task.id))

    flash('Ошибка формы. Проверьте поля.', 'warning')
    return render_template('tasks/edit_task.html', form=form, task=task, delete_form=ConfirmForm(), can_edit=True)
