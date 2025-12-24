from typing import Dict, Optional

from app.extensions import db
from app.models import Attempt, AttemptAnswer, VariantTask
from app.utils.date_utils import utcnow


class AttemptService:
    @staticmethod
    def create_attempt(user_id: int, variant_id: int) -> Attempt:
        attempt = Attempt(user_id=user_id, variant_id=variant_id, started_at=utcnow())
        db.session.add(attempt)
        db.session.commit()
        return attempt

    @staticmethod
    def get_attempt(attempt_id: int, user_id: int) -> Optional[Attempt]:
        return Attempt.query.filter_by(id=attempt_id, user_id=user_id).first()

    @staticmethod
    def finish_attempt(attempt_id: int, user_id: int) -> Optional[Attempt]:
        attempt = AttemptService.get_attempt(attempt_id, user_id)
        if not attempt or attempt.finished_at:
            return None

        attempt.finished_at = utcnow()
        db.session.commit()
        return attempt

    @staticmethod
    def save_answer(attempt_id: int, variant_task_id: int, answer_text: str, user_id: int) -> Optional[AttemptAnswer]:
        attempt = AttemptService.get_attempt(attempt_id, user_id)
        if not attempt:
            return None

        if attempt.finished_at:
            return None

        # Получить VariantTask для доступа к Task
        variant_task = VariantTask.query.get(variant_task_id)
        if not variant_task:
            return None

        # Вычислить is_correct
        correct_answer = variant_task.task.answer
        is_correct = AttemptService._check_answer_correctness(
            user_answer=answer_text,
            correct_answer=correct_answer,
            task_number=variant_task.task.number
        )

        answer = AttemptAnswer.query.filter_by(attempt_id=attempt_id, variant_task_id=variant_task_id).first()

        if answer:
            answer.answer_text = answer_text
            answer.is_correct = is_correct
            answer.updated_at = utcnow()
        else:
            answer = AttemptAnswer(
                attempt_id=attempt_id,
                variant_task_id=variant_task_id,
                answer_text=answer_text,
                is_correct=is_correct
            )
            db.session.add(answer)

        db.session.commit()
        return answer

    @staticmethod
    def _check_answer_correctness(user_answer: str, correct_answer: str, task_number: int) -> bool:
        """
        Проверить правильность ответа.

        Для задачи 19: считается правильным, если ВСЕ 3 ячейки правильные.
        Для остальных задач: нормализованное сравнение.
        """
        if not user_answer or not correct_answer:
            return False

        if task_number == 19:
            # Задача 19: проверяем все 3 ячейки
            try:
                user_cells = [c.strip().lower() for c in user_answer.split(',')]
                correct_cells = [c.strip().lower() for c in correct_answer.split(',')]

                # Все 3 ячейки должны совпадать
                if len(user_cells) >= 3 and len(correct_cells) >= 3:
                    return all(
                        user_cells[i] == correct_cells[i]
                        for i in range(3)
                    )
                return False
            except (IndexError, AttributeError):
                return False
        else:
            # Обычная задача: нормализованное сравнение
            # Для табличных задач сравниваем весь CSV
            return AttemptService._normalize_answer(user_answer) == AttemptService._normalize_answer(correct_answer)

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        """
        Нормализация ответа
        """
        if not answer:
            return ''

        # Если это CSV (таблица)
        if ',' in answer or '\n' in answer:
            rows = answer.split('\n')
            normalized_rows = []
            for row in rows:
                # Убираем пустые ячейки и нормализуем
                cells = [c.strip().lower() for c in row.split(',') if c.strip()]
                if cells:  # Только если есть непустые ячейки
                    normalized_rows.append(','.join(cells))
            return '\n'.join(normalized_rows)
        else:
            return answer.strip().lower()

    @staticmethod
    def get_attempt_data(attempt_id: int, user_id: int) -> Optional[Dict]:
        attempt = AttemptService.get_attempt(attempt_id, user_id)
        if not attempt:
            return None

        variant_tasks = (
            VariantTask.query
            .filter_by(variant_id=attempt.variant_id)
            .order_by(VariantTask.order)
            .all()
        )

        answers = {
            aa.variant_task_id: aa.answer_text
            for aa in attempt.answers
        }

        return {
            'attempt': attempt.as_dict,
            'tasks': [
                {
                    **vt.task.as_dict,
                    'variant_task_id': vt.id,
                    'order': vt.order,
                    'current_answer': answers.get(vt.id)  # ← ВАЖНО
                }
                for vt in variant_tasks
            ],
            'stats': {
                'answered': len([a for a in answers.values() if a]),
                'total': len(variant_tasks),
            }
        }

    @staticmethod
    def get_attempt_results(attempt_id: int, user_id: int) -> Optional[Dict]:
        attempt = AttemptService.get_attempt(attempt_id, user_id)
        if not attempt or not attempt.finished_at:
            return None

        variant_tasks = VariantTask.query.filter_by(variant_id=attempt.variant_id).order_by(VariantTask.order).all()
        answers_map = {aa.variant_task_id: aa for aa in attempt.answers}

        results = []

        for vt in variant_tasks:
            task = vt.task
            answer = answers_map.get(vt.id)
            user_answer = answer.answer_text if answer else None

            # Определяем, является ли это задачей 19
            is_task_19 = task.number == 19

            results.append({
                'task_number': task.number,
                'correct_answer': task.answer,
                'user_answer': user_answer,
                'task_id': task.id,
                'is_task_19_group': is_task_19,
            })

        return {
            'attempt_id': attempt.id,
            'variant_id': attempt.variant_id,
            'started_at': attempt.started_at.isoformat(),
            'finished_at': attempt.finished_at.isoformat(),
            'results': results,
            'total_tasks': attempt.variant.total_display_tasks,
        }
