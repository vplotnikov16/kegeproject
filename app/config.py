import os
from enum import StrEnum

from dotenv import load_dotenv

load_dotenv()


class EnvEnum(StrEnum):
    debug = 'DEBUG'
    host = 'HOST'
    port = 'PORT'
    secret_key = 'SECRET_KEY'

    @property
    def type(self):
        return {
            EnvEnum.debug: bool,
            EnvEnum.host: str,
            EnvEnum.port: int,
            EnvEnum.secret_key: str
        }[self]

    @property
    def default_str(self):
        return {
            EnvEnum.debug: 'False',
            EnvEnum.host: '0.0.0.0',
            EnvEnum.port: '5000',
            EnvEnum.secret_key: 'secret_key'
        }


def parse_env_var(var: EnvEnum):
    res = os.getenv(var, var.default_str)
    if var.type is int:
        return int(res)
    elif var.type is str:
        return res
    elif var.type is bool:
        return res.lower() in ('1', 'on', 'true')
    else:
        raise NotImplemented


class Config:
    DEBUG = parse_env_var(EnvEnum.debug)
    HOST = parse_env_var(EnvEnum.host)
    PORT = parse_env_var(EnvEnum.port)
    SECRET_KEY = parse_env_var(EnvEnum.secret_key)
