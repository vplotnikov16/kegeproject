from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import and_

from app.models import User, Task, Variant, Attempt
from app.utils.date_utils import utcnow


class DashboardService:
    @staticmethod
    def get_total_stats() -> Dict[str, int]:
        return {
            'total_users': User.query.count(),
            'total_tasks': Task.query.count(),
            'total_variants': Variant.query.count(),
            'total_attempts': Attempt.query.count(),
        }

    @staticmethod
    def get_recent_users(limit: int = 5) -> List[Dict[str, Any]]:
        users = (
            User.query
            .order_by(User.registered_at.desc())
            .limit(limit)
            .all()
        )
        return [user.as_dict for user in users]

    @staticmethod
    def get_recent_tasks(limit: int = 5) -> List[Dict[str, Any]]:
        tasks = (
            Task.query
            .order_by(Task.published_at.desc())
            .limit(limit)
            .all()
        )
        return [task.as_dict for task in tasks]

    @staticmethod
    def get_recent_variants(limit: int = 5) -> List[Dict[str, Any]]:
        variants = (
            Variant.query
            .order_by(Variant.created_at.desc())
            .limit(limit)
            .all()
        )
        return [variant.as_dict for variant in variants]

    @staticmethod
    def get_latest_completed_attempt() -> Optional[Dict[str, Any]]:
        attempt = (
            Attempt.query
            .filter(Attempt.finished_at.isnot(None))
            .order_by(Attempt.finished_at.desc())
            .first()
        )
        if not attempt:
            return None

        correct_count = sum(
            1 for answer in attempt.answers
            if answer.is_correct is True
        )
        total_count = len(attempt.answers)
        score = (correct_count / total_count * 100) if total_count > 0 else 0

        return {
            'id': attempt.id,
            'examinee_username': attempt.examinee.username,
            'variant_source': attempt.variant.source or 'Без источника',
            'finished_at': attempt.finished_at.strftime('%d.%m.%Y %H:%M'),
            'correct_answers': correct_count,
            'total_answers': total_count,
            'score': round(score, 2),
        }

    @staticmethod
    def get_score_distribution(days: int = 30) -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        attempts = (
            Attempt.query
            .filter(
                and_(
                    Attempt.finished_at.isnot(None),
                    Attempt.finished_at >= cutoff_date
                )
            )
            .all()
        )

        scores = []
        for attempt in attempts:
            correct_count = sum(
                1 for answer in attempt.answers
                if answer.is_correct is True
            )
            total_count = len(attempt.answers)
            if total_count > 0:
                score = correct_count / total_count * 100
                scores.append(score)

        score_ranges = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0,
        }

        for score in scores:
            if score <= 20:
                score_ranges['0-20'] += 1
            elif score <= 40:
                score_ranges['21-40'] += 1
            elif score <= 60:
                score_ranges['41-60'] += 1
            elif score <= 80:
                score_ranges['61-80'] += 1
            else:
                score_ranges['81-100'] += 1

        return score_ranges

    @staticmethod
    def get_average_scores_by_week(weeks: int = 4) -> List[Dict[str, Any]]:
        cutoff_date = utcnow() - timedelta(weeks=weeks)

        attempts = (
            Attempt.query
            .filter(
                and_(
                    Attempt.finished_at.isnot(None),
                    Attempt.finished_at >= cutoff_date
                )
            )
            .all()
        )

        weekly_data = {}
        for attempt in attempts:
            week_start = attempt.finished_at - timedelta(days=attempt.finished_at.weekday())
            week_key = week_start.strftime('%Y-%W')

            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    'week_start': week_start,
                    'scores': [],
                    'attempt_count': 0,
                }

            correct_count = sum(
                1 for answer in attempt.answers
                if answer.is_correct is True
            )
            total_count = len(attempt.answers)
            if total_count > 0:
                score = correct_count / total_count * 100
                weekly_data[week_key]['scores'].append(score)
                weekly_data[week_key]['attempt_count'] += 1

        result = []
        for week_key in sorted(weekly_data.keys()):
            data = weekly_data[week_key]
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                week_end = data['week_start'] + timedelta(days=6)
                result.append({
                    'week_start': data['week_start'].strftime('%d.%m'),
                    'week_end': week_end.strftime('%d.%m'),
                    'average_score': round(avg_score, 2),
                    'attempt_count': data['attempt_count'],
                })

        return result

    @staticmethod
    def get_top_performers(limit: int = 5, days: int = 30) -> List[Dict[str, Any]]:
        cutoff_date = utcnow() - timedelta(days=days)

        attempts = (
            Attempt.query
            .filter(
                and_(
                    Attempt.finished_at.isnot(None),
                    Attempt.finished_at >= cutoff_date
                )
            )
            .all()
        )

        user_scores = {}
        for attempt in attempts:
            user_id = attempt.user_id
            correct_count = sum(
                1 for answer in attempt.answers
                if answer.is_correct is True
            )
            total_count = len(attempt.answers)
            if total_count > 0:
                score = correct_count / total_count * 100

                if user_id not in user_scores:
                    user_scores[user_id] = {'scores': [], 'user': attempt.examinee}

                user_scores[user_id]['scores'].append(score)

        result = []
        for user_id, data in user_scores.items():
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                user = data['user']
                result.append({
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'average_score': round(avg_score, 2),
                    'attempts_count': len(data['scores']),
                })

        result.sort(key=lambda x: x['average_score'], reverse=True)
        return result[:limit]

    @staticmethod
    def get_activity_stats(days: int = 7) -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        new_users = User.query.filter(User.registered_at >= cutoff_date).count()
        new_tasks = Task.query.filter(Task.published_at >= cutoff_date).count()
        new_variants = Variant.query.filter(Variant.created_at >= cutoff_date).count()
        new_attempts = Attempt.query.filter(Attempt.started_at >= cutoff_date).count()

        return {
            'new_users': new_users,
            'new_tasks': new_tasks,
            'new_variants': new_variants,
            'new_attempts': new_attempts,
            'period_days': days,
        }

    @staticmethod
    def get_dashboard_data() -> Dict[str, Any]:
        return {
            'total_stats': DashboardService.get_total_stats(),
            'recent_users': DashboardService.get_recent_users(5),
            'recent_tasks': DashboardService.get_recent_tasks(5),
            'recent_variants': DashboardService.get_recent_variants(5),
            'latest_attempt': DashboardService.get_latest_completed_attempt(),
            'score_distribution': DashboardService.get_score_distribution(30),
            'weekly_scores': DashboardService.get_average_scores_by_week(4),
            'top_performers': DashboardService.get_top_performers(5, 30),
            'activity_stats': DashboardService.get_activity_stats(7),
        }
