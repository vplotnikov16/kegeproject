
import random
from datetime import timedelta
from faker import Faker

from app.utils.date_utils import utcnow
from run_in_venv import get_project_root


NUM_USERS = 100
NUM_TASKS_POOL = 400
NUM_VARIANTS = 150
VARIANT_PROBABILITY = 0.7  # вероятность у пользователя быть потенциальным автором
MIDDLE_NAME_PROBABILITY = 0.7
SOURCE_PROBABILITY = 0.6

SINGLE_ANSWER_PROB = 0.8  # вероятность, что для одиночного поля ответ - число, иначе слово


def _make_answer_for_number(slot_num: int, fake: Faker):

    def scalar():
        if random.random() < SINGLE_ANSWER_PROB:
            return str(random.randint(1, 100))
        else:
            return fake.word().upper()

    def one_row_n_cells(n):
        cells = [f"r1c{i+1}_{random.randint(1,999)}" for i in range(n)]
        return ",".join(cells)

    if 1 <= slot_num <= 16 or 22 <= slot_num <= 24:
        return scalar()
    if slot_num in (17, 18, 26):
        return one_row_n_cells(2)
    if slot_num == 19:
        return one_row_n_cells(3)
    if slot_num == 25:
        rows = []
        for r in range(10):
            cells = [f"r{r+1}c1_{random.randint(1,999)}", f"r{r+1}c2_{random.randint(1,999)}"]
            rows.append(",".join(cells))
        return ";".join(rows)
    if slot_num == 27:
        rows = []
        for r in range(2):
            cells = [f"r{r+1}c1_{random.randint(1,999)}", f"r{r+1}c2_{random.randint(1,999)}"]
            rows.append(",".join(cells))
        return ";".join(rows)

    # default fallback
    return scalar()


def create_roles(db):
    from app.models import Role
    print("Ensuring default roles...")

    try:
        Role.ensure_default_roles()
    except Exception:

        from app.models.roles import ensure_default_roles as _ensure
        try:
            _ensure()
        except Exception:
            # last resort: создать объекты вручную
            for role_id, role_name in [(0, 'admin'), (1, 'guest'), (2, 'user')]:
                if Role.query.filter_by(name=role_name).first() is None:
                    r = Role(id=role_id, name=role_name)
                    db.session.add(r)
            db.session.commit()
    print("Roles ready.")


