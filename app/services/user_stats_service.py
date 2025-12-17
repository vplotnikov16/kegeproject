from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_

from app.models import Attempt, Variant, VariantTask
from app.utils.date_utils import utcnow


class UserStatsService:
    """
    Сервис для сбора и обработки статистики пользователя
    """

    @staticmethod
    def get_user_attempts(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получить все попытки пользователя с основной информацией
        """
        attempts = (
            Attempt.query
            .filter_by(user_id=user_id)
            .order_by(Attempt.finished_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for attempt in attempts:
            if not attempt.finished_at:
                continue

            correct_count = sum(1 for ans in attempt.answers if ans.is_correct is True)
            total_count = len(attempt.answers)
            score = (correct_count / total_count * 100) if total_count > 0 else 0

            result.append({
                'id': attempt.id,
                'variant_source': attempt.variant.source or f'Вариант #{attempt.variant.id}',
                'started_at': attempt.started_at.strftime('%d.%m.%Y %H:%M'),
                'finished_at': attempt.finished_at.strftime('%d.%m.%Y %H:%M'),
                'duration': attempt.variant.duration,
                'correct_answers': correct_count,
                'total_answers': total_count,
                'score': round(score, 2),
                'is_full_variant': UserStatsService._is_full_variant(attempt.variant),
            })

        return result

    @staticmethod
    def _is_full_variant(variant: Variant) -> bool:
        """
        Проверить, является ли вариант полным ЕГЭ вариантом
        В БД хранится 25 задач (19-21 как одна), но отображаются 27 номеров (1-27)
        """
        tasks = VariantTask.query.filter_by(variant_id=variant.id).order_by(VariantTask.order).all()

        # Получить номера всех задач из БД
        task_numbers = sorted(set(t.task.number for t in tasks))

        # Полный вариант должен содержать номера: 1-18, 19 (за 19-21), 22-27
        # Это 25 уникальных номеров в БД, но 27 отображаемых задач
        expected_numbers = list(range(1, 19)) + [19] + list(range(22, 28))

        return task_numbers == expected_numbers

    @staticmethod
    def convert_to_secondary_score(primary_score: int) -> int:
        """
        Конвертация первичного балла во вторичный (0-100) по официальной шкале ЕГЭ
        Максимум 29 первичных баллов = 100 вторичных
        """
        score_table = {
            0: 0,
            1: 7, 2: 14, 3: 20, 4: 27, 5: 34, 6: 40, 7: 43, 8: 46,
            9: 48, 10: 51, 11: 54, 12: 56, 13: 59, 14: 62, 15: 64,
            16: 67, 17: 70, 18: 72, 19: 75, 20: 78, 21: 80, 22: 83,
            23: 85, 24: 88, 25: 90, 26: 93, 27: 95, 28: 98, 29: 100,
        }
        return score_table.get(min(primary_score, 29), 100)

    @staticmethod
    def get_attempt_details_with_scoring(attempt_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить детали попытки с конвертацией баллов (если полный вариант)
        """
        attempt = Attempt.query.get(attempt_id)
        if not attempt or attempt.user_id != user_id or not attempt.finished_at:
            return None

        variant = attempt.variant
        is_full = UserStatsService._is_full_variant(variant)

        # Подсчёт по номерам задач (1-27)
        answers_by_number = {}
        for answer in attempt.answers:
            task_number = answer.variant_task.task.number
            answers_by_number[task_number] = {
                'correct': answer.is_correct,
                'user_answer': answer.answer_text,
                'task_id': answer.variant_task.task_id,
            }

        # Подсчёт первичных баллов
        primary_score = 0
        if is_full:
            # Система баллов ЕГЭ информатика (29 максимум):
            task_scores = {
                1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
                11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 3,
                22: 1, 23: 1, 24: 1, 25: 1, 26: 2, 27: 2,
            }

            for task_num, score_info in answers_by_number.items():
                if score_info['correct'] and task_num in task_scores:
                    primary_score += task_scores[task_num]

        secondary_score = UserStatsService.convert_to_secondary_score(primary_score) if is_full else None

        return {
            'attempt_id': attempt.id,
            'variant_source': variant.source or f'Вариант #{variant.id}',
            'started_at': attempt.started_at.strftime('%d.%m.%Y %H:%M:%S'),
            'finished_at': attempt.finished_at.strftime('%d.%m.%Y %H:%M:%S'),
            'duration_seconds': attempt.variant.duration,
            'time_spent': UserStatsService._calculate_time_spent(attempt),
            'is_full_variant': is_full,
            'answers_by_number': answers_by_number,
            'total_correct': sum(1 for v in answers_by_number.values() if v['correct']),
            'total_answers': 27 if is_full else len(answers_by_number),
            'primary_score': primary_score if is_full else None,
            'secondary_score': secondary_score,
            'details_by_task': UserStatsService._get_task_details(attempt),
        }

    @staticmethod
    def _calculate_time_spent(attempt: Attempt) -> str:
        """
        Вычислить реальное время, потраченное на решение
        """
        if not attempt.finished_at:
            return "Не завершено"

        delta = attempt.finished_at - attempt.started_at
        minutes = delta.total_seconds() / 60
        hours = int(minutes // 60)
        mins = int(minutes % 60)

        if hours > 0:
            return f"{hours}ч {mins}мин"
        return f"{mins}мин"

    @staticmethod
    def _get_task_details(attempt: Attempt) -> Dict[int, Dict[str, Any]]:
        """
        Получить детальную информацию по каждой задаче
        """
        details = {}
        for answer in attempt.answers:
            task_num = answer.variant_task.task.number
            details[task_num] = {
                'correct': answer.is_correct,
                'user_answer': answer.answer_text,
                'correct_answer': answer.variant_task.task.answer,
                'updated_at': answer.updated_at.strftime('%d.%m.%Y %H:%M:%S'),
            }
        return details

    @staticmethod
    def get_performance_by_task_number(user_id: int, days: int = 90) -> Dict[int, Dict[str, Any]]:
        """
        Получить статистику по каждому номеру задачи (1-27) за период
        """
        cutoff_date = utcnow() - timedelta(days=days)

        attempts = (
            Attempt.query
            .filter(
                and_(
                    Attempt.user_id == user_id,
                    Attempt.finished_at.isnot(None),
                    Attempt.finished_at >= cutoff_date
                )
            )
            .all()
        )

        task_stats = {}
        for task_num in range(1, 28):
            task_stats[task_num] = {
                'correct': 0,
                'total': 0,
                'percentage': 0.0,
            }

        for attempt in attempts:
            for answer in attempt.answers:
                task_num = answer.variant_task.task.number
                if task_num not in task_stats:
                    continue

                task_stats[task_num]['total'] += 1
                if answer.is_correct:
                    task_stats[task_num]['correct'] += 1

        # Вычислить проценты
        for task_num in task_stats:
            if task_stats[task_num]['total'] > 0:
                task_stats[task_num]['percentage'] = round(
                    (task_stats[task_num]['correct'] / task_stats[task_num]['total']) * 100, 2
                )

        return task_stats

    @staticmethod
    def get_solving_speed_trends(user_id: int) -> List[Dict[str, Any]]:
        """
        Получить тенденции скорости решения стандартных вариантов
        """
        attempts = (
            Attempt.query
            .filter_by(user_id=user_id)
            .filter(Attempt.finished_at.isnot(None))
            .order_by(Attempt.finished_at)
            .all()
        )

        trends = []
        for attempt in attempts:
            if not UserStatsService._is_full_variant(attempt.variant):
                continue

            time_spent_minutes = (attempt.finished_at - attempt.started_at).total_seconds() / 60
            correct_count = sum(1 for ans in attempt.answers if ans.is_correct is True)

            trends.append({
                'date': attempt.finished_at.strftime('%d.%m.%Y'),
                'time_minutes': round(time_spent_minutes, 1),
                'correct_answers': correct_count,
                'total_answers': len(attempt.answers),
            })

        return trends

    @staticmethod
    def get_summary_stats(user_id: int) -> Dict[str, Any]:
        """
        Получить итоговую статистику пользователя
        """
        attempts = (
            Attempt.query
            .filter_by(user_id=user_id)
            .filter(Attempt.finished_at.isnot(None))
            .all()
        )

        if not attempts:
            return {
                'total_attempts': 0,
                'average_score': 0,
                'best_score': 0,
                'full_variants_count': 0,
            }

        scores = []
        best_score = 0
        full_count = 0

        for attempt in attempts:
            correct = sum(1 for ans in attempt.answers if ans.is_correct is True)
            total = len(attempt.answers)
            score = (correct / total * 100) if total > 0 else 0
            scores.append(score)
            best_score = max(best_score, score)

            if UserStatsService._is_full_variant(attempt.variant):
                full_count += 1

        return {
            'total_attempts': len(attempts),
            'average_score': round(sum(scores) / len(scores), 2) if scores else 0,
            'best_score': round(best_score, 2),
            'full_variants_count': full_count,
        }
