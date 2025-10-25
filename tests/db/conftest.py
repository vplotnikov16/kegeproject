import os
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.config import Config
from app.extensions import db as _db


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_DATABASE_URI определяется позже в фикстуре


@pytest.fixture(scope='session')
def project_root():
    return Path(__file__).resolve().parents[2]  # repo root


@pytest.fixture(scope='session')
def app(project_root, tmp_path_factory):
    """
    Создает приложение и конфигурацию к нему с временной БД
    """
    db_dir = tmp_path_factory.mktemp('db')
    db_file = db_dir / 'test_app.db'
    test_db_uri = f"sqlite:///{db_file}"

    class LocalTestConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = test_db_uri

    app = create_app(config_class=LocalTestConfig)

    # ensure migrations/env.py / alembic can see the app if it reads current_app
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db(app):
    """
    Создание чистой структуры (схемы) базы данных между тестами
    """
    _db.create_all()

    # форсируем включение обеспечения FK для тестов каскадных операций
    try:
        _db.session.execute(text("PRAGMA foreign_keys=ON"))
        _db.session.commit()
    except SQLAlchemyError:
        _db.session.rollback()

    yield _db

    _db.session.remove()
    _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


@pytest.fixture
def inspector(db):
    return inspect(_db.engine)
