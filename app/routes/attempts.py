from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import login_required, current_user

from app.models import Attempt, VariantTask
from app.services.attempt_service import AttemptService

attempts_bp = Blueprint('attempts', __name__)


@attempts_bp.route('/<int:attempt_id>', methods=['GET'])
@login_required
def attempt(attempt_id: int):
    attempt_obj = Attempt.query.get(attempt_id)
    if not attempt_obj:
        abort(404)
    elif attempt_obj.user_id != current_user.id:
        abort(403)

    variant = attempt_obj.variant
    variant_tasks = VariantTask.query.filter_by(variant_id=variant.id).order_by(VariantTask.order).all()
    kwargs = {
        'attempt': attempt_obj,
        'variant': variant,
        'variant_tasks': variant_tasks,
        'total_tasks': len(variant_tasks),
    }
    return render_template('attempts/attempt.html', **kwargs)


@attempts_bp.route('/<int:attempt_id>/data', methods=['GET'])
@login_required
def get_attempt_data(attempt_id: int):
    data = AttemptService.get_attempt_data(attempt_id, current_user.id)

    if not data:
        return jsonify(ok=False, error='Попытка не найдена'), 404

    return jsonify(data)


@attempts_bp.route('/<int:attempt_id>/save-answer', methods=['POST'])
@login_required
def save_answer(attempt_id: int):
    attempt = Attempt.query.get(attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        return jsonify(ok=False, error='Попытка не найдена'), 404

    if attempt.finished_at:
        return jsonify(ok=False, error='Попытка уже завершена'), 403

    data = request.get_json()
    variant_task_id = data.get('variant_task_id')
    answer_text = data.get('answer_text')

    if not variant_task_id:
        return jsonify(ok=False, error='Не удалось найти задачу'), 400

    vt = VariantTask.query.get(variant_task_id)
    if not vt or vt.variant_id != attempt.variant_id:
        return jsonify({'error': 'Invalid task'}), 400

    answer = AttemptService.save_answer(
        attempt_id,
        variant_task_id,
        answer_text,
        current_user.id
    )

    if not answer:
        return jsonify(ok=False, error='Не удалось сохранить ответ'), 400

    return jsonify(ok=True, variant_task_id=variant_task_id, updated_at=answer.updated_at.strftime('%d.%m.%Y %H:%M:%S'))


@attempts_bp.route('/<int:attempt_id>/finish', methods=['POST'])
@login_required
def finish_attempt(attempt_id: int):
    attempt = Attempt.query.get(attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        return jsonify(ok=False, error='Попытка не найдена'), 404

    if attempt.finished_at:
        return jsonify(ok=False, error='Попытка уже завершена'), 400

    finished = AttemptService.finish_attempt(attempt_id, current_user.id)

    if not finished:
        return jsonify(ok=False, error='Не удалось завершить попытку'), 400

    return jsonify(ok=True, finished_at=finished.finished_at.strftime('%d.%m.%Y %H:%M:%S'))


@attempts_bp.route('/<int:attempt_id>/results', methods=['GET'])
@login_required
def get_results(attempt_id: int):
    results = AttemptService.get_attempt_results(attempt_id, current_user.id)

    if not results:
        return jsonify(error='Результаты не найдены'), 404

    return jsonify(results)


@attempts_bp.route('/<int:attempt_id>/results-page', methods=['GET'])
@login_required
def results_page(attempt_id: int):
    attempt = Attempt.query.get(attempt_id)

    if not attempt:
        abort(404)
    elif attempt.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if not attempt.finished_at:
        return render_template('error.html', error_code=400, error_msg='Exam not finished'), 400

    return render_template('attempts/results.html', attempt=attempt, variant=attempt.variant)
