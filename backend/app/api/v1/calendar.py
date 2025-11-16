from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
import logging
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.calendar_event import CalendarEvent
from app.models.settings import UserSettings
from app.services.calendar.service import calendar_service

router = APIRouter()
logger = logging.getLogger(__name__)


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    meeting_link: Optional[str]
    meeting_platform: Optional[str]
    notetaker_enabled: bool
    recall_bot_id: Optional[str]
    google_event_id: str


class SyncResponse(BaseModel):
    synced: int
    created: int
    updated: int
    errors: List[str]
    create_bots: bool
    minutes_before: int
    bots_created: List[str]
    events: List[Dict[str, Any]]


@router.get("/events", response_model=List[CalendarEventResponse])
async def list_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: Optional[int] = 50,
    days_ahead: Optional[int] = 30
):
    """List upcoming calendar events for the current user"""
    # Use timezone-aware datetime for comparison
    now = datetime.now(timezone.utc)
    time_max = now.replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(days=days_ahead or 30)
    
    # Query events - only get events that haven't ended yet
    result = await db.execute(
        select(CalendarEvent)
        .where(
            and_(
                CalendarEvent.user_id == current_user.id,
                CalendarEvent.end_time > now,  # Event hasn't ended yet
                CalendarEvent.start_time <= time_max
            )
        )
        .order_by(CalendarEvent.start_time)
        .limit(limit or 50)
    )
    
    events = result.scalars().all()
    return events


@router.patch("/events/{event_id}/notetaker", response_model=CalendarEventResponse)
async def toggle_notetaker(
    event_id: int,
    enabled: bool = Query(..., description="Enable or disable notetaker"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle notetaker for an event"""
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
    
    # Update notetaker status
    event.notetaker_enabled = enabled
    await db.commit()
    await db.refresh(event)
    
    return event


@router.post("/sync", response_model=SyncResponse)
async def sync_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually sync calendar events from Google Calendar"""
    logger.info(f"Sync endpoint called by user {current_user.id} ({current_user.email})")
    
    # Get user settings for bot creation
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    minutes_before = settings.bot_join_minutes_before if settings else 5
    
    logger.info(f"User settings: minutes_before={minutes_before}")
    
    try:
        result = await calendar_service.sync_calendar_events_for_user(
            user_id=current_user.id, 
            db=db, 
            create_bots=True,
            minutes_before=minutes_before
        )
        
        logger.info(f"Sync endpoint returning: synced={result.get('synced')}, errors={len(result.get('errors', []))}")
        
        return SyncResponse(**result)
    except Exception as e:
        logger.error(f"Error in sync endpoint: {e}", exc_info=True)
        raise

