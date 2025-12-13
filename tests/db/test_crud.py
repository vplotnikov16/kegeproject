from app.extensions import db as _db
from app.models import User, Role, UserRole, Task, TaskAttachment, Variant, VariantTask, Attempt, AttemptAnswer


def test_user_role_cascade(db):
    u = User(username='u1', first_name='A', last_name='B', password_hash='h')
    r = Role(name='tester')
    _db.session.add_all([u, r])
    _db.session.commit()

    ur = UserRole(user_id=u.id, role_id=r.id)
    _db.session.add(ur)
    _db.session.commit()

    assert _db.session.query(UserRole).filter_by(user_id=u.id, role_id=r.id).one_or_none() is not None

    # Если удалили роль, все ассоциации с ней должны быть тоже удалены
    _db.session.delete(r)
    _db.session.commit()

    assert _db.session.query(UserRole).filter_by(user_id=u.id).count() == 0
    # но при этом пользователь не должен быть удален, если удалили роль
    assert _db.session.query(User).filter_by(id=u.id).one_or_none() is not None


def test_task_attachment_and_variant_task_cascade(db):
    t = Task(number=1, statement_html='<p>x</p>', answer='42')
    _db.session.add(t)
    _db.session.commit()

    ta = TaskAttachment(task_id=t.id, filename='x.png', content_type='image/png', data=b'')
    _db.session.add(ta)

    v = Variant()
    _db.session.add(v)
    _db.session.commit()

    vt = VariantTask(variant_id=v.id, task_id=t.id)
    _db.session.add(vt)
    _db.session.commit()

    assert _db.session.query(TaskAttachment).filter_by(task_id=t.id).count() == 1
    assert _db.session.query(VariantTask).filter_by(task_id=t.id).count() == 1

    # если удалили задачу, должны удалиться и вложения, и записи, куда задача была включена
    _db.session.delete(t)
    _db.session.commit()

    assert _db.session.query(TaskAttachment).filter_by(task_id=t.id).count() == 0
    assert _db.session.query(VariantTask).filter_by(task_id=t.id).count() == 0


def test_attempt_and_answers_cascade(db):
    u = User(username='user_for_attempt', first_name='A', last_name='B', password_hash='h')
    v = Variant()
    t = Task(number=10, statement_html='xx', answer='a')
    _db.session.add_all([u, v, t])
    _db.session.commit()

    vt = VariantTask(variant_id=v.id, task_id=t.id)
    _db.session.add(vt)
    _db.session.commit()

    att = Attempt(user_id=u.id, variant_id=v.id)
    _db.session.add(att)
    _db.session.commit()

    aa = AttemptAnswer(attempt_id=att.id, variant_task_id=vt.id, answer_text='x', is_correct=False)
    _db.session.add(aa)
    _db.session.commit()

    assert AttemptAnswer.query.filter_by(attempt_id=att.id).count() == 1

    attempt_id = att.id
    _db.session.delete(att)
    _db.session.commit()

    assert Attempt.query.filter_by(id=attempt_id).first() is None
    assert AttemptAnswer.query.filter_by(attempt_id=attempt_id).count() == 0


def test_user_crud(db):
    """
    Проверка базовых CRUD-операций для пользователя
    """
    user = User(username='crud_user', first_name='Ivan', last_name='Petrov', password_hash='hash')
    _db.session.add(user)
    _db.session.commit()

    # CREATE + READ
    found = User.query.filter_by(username='crud_user').first()
    assert found is not None
    assert found.first_name == 'Ivan'

    # UPDATE
    found.first_name = 'Sergey'
    _db.session.commit()

    updated = User.query.filter_by(username='crud_user').first()
    assert updated.first_name == 'Sergey'

    # DELETE
    _db.session.delete(updated)
    _db.session.commit()
    assert User.query.filter_by(username='crud_user').first() is None


def test_role_crud_and_user_assignment(db):
    """
    Создание роли и привязка к пользователю через user_roles
    """
    role = Role(name='admin_test')
    user = User(username='user_admin', first_name='A', last_name='B', password_hash='h')
    _db.session.add_all([role, user])
    _db.session.commit()

    user.roles.append(role)
    _db.session.commit()

    u = User.query.filter_by(username='user_admin').first()
    assert len(u.roles) == 1
    assert u.roles[0].name == 'admin_test'

    # UPDATE
    role.name = 'superadmin'
    _db.session.commit()
    assert Role.query.filter_by(id=role.id).first().name == 'superadmin'

    # DELETE
    _db.session.delete(role)
    _db.session.commit()
    assert Role.query.filter_by(name='superadmin').first() is None
    # связь должна быть очищена, но пользователь остаться
    assert User.query.filter_by(username='user_admin').first() is not None


def test_task_and_variant_crud(db):
    """
    CRUD для задач и вариантов
    """
    task = Task(number=3, statement_html='<b>3</b>', answer='123')
    variant = Variant(source='demo')
    _db.session.add_all([task, variant])
    _db.session.commit()

    # CREATE + связь variant-task
    vt = VariantTask(variant_id=variant.id, task_id=task.id)
    _db.session.add(vt)
    _db.session.commit()

    found_variant = _db.session.get(Variant, variant.id)
    assert len(found_variant.tasks) == 1

    # UPDATE
    task.answer = '999'
    _db.session.commit()
    assert _db.session.get(Task, task.id).answer == '999'

    # DELETE
    _db.session.delete(task)
    _db.session.commit()
    assert _db.session.get(Task, task.id) is None
    assert VariantTask.query.filter_by(variant_id=variant.id).count() == 0


def test_attempt_crud(db):
    """
    CRUD для попытки и ответов
    """
    user = User(username='test_user_crud', first_name='A', last_name='B', password_hash='h')
    variant = Variant(source='demo_variant')
    task = Task(number=5, statement_html='...', answer='yes')
    _db.session.add_all([user, variant, task])
    _db.session.commit()

    variant_task = VariantTask(variant_id=variant.id, task_id=task.id)
    _db.session.add(variant_task)
    _db.session.commit()

    attempt = Attempt(user_id=user.id, variant_id=variant.id)
    _db.session.add(attempt)
    _db.session.commit()
    assert Attempt.query.filter_by(user_id=user.id).first() is not None

    answer = AttemptAnswer(
        attempt_id=attempt.id,
        variant_task_id=variant_task.id,
        answer_text='no',
        is_correct=False
    )
    _db.session.add(answer)
    _db.session.commit()
    assert AttemptAnswer.query.filter_by(attempt_id=attempt.id).first() is not None

    # READ
    read_answer = AttemptAnswer.query.filter_by(attempt_id=attempt.id).first()
    assert read_answer.answer_text == 'no'
    assert read_answer.is_correct == False

    assert read_answer.variant_task_id == variant_task.id
    assert read_answer.variant_task.task == task

    # UPDATE
    answer.answer_text = 'yes'
    answer.is_correct = True
    _db.session.commit()
    updated_answer = AttemptAnswer.query.filter_by(attempt_id=attempt.id).first()
    assert updated_answer.answer_text == 'yes'
    assert updated_answer.is_correct == True

    # DELETE
    _db.session.delete(answer)
    _db.session.commit()
    assert AttemptAnswer.query.filter_by(attempt_id=attempt.id).first() is None
