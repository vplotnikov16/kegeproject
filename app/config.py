import os
from enum import StrEnum

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class EnvEnum(StrEnum):
    debug = 'DEBUG'
    host = 'HOST'
    port = 'PORT'
    secret_key = 'SECRET_KEY'
    sqlalchemy_database_uri = 'SQLALCHEMY_DATABASE_URI'
    sqlalchemy_track_modifications = 'SQLALCHEMY_TRACK_MODIFICATIONS'

    @property
    def type(self):
        return {
            EnvEnum.debug: bool,
            EnvEnum.host: str,
            EnvEnum.port: int,
            EnvEnum.secret_key: str,
            EnvEnum.sqlalchemy_database_uri: str,
            EnvEnum.sqlalchemy_track_modifications: bool,
        }[self]

    @property
    def default_str(self):
        db_path = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
        return {
            EnvEnum.debug: 'False',
            EnvEnum.host: '0.0.0.0',
            EnvEnum.port: '5000',
            EnvEnum.secret_key: 'secret_key',
            EnvEnum.sqlalchemy_database_uri: db_path,
            EnvEnum.sqlalchemy_track_modifications: 'False'
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
    DEBUG = parse_env_var(EnvEnum.debug)
    HOST = parse_env_var(EnvEnum.host)
    PORT = parse_env_var(EnvEnum.port)
    SECRET_KEY = parse_env_var(EnvEnum.secret_key)
    SQLALCHEMY_DATABASE_URI = parse_env_var(EnvEnum.sqlalchemy_database_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = parse_env_var(EnvEnum.sqlalchemy_track_modifications)
