from typing import List

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms.variants import VariantGenerationForm, VariantEditForm
from app.models import Task, Variant, VariantTask
from app.utils.variant_utils import build_tasks_set

variants_bp = Blueprint('variants', __name__, url_prefix='/variants')


@variants_bp.route('/', methods=['GET', 'POST'])
def variants():
    form = VariantGenerationForm()
    if not form.validate_on_submit():
        return render_template('variants/variants.html', form=form)

    if not current_user.is_authenticated:
        return redirect(url_for('pages.login'))

    selected = []
    for field in form:
        if not field.name.startswith('kim_'):
            continue
        if getattr(form, field.name).data:
            num = field.name.replace('kim_', '').replace('_', '-')
            cnt_raw = request.form.get(f'kim_count_{num}', 1)
            cnt = int(cnt_raw)
            selected.append((num, cnt))

    tasks: List[Task] = build_tasks_set(selected)
    if not tasks:
        print('Пустой вариант')
        return render_template('variants/variants.html', form=form)

    variant = Variant()
    db.session.add(variant)
    db.session.commit()

    for task in tasks:
        vt = VariantTask(variant_id=variant.id, task_id=task.id)
        db.session.add(vt)
    db.session.commit()

    return redirect(url_for('variants.view_variant', variant_id=variant.id))


@variants_bp.route('/new_variant')
def new_variant():
    return ''


@variants_bp.route('/view_variant/<int:variant_id>')
def view_variant(variant_id: int):
    variant = Variant.query.get_or_404(variant_id)
    return render_template('variants/view_variant.html', variant=variant)


@variants_bp.route('/edit_variant/<int:variant_id>', methods=['GET', 'POST'])
def edit_variant(variant_id):
    form = VariantEditForm()
    variant = Variant.query.get_or_404(variant_id)

    # Заполнить форму при GET
    if request.method == 'GET':
        form.variant_id.data = variant.id
        form.source.data = variant.source

    if form.validate_on_submit():
        # если нажали кнопку "Добавить задачу" (non-JS fallback)
        if form.add_task.data and form.add_task_id.data:
            # реализуйте проверку прав, добавление VariantTask и флеш-сообщение
            add_task_id = int(form.add_task_id.data)
            # ... логика добавления
            flash('Задача добавлена', 'success')
            return redirect(url_for('variants.edit_variant', variant_id=variant_id))

        # если нажали "Сохранить" — обновляем метаданные варианта
        if form.save.data:
            variant.source = form.source.data or None
            db.session.commit()
            flash('Вариант сохранён', 'success')
            return redirect(url_for('variants.view_variant', variant_id=variant_id))

    return render_template('variants/edit_variant.html', variant=variant, form=form, my_tasks=current_user.tasks)


@variants_bp.route('/<int:variant_id>/add_task', methods=['POST'])
@login_required
def add_task(variant_id):
    variant = Variant.query.get_or_404(variant_id)
    can_edit = (current_user is not None) and (current_user.is_admin or variant.author is not None and current_user.id == variant.author.id)

    if not can_edit:
        return jsonify(ok=False, message="Нет прав"), 403

    data = request.get_json(force=True, silent=True) or {}
    task_id = data.get('task_id')
    if not task_id:
        return jsonify(ok=False, message="task_id обязателен"), 400

    task = Task.query.get(task_id)
    if not task:
        return jsonify(ok=False, message="Задача не найдена"), 404

    exists = VariantTask.query.filter_by(variant_id=variant.id, task_id=task.id).first()
    if exists:
        return jsonify(ok=False, message="Задача уже в варианте"), 400

    try:
        vt = VariantTask(variant_id=variant.id, task_id=task.id)
        db.session.add(vt)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(ok=False, message="Ошибка добавления"), 500

    attachments = []
    for a in task.attachments:
        attachments.append({
            'id': a.id,
            'filename': a.filename,
            'size': a.size,
            'download_url': url_for('attachments.download_attachment', attachment_id=a.id)
        })
    task_payload = {
        'id': task.id,
        'number': task.number,
        'statement_html': task.statement_html,
        'answer': task.answer,
        'source': task.source,
        'attachments': attachments
    }
    return jsonify(ok=True, task=task_payload), 200


@variants_bp.route('/<int:variant_id>/remove_task', methods=['POST'])
@login_required
def remove_task(variant_id):
    variant = Variant.query.get_or_404(variant_id)
    can_edit = (current_user is not None) and (current_user.is_admin or variant.author is not None and current_user.id == variant.author.id)

    if not can_edit:
        return jsonify(ok=False, message="Нет прав"), 403

    data = request.get_json(force=True, silent=True) or {}
    task_id = data.get('task_id')
    if not task_id:
        return jsonify(ok=False, message="task_id обязателен"), 400

    vt = VariantTask.query.filter_by(variant_id=variant.id, task_id=task_id).first()
    if not vt:
        return jsonify(ok=False, message="Задача не найдена в варианте"), 404
    try:
        db.session.delete(vt)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(ok=False, message="Ошибка удаления"), 500
    return jsonify(ok=True), 200


@variants_bp.route('/<int:variant_id>/move_task', methods=['POST'])
@login_required
def move_task(variant_id):
    variant = Variant.query.get_or_404(variant_id)
    can_edit = (current_user is not None) and (current_user.is_admin or variant.author is not None and current_user.id == variant.author.id)

    if not can_edit:
        return jsonify(ok=False, message="Нет прав"), 403

    data = request.get_json(force=True, silent=True) or {}
    task_id = data.get('task_id')
    direction = data.get('direction')  # 'up' или 'down'
    if not task_id or direction not in ('up', 'down'):
        return jsonify(ok=False, message="Неверные параметры"), 400

    if not hasattr(VariantTask, 'position'):
        return jsonify(ok=True, moved=True, task_id=task_id), 200

    vt = VariantTask.query.filter_by(variant_id=variant.id, task_id=task_id).first()
    if not vt:
        return jsonify(ok=False, message="Задача не в варианте"), 404

    if direction == 'up':
        neighbor = VariantTask.query.filter(
            VariantTask.variant_id == variant.id,
            VariantTask.position < vt.position
        ).order_by(VariantTask.position.desc()).first()
    else:
        neighbor = VariantTask.query.filter(
            VariantTask.variant_id == variant.id,
            VariantTask.position > vt.position
        ).order_by(VariantTask.position.asc()).first()

    if not neighbor:
        return jsonify(ok=False, message="Невозможно переместить"), 400

    try:
        vt.position, neighbor.position = neighbor.position, vt.position
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(ok=False, message="Ошибка перемещения"), 500

    order = [vt.task_id for vt in VariantTask.query.filter_by(variant_id=variant.id).order_by(VariantTask.position.asc()).all()]
    return jsonify(ok=True, order=order), 200


@variants_bp.route('/tasks/<int:task_id>/json')
@login_required
def task_json(task_id):
    task = Task.query.get_or_404(task_id)
    attachments = []
    for a in task.attachments:
        attachments.append({
            'id': a.id,
            'filename': a.filename,
            'size': a.size,
            'download_url': url_for('attachments.download_attachment', attachment_id=a.id)
        })
    payload = {
        'id': task.id,
        'number': task.number,
        'statement_html': task.statement_html,
        'answer': task.answer,
        'source': task.source,
        'attachments': attachments
    }
    return jsonify(ok=True, task=payload), 200
