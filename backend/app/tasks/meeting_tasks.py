"""
Celery tasks for meeting-related background jobs.

This module contains periodic tasks for:
- Polling completed meetings and creating Meeting records
- Scheduling bots to join meetings
"""
import sys
import asyncio
import logging
from celery import Task
from app.tasks import celery_app
from app.core.database import AsyncSessionLocal
from app.services.recall_bot_manager import (
    check_and_process_completed_meetings,
    schedule_bot_joins
)
from sqlalchemy import select
from app.models.user import User
from app.models.settings import UserSettings

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Run an async coroutine, handling event loop creation properly.
    Works even if there's already an event loop running (e.g., in some test environments).
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            # Create a new event loop in a thread (for Celery, this shouldn't happen)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            # Loop exists but not running - use it
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists - create one
        # Fix for Windows: Use SelectorEventLoop for psycopg compatibility
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        return asyncio.run(coro)


class DatabaseTask(Task):
    """Custom task class that provides database session management."""
    
    def __call__(self, *args, **kwargs):
        """Execute task with database session."""
        return self.run(*args, **kwargs)


@celery_app.task(
    name="app.tasks.meeting_tasks.poll_completed_meetings_periodic",
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    default_retry_delay=60
)
def poll_completed_meetings_periodic(self):
    """
    Periodic task to poll for completed meetings and create Meeting records.
    
    This task runs every 5 minutes and processes all users' completed meetings.
    """
    logger.info("Starting periodic task: poll_completed_meetings")
    
    try:
        # We need to use async context manager for database sessions
        # Since Celery tasks are sync, we'll use run_async helper
        async def process_all_users():
            async with AsyncSessionLocal() as db:
                # Get all users
                result = await db.execute(select(User))
                users = result.scalars().all()
                
                total_created = 0
                total_updated = 0
                errors = []
                
                for user in users:
                    try:
                        result = await check_and_process_completed_meetings(
                            user_id=user.id,
                            db=db
                        )
                        total_created += result.get("created", 0)
                        total_updated += result.get("updated", 0)
                        if result.get("errors"):
                            errors.extend(result["errors"])
                    except Exception as e:
                        error_msg = f"Error processing user {user.id}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        errors.append(error_msg)
                
                logger.info(
                    f"Completed polling: {total_created} created, "
                    f"{total_updated} updated, {len(errors)} errors"
                )
                
                return {
                    "created": total_created,
                    "updated": total_updated,
                    "errors": errors
                }
        
        # Run async function
        result = run_async(process_all_users())
        return result
        
    except Exception as exc:
        logger.error(f"Error in poll_completed_meetings_periodic: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.meeting_tasks.schedule_bot_joins_periodic",
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    default_retry_delay=60
)
def schedule_bot_joins_periodic(self):
    """
    Periodic task to schedule bots to join meetings that are about to start.
    
    This task runs every 2 minutes to ensure bots join meetings on time.
    """
    logger.info("Starting periodic task: schedule_bot_joins")
    
    try:
        async def process_all_users():
            async with AsyncSessionLocal() as db:
                # Get all users
                result = await db.execute(select(User))
                users = result.scalars().all()
                
                total_joined = 0
                total_skipped = 0
                errors = []
                
                for user in users:
                    try:
                        # Get user settings for minutes_before
                        settings_result = await db.execute(
                            select(UserSettings).where(
                                UserSettings.user_id == user.id
                            )
                        )
                        settings = settings_result.scalar_one_or_none()
                        minutes_before = (
                            settings.bot_join_minutes_before 
                            if settings else 5
                        )
                        
                        result = await schedule_bot_joins(
                            user_id=user.id,
                            db=db,
                            minutes_before=minutes_before
                        )
                        total_joined += result.get("joined", 0)
                        total_skipped += result.get("skipped", 0)
                        if result.get("errors"):
                            errors.extend(result["errors"])
                    except Exception as e:
                        error_msg = f"Error scheduling joins for user {user.id}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        errors.append(error_msg)
                
                logger.info(
                    f"Completed scheduling: {total_joined} joined, "
                    f"{total_skipped} skipped, {len(errors)} errors"
                )
                
                return {
                    "joined": total_joined,
                    "skipped": total_skipped,
                    "errors": errors
                }
        
        # Run async function
        result = run_async(process_all_users())
        return result
        
    except Exception as exc:
        logger.error(f"Error in schedule_bot_joins_periodic: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)

