from flask import Blueprint, render_template
from flask_login import login_required, current_user

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('')
@login_required
def profile():
    return render_template('profile/profile.html', user=current_user)


@profile_bp.route('/stats')
@login_required
def stats():
    return render_template('profile/stats.html', user=current_user)


@profile_bp.route('/my_tasks')
@login_required
def my_tasks():
    return render_template('profile/my_tasks.html', user=current_user)


@profile_bp.route('/my_variants')
@login_required
def my_variants():
    return render_template('profile/my_variants.html', user=current_user)
