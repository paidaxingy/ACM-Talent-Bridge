"""
Celery tasks package.

Celery autodiscovery imports `app.tasks` (this package). We import task modules here
so all tasks get registered on worker startup.
"""

from app.tasks.aggregate_contests import aggregate_contests  # noqa: F401
from app.tasks.ai_profile import generate_daily_ai_profiles  # noqa: F401
from app.tasks.ai_interview import evaluate_interview_answer, generate_interview_questions  # noqa: F401
from app.tasks.judge import judge_submission  # noqa: F401
from app.tasks.ping import ping  # noqa: F401

