from flask import Blueprint, abort, render_template, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.models import User, UserAvatar
from app.forms.users import UserEditForm
from app.utils.date_utils import utcnow

users_bp = Blueprint('users', __name__)


@users_bp.route('/view_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def view_user(user_id):
    if current_user.id == user_id:
        return redirect(url_for('profile.profile'))

    user = User.query.get_or_404(user_id)

    is_admin = current_user.is_admin
    form = None

    if is_admin:
        form = UserEditForm(obj=user)

        if form.validate_on_submit():
            if form.username.data:
                user.username = form.username.data
            if form.first_name.data:
                user.first_name = form.first_name.data
            if form.last_name.data:
                user.last_name = form.last_name.data
            if form.middle_name.data:
                user.middle_name = form.middle_name.data

            fs = form.avatar_file.data
            if fs and fs.filename:
                data = fs.read()
                ua = UserAvatar.query.filter_by(user_id=user_id).first()
                if not ua:
                    ua = UserAvatar(user_id=user.id)
                ua.filename = secure_filename(fs.filename)
                ua.content_type = fs.mimetype
                ua.size = len(data)
                ua.data = data
                ua.uploaded = utcnow()
                db.session.add(ua)
            db.session.commit()

    return render_template(
        'users/view_user.html',
        user=user,
        is_admin=is_admin,
        form=form,
        my_tasks=user.tasks[-5:],
        my_variants=user.variants[-5:],
    )
