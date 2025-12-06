from flask import Blueprint, abort

from app.models import User

users_bp = Blueprint('users', __name__)


@users_bp.route('/<int:user_id>')
def view(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user.data:
        abort(404)

    return 'user view'
