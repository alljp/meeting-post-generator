"""
Celery tasks for background job processing.

This module sets up Celery for async task processing and periodic tasks.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "postmeeting",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.meeting_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        "poll-completed-meetings": {
            "task": "app.tasks.meeting_tasks.poll_completed_meetings_periodic",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"expires": 300}  # Task expires after 5 minutes
        },
        "schedule-bot-joins": {
            "task": "app.tasks.meeting_tasks.schedule_bot_joins_periodic",
            "schedule": crontab(minute="*/2"),  # Every 2 minutes
            "options": {"expires": 120}  # Task expires after 2 minutes
        },
    },
)

# Import tasks to register them
from app.tasks import meeting_tasks  # noqa: E402

__all__ = ["celery_app"]

