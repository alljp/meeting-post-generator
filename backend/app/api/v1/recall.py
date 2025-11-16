from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.calendar_event import CalendarEvent
from app.models.settings import UserSettings
from app.services.recall_bot_manager import (
    create_bot_for_event,
    join_bot_to_meeting,
    check_and_process_completed_meetings,
    schedule_bot_joins
)
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()


class BotStatusResponse(BaseModel):
    bot_id: str
    status: str
    state: str
    transcript_available: bool
    recording_available: bool


@router.post("/events/{event_id}/create-bot")
async def create_bot_for_calendar_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Recall.ai bot for a calendar event"""
    # Get event
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if not event.meeting_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event does not have a meeting link"
        )
    
    if not event.notetaker_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notetaker is not enabled for this event"
        )
    
    # Get user settings for minutes_before
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    minutes_before = settings.bot_join_minutes_before if settings else 5
    
    # Create bot
    bot_id = await create_bot_for_event(event, db, minutes_before)
    
    if not bot_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bot"
        )
    
    return {"bot_id": bot_id, "message": "Bot created successfully"}


@router.post("/poll-completed")
async def poll_completed_meetings(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Poll for completed meetings and create Meeting records"""
    result = await check_and_process_completed_meetings(current_user.id, db)
    return result


@router.post("/schedule-joins")
async def schedule_bot_joins_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule bots to join meetings that are about to start"""
    # Get user settings
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    minutes_before = settings.bot_join_minutes_before if settings else 5
    
    result = await schedule_bot_joins(current_user.id, db, minutes_before)
    return result


@router.get("/bot/{bot_id}/status")
async def get_bot_status(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of a Recall.ai bot"""
    # Verify bot belongs to user's event
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.recall_bot_id == bot_id,
            CalendarEvent.user_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    from app.services.recall_service import recall_service
    bot_status = await recall_service.get_bot_status(bot_id)
    
    return bot_status

