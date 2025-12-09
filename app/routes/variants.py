from typing import List

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user

from app import db
from app.forms.variants import VariantGenerationForm
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

    return f'ура, я увидел новый варик (дебаг): {selected}'


@variants_bp.route('/new_variant')
def new_variant():
    return ''
