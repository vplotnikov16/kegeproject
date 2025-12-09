from typing import List, Tuple

from sqlalchemy import func

from app.models import Task


def _parse_kim_key(kim_str: str) -> List[int]:
    kim_str = (kim_str or '').strip()
    if not kim_str:
        return []

    if '-' in kim_str:
        try:
            a_s, b_s = kim_str.split('-', 1)
            a = int(a_s)
            b = int(b_s)
            if b < a:
                return []
            return list(range(a, b + 1))
        except ValueError:
            return []
    try:
        return [int(kim_str)]
    except ValueError:
        return []


def _choose_random_via_sql(query, limit: int):
    return query.order_by(func.random()).limit(limit).all()


def get_random_tasks_for_kim(kim_str: str, count: int) -> List[Task]:
    if count <= 0:
        return []

    # Разбор ключа
    numbers = _parse_kim_key(kim_str)
    if not numbers:
        return []

    if kim_str.strip() == '19-21':
        q = Task.query.filter(Task.number == 19)
    else:
        q = Task.query.filter(Task.number.in_(numbers))
    return _choose_random_via_sql(q, count)


def build_tasks_set(specs: List[Tuple[str, int]]) -> List[Task]:
    selected_tasks: List[Task] = []

    for kim_str, want_count in specs:
        if want_count <= 0:
            continue
        tasks = get_random_tasks_for_kim(kim_str, want_count)
        selected_tasks.extend(tasks)

    return selected_tasks
