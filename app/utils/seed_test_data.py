import random
from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional

from faker import Faker

from app.utils.date_utils import utcnow
from run_in_venv import get_project_root

NUM_USERS = 100
NUM_TASKS = 400
NUM_VARIANTS = 150

VARIANT_PROBABILITY = 0.7
MIDDLE_NAME_PROBABILITY = 0.7
SOURCE_PROBABILITY = 0.6
SINGLE_ANSWER_PROB = 0.8

ATTEMPTS_MAX_PER_VARIANT = 3


def _scalar_value(fake: Faker) -> str:
    if random.random() < SINGLE_ANSWER_PROB:
        return str(random.randint(1, 100))
    return fake.word().upper()


def _vector_line(n: int, fake: Faker) -> str:
    parts: List[str] = []
    for _ in range(n):
        parts.append(_scalar_value(fake) if random.random() < 0.5 else fake.word().upper())
    return ";".join(parts)


def _table_rows(rows: int, cols: int, fake: Faker) -> str:
    out: List[str] = []
    for _ in range(rows):
        row: List[str] = []
        for _ in range(cols):
            row.append(_scalar_value(fake) if random.random() < 0.5 else fake.word().upper())
        out.append(";".join(row))
    return "\n".join(out)


def make_answer_csv(slot_num: int, fake: Faker) -> str:
    if 1 <= slot_num <= 16 or 22 <= slot_num <= 24:
        return _scalar_value(fake)
    if slot_num in (17, 18, 26):
        return _vector_line(2, fake)
    if slot_num == 19:
        return _vector_line(3, fake)
    if slot_num == 25:
        return _table_rows(10, 2, fake)
    if slot_num == 27:
        return _table_rows(2, 2, fake)
    return _scalar_value(fake)


# ---------- user creation ----------
def _make_user_object(fake: Faker):
    from app.models import User
    first = fake.first_name()
    last = fake.last_name()
    middle = fake.middle_name() if random.random() < MIDDLE_NAME_PROBABILITY else None
    username = User.generate_username(first, last, middle)
    u = User(
        username=username,
        first_name=first,
        last_name=last,
        middle_name=middle,
        registered_at=utcnow() - timedelta(days=random.randint(0, 365)),
    )
    u.set_password("P@ssw0rd")
    return u


def create_users(db, count: int = NUM_USERS) -> List[int]:
    from app.models import User
    fake = Faker("ru_RU")
    created_ids: List[int] = []
    print(f"Создаю {count} новых пользователей...")
    for _ in range(count):
        u = _make_user_object(fake)
        db.session.add(u)
    # назначим id (flush) — в одной транзакции
    db.session.flush()
    # вернём список новых пользователей (последние count в таблице)
    rows = db.session.query(User.id).order_by(User.id.desc()).limit(count).all()
    for r in reversed(rows):
        created_ids.append(r.id)
    print(f"Добавлено {len(created_ids)} пользователей (id сгенерированы).")
    return created_ids


def add_avatars_for_users(db, user_ids: Iterable[int], proportion: float = 0.1) -> int:
    from app.models import UserAvatar
    user_list = list(user_ids)
    sample_size = max(1, int(len(user_list) * proportion))
    sample = random.sample(user_list, sample_size)
    created = 0
    for uid in sample:
        # только для новых users — предполагаем, что пользователь не имеет аватарки
        av = UserAvatar(
            user_id=uid,
            filename=f"user_{uid}_avatar.png",
            content_type="image/png",
            size=128,
            data=b"\x89PNG\r\n\x1a\n" + bytes(random.getrandbits(8) for _ in range(64)),
            uploaded_at=utcnow(),
        )
        db.session.add(av)
        created += 1
    print(f"Создано аватарок: {created}.")
    return created


# ---------- task creation ----------
def _make_task_object(number: int, fake: Faker):
    from app.models import Task
    text = "".join(f"<p>{fake.sentence()}</p>" for _ in range(random.randint(1, 4)))
    return Task(
        number=number,
        statement_html=text,
        answer=make_answer_csv(number, fake),
        published_at=utcnow() - timedelta(days=random.randint(0, 180)),
        source=(fake.sentence() if random.random() < SOURCE_PROBABILITY else None),
    )


