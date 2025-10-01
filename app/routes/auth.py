from flask import Blueprint, request, jsonify

from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

def _is_err_400(data: dict) -> bool:
    """
    Проверка на некорректный запрос
    """
    # Случаи для ошибки 400
    is_err_400 = False
    # Случай 1: пустой словарь
    is_err_400 |= not data
    # Случай 2: отсутствующий логин
    is_err_400 |= not data.get('login')
    # Случай 3: отсутствующий пароль
    is_err_400 |= not data.get('password')
    return is_err_400

def _is_err_401(data: dict, user: User) -> bool:
    """
    Проверка на ошибку идентификации или аутентификации пользователя
    """
    # Случаи для ошибки 401
    is_err_401 = False
    # Случай 1: пользователя с указанным login нет в БД
    is_err_401 |= not user
    # Случай 2: неверный пароль
    is_err_401 |= not user.check_password(data['password'])
    return is_err_401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Проверки на ошибку с кодом 400
    if _is_err_400(data):
        return jsonify({'error': 'Не указано имя пользователя и/или пароль'}), 400
    if User.query.filter_by(login=data['login']).first():
        return jsonify({'error': 'Пользователь с таким именем пользователя уже существует в системе'}), 400

    user = User(login=data['login'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Успешно'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Проверка на ошибку с кодом 400
    if _is_err_400(data):
        return jsonify({'error': 'Не указано имя пользователя и/или пароль'}), 400

    user = User.query.filter_by(login=data['login']).first()
    # Проверка на ошибку с кодом 401
    if _is_err_401(data, user):
        return jsonify({'error': 'Неправильное имя пользователя и/или пароль'}), 401

    return jsonify({'message': 'Успешно'}), 200
