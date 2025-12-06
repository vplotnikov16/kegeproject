import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class EnvEnum(str, Enum):
    DEBUG = 'DEBUG'
    HOST = 'HOST'
    PORT = 'PORT'
    SECRET_KEY = 'SECRET_KEY'
    SQLALCHEMY_DATABASE_URI = 'SQLALCHEMY_DATABASE_URI'
    SQLALCHEMY_TRACK_MODIFICATIONS = 'SQLALCHEMY_TRACK_MODIFICATIONS'
    MAX_CONTENT_LENGTH = 'MAX_CONTENT_LENGTH'
    FLASK_APP = 'FLASK_APP'
    PYTHONUNBUFFERED = 'PYTHONUNBUFFERED'

    @property
    def type(self):
        return {
            EnvEnum.DEBUG: bool,
            EnvEnum.HOST: str,
            EnvEnum.PORT: int,
            EnvEnum.SECRET_KEY: str,
            EnvEnum.SQLALCHEMY_DATABASE_URI: str,
            EnvEnum.SQLALCHEMY_TRACK_MODIFICATIONS: bool,
            EnvEnum.MAX_CONTENT_LENGTH: int,
            EnvEnum.FLASK_APP: str,
            EnvEnum.PYTHONUNBUFFERED: bool,
        }[self]

    @property
    def default_str(self):
        db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
        return {
            EnvEnum.DEBUG: 'False',
            EnvEnum.HOST: '0.0.0.0',
            EnvEnum.PORT: '5000',
            EnvEnum.SECRET_KEY: 'secret_key',
            EnvEnum.SQLALCHEMY_DATABASE_URI: db_path,
            EnvEnum.SQLALCHEMY_TRACK_MODIFICATIONS: 'False',
            EnvEnum.MAX_CONTENT_LENGTH: str(6 * 1024 * 1024),
            EnvEnum.FLASK_APP: 'app',
            EnvEnum.PYTHONUNBUFFERED: '1',
        }[self]


def parse_env_var(var: EnvEnum):
    res = os.getenv(var, var.default_str)
    if var.type is int:
        return int(res)
    elif var.type is str:
        return res
    elif var.type is bool:
        return res.lower() in ('1', 'on', 'true', 'yes')
    else:
        raise NotImplementedError


class Config:
    DEBUG = parse_env_var(EnvEnum.DEBUG)
    HOST = parse_env_var(EnvEnum.HOST)
    PORT = parse_env_var(EnvEnum.PORT)
    SECRET_KEY = parse_env_var(EnvEnum.SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = parse_env_var(EnvEnum.SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = parse_env_var(EnvEnum.SQLALCHEMY_TRACK_MODIFICATIONS)
    MAX_CONTENT_LENGTH = parse_env_var(EnvEnum.MAX_CONTENT_LENGTH)
    FLASK_APP = parse_env_var(EnvEnum.FLASK_APP)
    PYTHONUNBUFFERED = parse_env_var(EnvEnum.PYTHONUNBUFFERED)
