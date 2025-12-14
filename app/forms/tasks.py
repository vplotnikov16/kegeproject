from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import StringField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class NewTaskForm(FlaskForm):
    number = IntegerField('Номер задачи в КИМ', validators=[DataRequired("Укажите номер КИМ этой задачи")])
    statement_html = TextAreaField('Текст задачи', validators=[DataRequired("У задачи должно быть условие")])
    answer = StringField('Ответ на задачу', validators=[DataRequired("У задачи должен быть ответ")])
    attachments = MultipleFileField("Файлы к задаче")
    submit = SubmitField('Добавить задачу')
