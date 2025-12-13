from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import Optional, Length


class UserEditForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[Optional(), Length(max=120)])
    first_name = StringField('Имя', validators=[Optional(), Length(max=20)])
    last_name = StringField('Фамилия', validators=[Optional(), Length(max=40)])
    middle_name = StringField('Отчество', validators=[Optional(), Length(max=20)])
    avatar_file = FileField('Аватар')
    submit = SubmitField('Сохранить')
