import os
from alembic import command, config as alembic_config
from pathlib import Path
from sqlalchemy import inspect

from app.extensions import db


def test_alembic_upgrade_head(app, project_root):
    """
    Запускаем `alembic upgrade head` через API alembic внутри контекста
    приложения и проверяем, что миграции применились (таблицы есть).
    Тест провалится, если миграции падают
    """
    alembic_ini = project_root / 'migrations' / "alembic.ini"
    assert alembic_ini.exists(), "alembic.ini не найден"

    cfg = alembic_config.Config(str(alembic_ini))
    migrations_dir = project_root / "migrations"
    cfg.set_main_option("script_location", str(migrations_dir))

    command.upgrade(cfg, "head")

    # быстрая проверка, что таблица есть после миграций
    insp = inspect(db.engine)
    tables = set(insp.get_table_names())
    assert "users" in tables and "tasks" in tables
