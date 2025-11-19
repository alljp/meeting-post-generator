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

# Start health check server in background for Railway
# This allows Railway to verify the worker is running via HTTP health checks
try:
    from app.tasks.health_check import start_health_check_in_background
    import os
    
    # Only start health check server if PORT is set (Railway sets this)
    # or if explicitly enabled via environment variable
    if os.environ.get("ENABLE_CELERY_HEALTH_CHECK", "true").lower() == "true":
        health_check_port = int(os.environ.get("CELERY_HEALTH_CHECK_PORT", os.environ.get("PORT", 9000)))
        start_health_check_in_background(health_check_port)
        logger.info(f"Celery health check server enabled on port {health_check_port}")
except Exception as e:
    # Don't fail if health check server can't start
    logger.warning(f"Failed to start health check server: {e}")

__all__ = ["celery_app"]

