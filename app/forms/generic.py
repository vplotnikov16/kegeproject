from flask_wtf import FlaskForm
from wtforms import SubmitField


class ConfirmForm(FlaskForm):
    submit = SubmitField("Подтвердить")
