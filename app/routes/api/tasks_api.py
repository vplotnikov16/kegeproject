from flask import Blueprint, request, jsonify

from app.services.task_services import TaskService

tasks_api_bp = Blueprint("api_tasks", __name__)


@tasks_api_bp.route("/by_numbers", methods=["POST"])
def by_numbers():
    """
    На вход отправляют номера КИМ, на выходе выдаем все задачи этих номеров КИМ
    """
    payload = request.get_json(silent=True) or {}
    numbers = payload.get("numbers") or []

    try:
        nums = [int(n) for n in numbers]
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Некорректный запрос"), 400

    tasks = TaskService.get_by_numbers(nums)
    return jsonify(ok=True, tasks=[t.as_dict for t in tasks]), 200


@tasks_api_bp.route("/by_ids", methods=["POST"])
def by_ids():
    """
    На вход отправляют ID задач, на выходе отправляем инфо об этих задачах
    """
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids") or []
    try:
        ids = [int(id) for id in ids]
    except (TypeError, ValueError):
        return jsonify(ok=False, error="Некорректный запрос"), 400

    tasks = TaskService.get_by_ids(ids)
    return jsonify(ok=True, tasks=[t.as_dict for t in tasks]), 200