def create_tasks(db, count: int = NUM_TASKS) -> List[int]:
    from app.models import Task
    fake = Faker("ru_RU")
    created_ids: List[int] = []
    print(f"Создаю {count} новых задач...")

    def normalize_slot(s: int) -> int:
        return 19 if s in (20, 21) else s

    for _ in range(count):
        num = normalize_slot(random.randint(1, 27))
        t = _make_task_object(num, fake)
        db.session.add(t)

    db.session.flush()
    rows = db.session.query(Task.id).order_by(Task.id.desc()).limit(count).all()
    for r in reversed(rows):
        created_ids.append(r.id)
    print(f"Добавлено задач: {len(created_ids)}.")
    return created_ids


def add_attachments_for_tasks(db, task_ids: Iterable[int], proportion: float = 0.05) -> int:
    from app.models import TaskAttachment
    task_list = list(task_ids)
    sample_size = max(1, int(len(task_list) * proportion))
    sample = random.sample(task_list, sample_size)
    created = 0
    for tid in sample:
        ta = TaskAttachment(
            task_id=tid,
            filename=f"{tid}_file.pdf",
            content_type="application/pdf",
            size=2048,
            data=b"%PDF-1.4\n" + bytes(random.getrandbits(8) for _ in range(128)),
            uploaded_at=utcnow(),
        )
        db.session.add(ta)
        created += 1
    print(f"Добавлено вложений к задачам: {created}.")
    return created


# ---------- variant creation ----------
def create_variants(db, count: int = NUM_VARIANTS, author_ids: Optional[List[int]] = None) -> List[int]:
    from app.models import Variant, User
    fake = Faker()
    created_ids: List[int] = []
    if author_ids is None:
        author_ids = [r.id for r in db.session.query(User.id).all()] or []
    print(f"Создаю {count} новых вариантов...")
    for _ in range(count):
        author_id = random.choice(author_ids) if author_ids and random.random() < 0.9 else None
        v = Variant(
            source=(fake.sentence() if random.random() < SOURCE_PROBABILITY else None),
            created_at=utcnow() - timedelta(days=random.randint(0, 90)),
            duration=random.choice([14100, 10800, 7200]),
            author_id=author_id,
        )
        db.session.add(v)
    db.session.flush()
    rows = db.session.query(Variant.id).order_by(Variant.id.desc()).limit(count).all()
    for r in reversed(rows):
        created_ids.append(r.id)
    print(f"Добавлено вариантов: {len(created_ids)}.")
    return created_ids


# ---------- task chooser (polymorphic small object) ----------
class TaskChooser:
    def __init__(self, db, relevant_task_ids: Iterable[int]):
        from app.models import Task
        rows = db.session.query(Task.id, Task.number).filter(Task.id.in_(relevant_task_ids)).all()
        pool: Dict[int, List[int]] = {}
        for r in rows:
            pool.setdefault(r.number, []).append(r.id)
        self.pool = pool
        self.global_list = [r.id for r in rows]

    def pick_for_slot(self, slot: int, used: set) -> Optional[int]:
        desired = 19 if slot in (20, 21) else slot
        candidates = [tid for tid in self.pool.get(desired, []) if tid not in used]
        if candidates:
            return random.choice(candidates)
        other = [tid for tid in self.global_list if tid not in used]
        if other:
            return random.choice(other)
        return None


# ---------- variant_task linking ----------
def link_tasks_to_variants(db, variant_ids: Iterable[int], task_ids: Iterable[int]) -> int:
    from app.models import VariantTask
    chooser = TaskChooser(db, task_ids)
    to_insert_count = 0
    for vid in variant_ids:
        used: set = set()
        order = 1
        for slot in range(1, 28):
            tid = chooser.pick_for_slot(slot, used)
            if tid is None:
                continue
            used.add(tid)
            vt = VariantTask(variant_id=vid, task_id=tid, order=order)
            db.session.add(vt)
            order += 1
            to_insert_count += 1
    print(f"Добавлено variant_task записей: {to_insert_count}.")
    return to_insert_count


def _random_times_for_attempt(db, variant_id: int):
    from app.models import Variant
    now = utcnow()
    started = now - timedelta(days=random.randint(0, 29), seconds=random.randint(0, 24 * 3600 - 1))
    finished = None
    if random.random() >= 0.3:
        dur = db.session.query(Variant.duration).filter(Variant.id == variant_id).scalar()
        dur = int(dur) if dur and dur > 0 else 60
        taken = random.randint(1, dur)
        cand = started + timedelta(seconds=taken)
        finished = now if cand > now else cand
    return started, finished


