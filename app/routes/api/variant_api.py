from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Variant

variants_api_bp = Blueprint('variants_api', __name__)


@variants_api_bp.delete('/<int:variant_id>')
@login_required
def delete_variant(variant_id):
    variant = Variant.query.get_or_404(variant_id)

    can_delete = current_user.is_admin or (variant.author_id == current_user.id)

    if not can_delete:
        return jsonify(ok=False, error='Нет прав'), 403

    db.session.delete(variant)
    db.session.commit()

    return jsonify(ok=True), 200
