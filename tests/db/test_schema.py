from sqlalchemy import text

EXPECTED_TABLES = {
    'users', 'roles', 'user_roles',
    'tasks', 'task_attachments',
    'variants', 'variant_tasks',
    'attempts', 'attempt_answers', 'user_avatars'
}


def test_tables_exist(inspector):
    tbls = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(tbls), f"Не хватает таблиц: {EXPECTED_TABLES - tbls}"


def test_foreign_keys_present(inspector):
    # проверяем, есть ли у таблиц FK
    fk_map = {t: inspector.get_foreign_keys(t) for t in inspector.get_table_names()}

    # user_roles должна ссылаться на users и roles
    ur_fks = {fk['referred_table'] for fk in fk_map.get('user_roles', [])}
    assert 'users' in ur_fks and 'roles' in ur_fks

    # task_attachments -> tasks
    ta_fks = {fk['referred_table'] for fk in fk_map.get('task_attachments', [])}
    assert 'tasks' in ta_fks

    # variant_tasks -> variants, tasks
    vt_fks = {fk['referred_table'] for fk in fk_map.get('variant_tasks', [])}
    assert 'variants' in vt_fks and 'tasks' in vt_fks

    # attempt_answers -> attempts, tasks
    aa_fks = {fk['referred_table'] for fk in fk_map.get('attempt_answers', [])}
    assert 'attempts' in aa_fks and 'tasks' in aa_fks
