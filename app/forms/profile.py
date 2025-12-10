from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired


class AvatarUploadForm(FlaskForm):
    avatar_file = FileField('Аватар')
    submit = SubmitField('Загрузить')
