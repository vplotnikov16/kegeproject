from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import StringField, IntegerField, SubmitField, TextAreaField


class NewTaskForm(FlaskForm):
    number = IntegerField('Номер задачи в КИМ')
    statement_html = TextAreaField('Текст задачи')
    answer = StringField('Ответ на задачу')
    attachments = MultipleFileField("Файлы к задаче")
    submit = SubmitField('Зарегистрироваться')

