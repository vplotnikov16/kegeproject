import string

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import ValidationError, DataRequired

cyrillic_uppercase = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
cyrillic_lowercase = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
cyrillic_letters = cyrillic_uppercase + cyrillic_lowercase


def password_validator(form, field):
    text = ''
    if len(field.data) < 8:
        text = 'Пароль должен быть не короче 8 символов.'

    errors = []
    if not any(ch.islower() for ch in field.data):
        errors.append('строчной буквы')
    if not any(ch.isupper() for ch in field.data):
        errors.append('прописной буквы')
    if not any(ch in string.digits for ch in field.data):
        errors.append('цифры')
    if not any(ch in string.punctuation for ch in field.data):
        errors.append('спецсимвола')
    if errors:
        template = f'Не хватает {", ".join(errors)}.'
        text = text + ' ' + template if text else template
    if text:
        raise ValidationError(text)


def last_name_validator(form, field):
    additional_symbols = ' ' + '-'
    valid_chars = cyrillic_letters + additional_symbols
    if any(ch not in valid_chars for ch in field.data):
        raise ValidationError('Фамилия должна состоять только из символов русского алфавита')
    if len(field.data) > 40:
        raise ValidationError('Фамилия не может быть длиннее 40 символов')
    if field.data[0] not in cyrillic_uppercase:
        raise ValidationError('Фамилия должна начинаться с заглавной буквы')
    if any(field.data.startswith(ch) or field.data.endswith(ch) for ch in additional_symbols):
        raise ValidationError('Фамилия не может начинаться или заканчиваться пробелом или знаком "-"')
    if any(ch * 2 in field.data for ch in additional_symbols):
        raise ValidationError('Недопустимо использование подряд идущих символов пробела или знака "-"')


def first_name_validator(form, field):
    additional_symbols = ' ' + '-'
    valid_chars = cyrillic_letters + additional_symbols
    if any(ch not in valid_chars for ch in field.data):
        raise ValidationError('Имя должно состоять только из символов русского алфавита')
    if len(field.data) > 20:
        raise ValidationError('Имя не может быть длиннее 20 символов')
    if field.data[0] not in cyrillic_uppercase:
        raise ValidationError('Имя должно начинаться с заглавной буквы')
    if any(field.data.startswith(ch) or field.data.endswith(ch) for ch in additional_symbols):
        raise ValidationError('Имя не может начинаться или заканчиваться пробелом или знаком "-"')
    if any(ch * 2 in field.data for ch in additional_symbols):
        raise ValidationError('Недопустимо использование подряд идущих символов пробела или знака "-"')


def middle_name_validator(form, field):
    additional_symbols = ' ' + '-'
    valid_chars = cyrillic_letters + additional_symbols
    # Отсутствие отчества допустимо
    if not field.data:
        return
    if any(ch not in valid_chars for ch in field.data):
        raise ValidationError('Отчество должно состоять только из символов русского алфавита')
    if len(field.data) > 20:
        raise ValidationError('Отчество не может быть длиннее 20 символов')
    if field.data[0] not in cyrillic_uppercase:
        raise ValidationError('Отчество должно начинаться с заглавной буквы')
    if any(field.data.startswith(ch) or field.data.endswith(ch) for ch in additional_symbols):
        raise ValidationError('Отчество не может начинаться или заканчиваться пробелом или знаком "-"')
    if any(ch * 2 in field.data for ch in additional_symbols):
        raise ValidationError('Недопустимо использование подряд идущих символов пробела или знака "-"')


class RegisterForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired(), last_name_validator])
    first_name = StringField('Имя', validators=[DataRequired(), first_name_validator])
    middle_name = StringField('Отчество', validators=[middle_name_validator])
    password = PasswordField('Password', validators=[DataRequired(), password_validator])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
