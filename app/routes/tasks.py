from flask import Blueprint, render_template
from flask_login import login_required

from app.forms.tasks import NewTaskForm
from app.models import Task
from app.extensions import db

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route('/')
def tasks():
    return render_template('tasks/tasks.html')


@tasks_bp.route('/new_task', methods=['GET', 'POST'])
@login_required
def new_task():
    form = NewTaskForm()

    if form.validate_on_submit():
        number = form.number.data
        statement_html = form.statement_html.data
        answer = form.answer.data
        files = form.attachments.data
        print(files)

        task = Task(
            number=number,
            statement_html=statement_html,
            answer=answer,
            source='kegeproject'
        )
        db.session.add(task)
        db.session.commit()

    return render_template('tasks/new_task.html', form=form)
