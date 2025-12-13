from typing import Iterable, List, Sequence

from app.models import Task


class TaskService:
    @staticmethod
    def get_by_ids(ids: Sequence[int]) -> List[Task]:
        if not ids:
            return []

        return (
            Task.query
            .filter(Task.id.in_(ids))
            .order_by(Task.id)
            .all()
        )

    @staticmethod
    def get_by_numbers(numbers: Iterable[int]) -> List[Task]:
        nums = list(numbers)
        if not nums:
            return []

        return (
            Task.query
            .filter(Task.number.in_(nums))
            .order_by(Task.number, Task.id)
            .all()
        )

    @staticmethod
    def get_by_author(author_id: int) -> List[Task]:
        return (
            Task.query
            .filter_by(author_id=author_id)
            .order_by(Task.published_at.desc())
            .all()
        )