def create_users(db, fake):  # pyling disable=R0914
    from app.models import User, UserAvatar, Role, UserRole

    print(f"Creating {NUM_USERS} users...")
    users = []
    for _ in range(NUM_USERS):
        first_name = fake.first_name()
        last_name = fake.last_name()
        middle_name = fake.middle_name() if random.random() < MIDDLE_NAME_PROBABILITY else None

        username = User.generate_username(first_name, last_name, middle_name)
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            registered_at=utcnow() - timedelta(days=random.randint(0, 365))
        )
        user.set_password('P@ssw0rd')

        db.session.add(user)
        users.append(user)

    db.session.commit()

    # Назначим роли: 2-3 админа, остальные роли распределим
    roles = {r.name: r for r in Role.query.all()}
    admins = random.sample(users, max(1, NUM_USERS // 30))
    for a in admins:
        a.roles.append(roles.get('admin'))
    for u in users:
        if u not in admins:
            u.roles.append(roles.get('user'))

    db.session.commit()

    # Создадим аватарки для 10% пользователей
    avatar_count = 0
    for u in random.sample(users, max(1, NUM_USERS // 10)):
        av = UserAvatar(
            user=u,
            filename=f"{u.username}_avatar.png",
            content_type="image/png",
            size=128,
            data=b'\x89PNG\r\n\x1a\n' + bytes(random.getrandbits(8) for _ in range(64)),
            uploaded_at=utcnow()
        )
        db.session.add(av)
        avatar_count += 1

    db.session.commit()
    print(f"Created {len(users)} users, {avatar_count} avatars.")
    return users


def create_tasks(db, fake):
    from app.models import Task

    print("Creating tasks pool...")

    tasks = []

    required_slots = list(range(1, 28))  # 1..27
    for slot in required_slots:
        number = slot
        if slot in (20, 21):
            number = 19

        statement_parts = []
        sentences = random.randint(1, 4)
        for _ in range(sentences):
            statement_parts.append(f"<p>{fake.sentence()}</p>")
        statement_html = "".join(statement_parts)

        answer = _make_answer_for_number(number if number != 20 else 19, fake)

        task = Task(
            number=number,
            statement_html=statement_html,
            answer=answer,
            published_at=utcnow() - timedelta(days=random.randint(0, 180)),
            source=(fake.sentence() if random.random() < SOURCE_PROBABILITY else None),
        )
        db.session.add(task)
        tasks.append(task)

    while len(tasks) < NUM_TASKS_POOL:
        number = random.randint(1, 27)
        if 19 <= number <= 21:
            number = 19
        statement_parts = []
        for _ in range(random.randint(1, 6)):
            statement_parts.append(f"<p>{fake.sentence()}</p>")
        statement_html = "".join(statement_parts)
        answer = _make_answer_for_number(number, fake)
        task = Task(
            number=number,
            statement_html=statement_html,
            answer=answer,
            published_at=utcnow() - timedelta(days=random.randint(0, 180)),
            source=(fake.sentence() if random.random() < SOURCE_PROBABILITY else None),
        )
        db.session.add(task)
        tasks.append(task)

    db.session.commit()
    print(f"Created {len(tasks)} tasks.")
    return tasks


def attach_files_to_some_tasks(db, tasks):
    from app.models import TaskAttachment
    count = 0
    # attach to ~5% tasks
    sample = random.sample(tasks, max(1, len(tasks) // 20))
    for t in sample:
        ta = TaskAttachment(
            task=t,
            filename=f"{t.number}_file.pdf",
            content_type="application/pdf",
            size=2048,
            data=b'%PDF-1.4\n' + bytes(random.getrandbits(8) for _ in range(128)),
            uploaded_at=utcnow()
        )
        db.session.add(ta)
        count += 1
    db.session.commit()
    print(f"Created {count} task attachments.")


def create_variants_and_links(db, tasks, users):
    from app.models import Variant, VariantTask

    print("Creating variants and linking 27 slots per variant (slot 20 and 21 merged into 19)...")
    variants = []
    potential_authors = [u for u in users if random.random() < VARIANT_PROBABILITY]

    slot_to_tasks = {}
    for slot in range(1, 28):
        desired = 19 if slot in (20, 21) else slot
        slot_pool = [t for t in tasks if t.number == desired]
        slot_to_tasks[slot] = slot_pool

    for _ in range(NUM_VARIANTS):
        variant = Variant(
            source=(fake.sentence() if random.random() < SOURCE_PROBABILITY else None),
            created_at=utcnow() - timedelta(days=random.randint(0, 90)),
            duration=random.choice([14100, 10800, 7200]),
            author=random.choice(potential_authors) if potential_authors and random.random() < 0.9 else None
        )
        db.session.add(variant)
        variants.append(variant)
    db.session.commit()

    id_to_task = {t.id: t for t in tasks}

    variant_tasks_total = 0
    for variant in variants:
        used_task_ids = set()
        order = 1
        for slot in range(1, 28):
            pool = slot_to_tasks.get(slot, [])

            avail = [t for t in pool if t.id not in used_task_ids]

            if not avail:
                avail = [t for t in tasks if t.id not in used_task_ids]

            if not avail:
                continue

            chosen = random.choice(avail)
            if chosen.id in used_task_ids:
                continue

            vt = VariantTask(
                variant=variant,
                task=chosen,
                order=order
            )
            db.session.add(vt)
            used_task_ids.add(chosen.id)
            order += 1
            variant_tasks_total += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Warning: commit for variant {variant.id} failed: {e}")
    print(f"Created {len(variants)} variants and {variant_tasks_total} variant_task links.")
    return variants

def create_attempts_and_answers(db, users, variants):
    from app.models import Attempt, AttemptAnswer, VariantTask
    print("Creating attempts and answers with distributed dates...")

    attempts_created = 0
    answers_created = 0

    now = utcnow()
    max_days = 30  # распределение по последнему месяцу

    # выбираем пользователей (как было)
    for user in random.sample(users, max(1, len(users) // 2)):
        # сколько попыток создадим для пользователя
        num_att = random.randint(1, 5)
        chosen_variants = random.sample(variants, min(len(variants), num_att))

        for v in chosen_variants:
            # проверяем уникальность attempt (user, variant)
            existing = Attempt.query.filter_by(user_id=user.id, variant_id=v.id).first()
            if existing:
                continue

            # случайная дата старта в пределах последних max_days дней (разная для каждой попытки)
            days_ago = random.randint(0, max_days - 1)
            seconds_in_day = random.randint(0, 24 * 3600 - 1)
            started_at = now - timedelta(days=days_ago, seconds=seconds_in_day)

            # решаем, будет ли попытка завершена
            finished_is_none = random.random() < 0.3
            finished_at = None
            if not finished_is_none:
                # variant.duration хранится в секундах (обязательное поле)
                dur = getattr(v, "duration", None) or 0
                if dur <= 0:
                    # защита на случай некорректного duration — ставим небольшой временной отрезок
                    dur = 60
                taken_seconds = random.randint(1, int(dur))
                candidate_finished = started_at + timedelta(seconds=taken_seconds)

                # не позволяем finished_at быть в будущем относительно now
                if candidate_finished > now:
                    finished_at = now
                else:
                    finished_at = candidate_finished

            attempt = Attempt(
                examinee=user,
                variant=v,
                started_at=started_at,
                finished_at=finished_at
            )
            db.session.add(attempt)
            db.session.flush()  # чтобы получить attempt.id

            # получаем список VariantTask для варианта в порядке order
            vtasks = VariantTask.query.filter_by(variant_id=v.id).order_by(VariantTask.order).all()

            for vt in vtasks:
                # небольшой шанс оставить вопрос без ответа
                if random.random() < 0.05:
                    answer_text = None
                    is_correct = None
                else:
                    correct = random.random() < 0.7
                    if correct:
                        # кладём "правильный" ответ из задания
                        answer_text = vt.task.answer
                        is_correct = True
                    else:
                        # генерируем неправильный ответ той же "формы"
                        slot = vt.task.number
                        answer_text = _make_answer_for_number(slot, fake)
                        is_correct = False

                aa = AttemptAnswer(
                    attempt=attempt,
                    variant_task=vt,
                    answer_text=answer_text,
                    is_correct=is_correct
                )
                db.session.add(aa)
                answers_created += 1

            attempts_created += 1

            # коммитим после каждой попытки (как в исходнике) — безопасно и контролируемо
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Warning: commit failed for attempt user={user.id} variant={v.id}: {e}")

    print(f"Created {attempts_created} attempts and ~{answers_created} attempt answers.")



def create_user_roles_for_demo(db, users):
    from app.models import Role
    role_user = Role.query.filter_by(name='user').first()
    role_guest = Role.query.filter_by(name='guest').first()
    for u in random.sample(users, max(1, len(users) // 10)):
        if role_user not in u.roles:
            u.roles.append(role_user)
    for u in random.sample(users, max(1, len(users) // 20)):
        if role_guest not in u.roles:
            u.roles.append(role_guest)
    db.session.commit()


def create_test_data(db):
    fake = Faker('ru_RU')

    # create roles first
    create_roles(db)

    users = create_users(db, fake)
    tasks = create_tasks(db, fake)
    attach_files_to_some_tasks(db, tasks)
    variants = create_variants_and_links(db, tasks, users)
    create_user_roles_for_demo(db, users)
    create_attempts_and_answers(db, users, variants)

    print("\n" + "=" * 50)
    print("SEED COMPLETE")
    print(f"Users: {len(users)}")
    print(f"Tasks pool: {len(tasks)}")
    print(f"Variants: {len(variants)}")
    print("=" * 50)


def main():
    import sys
    from app import create_app
    from app.extensions import db

    sys.path.insert(0, str(get_project_root()))
    app = create_app()

    with app.app_context():
        create_test_data(db)


if __name__ == '__main__':
    main()
