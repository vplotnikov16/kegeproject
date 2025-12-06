from io import BytesIO

from flask import Blueprint, render_template, request, redirect, url_for, abort, send_file
from flask_login import login_user, login_required, logout_user, current_user

from app.forms.auth import RegisterForm, LoginForm
from app.models import User, UserAvatar
from app.extensions import db

pages_bp = Blueprint("pages", __name__)


@pages_bp.route('', methods=['GET'])
def index():
    return render_template("index.html")


@pages_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template('login.html', form=form)
    user = User.query.filter_by(username=form.username.data).first()
    if user and user.check_password(form.password.data):
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('pages.index'))
    else:
        error = "Неправильное имя пользователя и/или пароль"
        return render_template("login.html", error=error, form=form)


@pages_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('pages.index'))

    form = RegisterForm()

    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        middle_name = form.middle_name.data or None
        username = User.generate_username(first_name, last_name, middle_name)

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('pages.index'))

    return render_template('register.html', form=form)


@pages_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('pages.index'))


@pages_bp.get("/avatar/<int:user_id>")
def get_avatar(user_id):
    avatar = UserAvatar.query.get(user_id)
    if not avatar:
        abort(404)
    return send_file(
        BytesIO(avatar.data),
        mimetype=avatar.mime_type,
        download_name=f"avatar_{user_id}.png"
    )