def _build_variant_task_map(db, variant_ids: Iterable[int]) -> Dict[int, List[Dict[str, Any]]]:
    from app.models import VariantTask, Task

    rows = (
        db.session.query(
            VariantTask.id,
            VariantTask.variant_id,
            Task.number,
            Task.answer,
        )
        .join(Task, VariantTask.task_id == Task.id)
        .filter(VariantTask.variant_id.in_(list(variant_ids)))
        .order_by(VariantTask.variant_id, VariantTask.order)
        .all()
    )

    mapping: Dict[int, List[Dict[str, Any]]] = {}
    for row in rows:
        mapping.setdefault(row.variant_id, []).append(
            {
                "vt_id": row.id,
                "number": row.number,
                "answer": row.answer,
            }
        )

    return mapping


def _make_attempt_answer(fake: Faker, vt: Dict[str, Any]):
    if random.random() < 0.05:
        return None, None

    if random.random() < 0.7:
        return vt["answer"], True

    return make_answer_csv(vt["number"], fake), False


def _create_answers_for_attempt(db, attempt_id: int, vtasks: List[Dict[str, Any]], fake: Faker) -> int:
    from app.models import AttemptAnswer

    created = 0
    for vt in vtasks:
        text, correct = _make_attempt_answer(fake, vt)
        db.session.add(
            AttemptAnswer(
                attempt_id=attempt_id,
                variant_task_id=vt["vt_id"],
                answer_text=text,
                is_correct=correct,
            )
        )
        created += 1

    return created


def _create_single_attempt(db, user_id: int, variant_id: int):
    from app.models import Attempt

    exists = (
        db.session.query(Attempt.id)
        .filter_by(user_id=user_id, variant_id=variant_id)
        .first()
    )
    if exists:
        return None

    started_at, finished_at = _random_times_for_attempt(db, variant_id)

    attempt = Attempt(
        user_id=user_id,
        variant_id=variant_id,
        started_at=started_at,
        finished_at=finished_at,
    )
    db.session.add(attempt)
    db.session.flush()
    return attempt


def create_attempts_and_answers(
        db,
        variant_ids: Iterable[int],
        user_ids: Iterable[int],
) -> int:
    fake = Faker("ru_RU")
    created_attempts = 0
    created_answers = 0

    user_list = list(user_ids)
    if not user_list:
        print("Нет пользователей для создания попыток — пропускаю.")
        return 0

    variant_task_map = _build_variant_task_map(db, variant_ids)

    for variant_id in variant_ids:
        vtasks = variant_task_map.get(variant_id)
        if not vtasks:
            continue

        attempts_count = random.randint(1, ATTEMPTS_MAX_PER_VARIANT)
        users_sample = random.sample(user_list, min(len(user_list), attempts_count))

        for user_id in users_sample:
            attempt = _create_single_attempt(db, user_id, variant_id)
            if attempt is None:
                continue

            created_answers += _create_answers_for_attempt(
                db,
                attempt.id,
                vtasks,
                fake,
            )
            created_attempts += 1

    print(f"Создано попыток: {created_attempts}, ответов: {created_answers}.")
    return created_attempts


def seed_add_new(db,
                 users_n: int = NUM_USERS,
                 tasks_n: int = NUM_TASKS,
                 variants_n: int = NUM_VARIANTS) -> None:
    from app.models import User
    try:
        print("Начинаю генерацию новых данных. Вся операция будет выполнена одной транзакцией.")
        new_user_ids = create_users(db, users_n)
        add_avatars_for_users(db, new_user_ids)

        new_task_ids = create_tasks(db, tasks_n)
        add_attachments_for_tasks(db, new_task_ids)

        db.session.flush()

        new_variant_ids = create_variants(db, variants_n, author_ids=list(new_user_ids) or None)

        link_tasks_to_variants(db, new_variant_ids, new_task_ids)

        all_user_ids = [r.id for r in db.session.query(User.id).all()]
        create_attempts_and_answers(db, new_variant_ids, all_user_ids)

        db.session.commit()
        print("Транзакция завершена: все новые данные сохранены.")
    except Exception as e:
        db.session.rollback()
        print("Ошибка при сидировании - выполнен откат транзакции.")
        print(e)
        raise


def main():
    import sys
    from app import create_app
    from app.extensions import db

    sys.path.insert(0, str(get_project_root()))
    app = create_app()

    db.session.expire_on_commit = False

    with app.app_context():
        seed_add_new(db)


if __name__ == "__main__":
    main()
