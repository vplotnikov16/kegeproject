from typing import Dict, List, Any, Optional
from datetime import timedelta
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
            .filter(Attempt.finished_at.isnot(None))
            .order_by(Attempt.finished_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for attempt in attempts:
            variant_tasks = VariantTask.query.filter_by(variant_id=attempt.variant_id).all()

            # Подсчёт реального количества задач для отображения
            total_display_tasks = attempt.variant.total_display_tasks
            correct_count = 0

            for vt in variant_tasks:
                answer = next((a for a in attempt.answers if a.variant_task_id == vt.id), None)

                # Если ответа нет вообще - пропускаем
                if not answer:
                    continue

                # Обработка задачи 19 (отдельно для каждой ячейки)
                if vt.task.number == 19:
                    # Задача 19: проверяем каждую ячейку отдельно (формат CSV: "A,B,C")
                    try:
                        # Парсим CSV
                        user_cells = [c.strip() for c in (answer.answer_text.split(',') if answer.answer_text else [])]
                        correct_cells = [c.strip() for c in (vt.task.answer.split(',') if vt.task.answer else [])]

                        # Проверяем каждую ячейку (максимум 3)
                        for i in range(3):
                            user_val = user_cells[i] if i < len(user_cells) else ''
                            correct_val = correct_cells[i] if i < len(correct_cells) else ''

                            # Если ячейка заполнена и правильная - считаем
                            if user_val and correct_val and user_val.lower() == correct_val.lower():
                                correct_count += 1
                    except (IndexError, AttributeError, ValueError):
                        # При ошибке парсинга не засчитываем ничего
                        pass
                else:
                    # Обычная задача: используем поле is_correct
                    if answer.is_correct:
                        correct_count += 1

            score = (correct_count / total_display_tasks * 100) if total_display_tasks > 0 else 0

            result.append({
                'id': attempt.id,
                'variant_source': attempt.variant.source or f'Вариант #{attempt.variant.id}',
                'started_at': attempt.started_at.strftime('%d.%m.%Y %H:%M'),
                'finished_at': attempt.finished_at.strftime('%d.%m.%Y %H:%M'),
                'duration': attempt.variant.duration,
                'correct_answers': correct_count,
                'total_answers': total_display_tasks,
                'score': round(score, 2),
                'is_full_variant': UserStatsService.is_full_variant(attempt.variant),
            })

        return result

    @staticmethod
    def is_full_variant(variant: Variant) -> bool:
        tasks = VariantTask.query.filter_by(variant_id=variant.id).all()

        # Подсчитываем количество каждого номера КИМ
        number_counts = {}
        for vt in tasks:
            num = vt.task.number
            number_counts[num] = number_counts.get(num, 0) + 1

        # Ожидаемая структура полного варианта:
        # Номера 1-18: по 1 разу
        for num in range(1, 19):
            if number_counts.get(num, 0) != 1:
                return False

        # Номер 19: ровно 1 раз (это задачи 19-21)
        if number_counts.get(19, 0) != 1:
            return False

        # Номера 22-27: по 1 разу
        for num in range(22, 28):
            if number_counts.get(num, 0) != 1:
                return False

        # Проверка, что нет лишних номеров
        expected_numbers = set(range(1, 19)) | {19} | set(range(22, 28))
        actual_numbers = set(number_counts.keys())

        return actual_numbers == expected_numbers and len(tasks) == 25

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
        is_full = UserStatsService.is_full_variant(variant)

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
            if not UserStatsService.is_full_variant(attempt.variant):
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

            if UserStatsService.is_full_variant(attempt.variant):
                full_count += 1

        return {
            'total_attempts': len(attempts),
            'average_score': round(sum(scores) / len(scores), 2) if scores else 0,
            'best_score': round(best_score, 2),
            'full_variants_count': full_count,
        }

    @staticmethod
    def count_display_tasks(variant_tasks: List[VariantTask]) -> int:
        count = 0
        for vt in variant_tasks:
            if vt.task.number == 19:
                count += 3  # Задачи 19-21 считаются как 3
            else:
                count += 1
        return count

    @staticmethod
    def count_answered_tasks_for_task19(answer_text: str) -> int:
        if not answer_text:
            return 0

        try:
            import json
            answers = json.loads(answer_text)
            # Подсчитываем непустые ячейки
            return sum(1 for v in answers.values() if v and str(v).strip())
        except (json.JSONDecodeError, AttributeError):
            # Если не JSON или ошибка парсинга
            return 1 if answer_text.strip() else 0

    @staticmethod
    def is_table_answer_filled(answer_text: str) -> bool:
        if not answer_text:
            return False

        try:
            import json
            answers = json.loads(answer_text)
            return any(v and str(v).strip() for v in answers.values())
        except (json.JSONDecodeError, AttributeError):
            return bool(answer_text.strip())
