from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user

from app.models.user import User
from app.extensions import db

pages_bp = Blueprint("pages", __name__)


@pages_bp.route('', methods=['GET'])
def index():
    return render_template("index.html")


@pages_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("pages.index"))
        return render_template("login.html", error="Неправильное имя пользователя и/или пароль")

    return render_template("login.html")


@pages_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('pages.index'))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Пользователь с таким именем пользователя уже существует в системе")

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("pages.index"))

    return render_template("register.html")


@pages_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('pages.index'))


@pages_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@pages_bp.route('/stats')
@login_required
def stats():
    return render_template('stats.html', user=current_user)