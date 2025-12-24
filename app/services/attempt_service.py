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

        answer = AttemptAnswer.query.filter_by(attempt_id=attempt_id, variant_task_id=variant_task_id).first()

        if answer:
            answer.answer_text = answer_text
            answer.updated_at = utcnow()
        else:
            answer = AttemptAnswer(attempt_id=attempt_id, variant_task_id=variant_task_id, answer_text=answer_text)
            db.session.add(answer)

        db.session.commit()
        return answer

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
        total_display_tasks = 0

        for vt in variant_tasks:
            task = vt.task
            answer = answers_map.get(vt.id)
            user_answer = answer.answer_text if answer else None

            if task.number == 19:
                # Задача 19 отображается как 3 задачи (19, 20, 21)
                # Каждая ячейка таблицы = отдельная задача
                total_display_tasks += 3

                results.append({
                    'task_number': 19,
                    'correct_answer': task.answer,
                    'user_answer': user_answer,
                    'task_id': task.id,
                    'is_task_19_group': True,  # Флаг для фронтенда
                })
            else:
                # Обычная задача
                total_display_tasks += 1

                results.append({
                    'task_number': task.number,
                    'correct_answer': task.answer,
                    'user_answer': user_answer,
                    'task_id': task.id,
                    'is_task_19_group': False,
                })

        return {
            'attempt_id': attempt.id,
            'variant_id': attempt.variant_id,
            'started_at': attempt.started_at.isoformat(),
            'finished_at': attempt.finished_at.isoformat(),
            'results': results,
            'total_tasks': total_display_tasks,
        }
