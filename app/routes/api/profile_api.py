from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app import db

profile_api_bp = Blueprint("profile_api", __name__)


@profile_api_bp.post("/delete_avatar")
@login_required
def delete_avatar():
    ua = current_user.avatar
    if not ua:
        return jsonify(ok=False, error="Аватар отсутствует"), 404

    try:
        db.session.delete(ua)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(ok=False, error="Ошибка удаления"), 500

    return jsonify(ok=True), 200
