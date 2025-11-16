from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
from app.models.calendar_event import CalendarEvent
from app.models.meeting import Meeting, Attendee
from app.models.user import User
from app.services.recall_service import recall_service

logger = logging.getLogger(__name__)


async def create_bot_for_event(
    event: CalendarEvent,
    db: AsyncSession,
    minutes_before: int = 5
) -> Optional[str]:
    """
    Create a Recall.ai bot for a calendar event.
    
    Args:
        event: Calendar event with meeting link
        db: Database session
        minutes_before: Minutes before meeting to join (default 5)
    
    Returns:
        Bot ID if created successfully, None otherwise
    """
    # Check if event has a meeting link and notetaker is enabled
    if not event.meeting_link or not event.notetaker_enabled:
        return None
    
    # Check if bot already exists
    if event.recall_bot_id:
        return event.recall_bot_id
    
    try:
        # Calculate join time (X minutes before meeting start)
        join_time = event.start_time - timedelta(minutes=minutes_before)
        
        # Create bot
        bot_response = await recall_service.create_bot(
            meeting_url=event.meeting_link,
            meeting_start_time=event.start_time,
            bot_name=f"{event.title[:50]}-{event.id}"
        )
        
        bot_id = bot_response.get("id")
        if not bot_id:
            return None
        
        # Update event with bot ID
        event.recall_bot_id = bot_id
        await db.commit()
        
        return bot_id
    except Exception as e:
        logger.error(f"Error creating bot for event {event.id}: {e}", exc_info=True)
        return None


async def join_bot_to_meeting(
    bot_id: str,
    event: CalendarEvent,
    db: AsyncSession
) -> bool:
    """
    Join a bot to its meeting.
    
    Args:
        bot_id: The bot ID
        event: Calendar event
        db: Database session
    
    Returns:
        True if joined successfully, False otherwise
    """
    try:
        await recall_service.join_bot(bot_id)
        return True
    except Exception as e:
        logger.error(f"Error joining bot {bot_id}: {e}", exc_info=True)
        return False


async def check_and_process_completed_meetings(
    user_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Check bot statuses and create Meeting records for completed meetings.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        Summary of processed meetings
    """
    # Get all events with bots that haven't been converted to meetings
    # Use timezone-aware datetime for comparison
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.recall_bot_id.isnot(None),
                CalendarEvent.end_time < now
            )
        )
    )
    events_with_bots = result.scalars().all()
    
    created = 0
    updated = 0
    errors = []
    bot_statuses = []
    logger.info(f"Processing {len(events_with_bots)} events with bots for user {user_id}")
    for event in events_with_bots:
        try:
            # Check if meeting already exists
            result = await db.execute(
                select(Meeting).where(Meeting.recall_bot_id == event.recall_bot_id)
            )
            existing_meeting = result.scalar_one_or_none()
            
            if existing_meeting:
                # Update existing meeting if transcript is now available
                bot_status = await recall_service.get_bot_status(event.recall_bot_id)
                bot_statuses.append(bot_status)
                if bot_status.get("transcript_available") and not existing_meeting.transcript_available:
                    transcript = await recall_service.get_transcript(event.recall_bot_id)
                    if transcript:
                        existing_meeting.transcript = transcript
                        existing_meeting.transcript_available = True
                    
                    recording_url = await recall_service.get_recording_url(event.recall_bot_id)
                    if recording_url:
                        existing_meeting.recording_url = recording_url
                    
                    await db.commit()
                    updated += 1
                continue
            
            # Check bot status
            bot_status = await recall_service.get_bot_status(event.recall_bot_id)
            bot_statuses.append(bot_status)
            # Only create meeting if bot has ended or transcript is available
            if bot_status.get("state") in ["ended", "left"] or bot_status.get("transcript_available"):
                # Get transcript
                transcript = await recall_service.get_transcript(event.recall_bot_id)
                recording_url = await recall_service.get_recording_url(event.recall_bot_id)
                
                # Get attendees
                attendees_data = await recall_service.get_bot_attendees(event.recall_bot_id)
                
                # Create meeting
                meeting = Meeting(
                    user_id=user_id,
                    calendar_event_id=event.id,
                    recall_bot_id=event.recall_bot_id,
                    title=event.title,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    platform=event.meeting_platform or "unknown",
                    transcript=transcript,
                    transcript_available=bool(transcript),
                    recording_url=recording_url,
                )
                db.add(meeting)
                await db.flush()  # Get meeting ID
                
                # Create attendees
                for attendee_data in attendees_data:
                    name = attendee_data.get("name") or attendee_data.get("email") or "Unknown"
                    email = attendee_data.get("email")
                    
                    # Check if attendee exists
                    result = await db.execute(
                        select(Attendee).where(
                            and_(
                                Attendee.name == name,
                                Attendee.email == email if email else Attendee.email.is_(None)
                            )
                        )
                    )
                    attendee = result.scalar_one_or_none()
                    
                    if not attendee:
                        attendee = Attendee(name=name, email=email)
                        db.add(attendee)
                        await db.flush()
                    
                    meeting.attendees.append(attendee)
                
                await db.commit()
                created += 1
        except Exception as e:
            errors.append(f"Error processing event {event.id}: {str(e)}")
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "bot_statuses": bot_statuses,
    }


async def schedule_bot_joins(
    user_id: int,
    db: AsyncSession,
    minutes_before: int = 5
) -> Dict[str, Any]:
    """
    Schedule bots to join meetings X minutes before start.
    
    Args:
        user_id: User ID
        db: Database session
        minutes_before: Minutes before meeting to join
    
    Returns:
        Summary of scheduled joins
    """
    # Use timezone-aware datetime for comparison
    now = datetime.now(timezone.utc)
    
    # Calculate the join window
    # Bot should join X minutes before meeting start
    # So if meeting starts at T, bot should join at T - minutes_before
    # We want to find meetings where: (start_time - minutes_before) is around now
    # Which means: start_time should be around (now + minutes_before)
    
    # Tolerance window: ±2 minutes around the exact join time
    # This allows for slight timing variations
    tolerance_minutes = 2
    
    # Calculate the target join time window
    # Bot should join when: (start_time - minutes_before) is between (now - tolerance) and (now + tolerance)
    # Which means: start_time is between (now + minutes_before - tolerance) and (now + minutes_before + tolerance)
    # But we also want to catch meetings that should have been joined already (missed joins)
    # So we extend the window backwards to catch any missed joins
    
    # Window for meetings that should be joined now (within tolerance)
    # start_time should be between (now + minutes_before - tolerance) and (now + minutes_before + tolerance)
    window_start = now + timedelta(minutes=minutes_before - tolerance_minutes)
    window_end = now + timedelta(minutes=minutes_before + tolerance_minutes)
    
    # Also check for missed joins: meetings that should have been joined already
    # Extend backwards to catch meetings that should have been joined up to tolerance_minutes ago
    missed_join_cutoff = now - timedelta(minutes=tolerance_minutes)
    missed_join_window_start = missed_join_cutoff + timedelta(minutes=minutes_before - tolerance_minutes)
    
    # Use the earlier of the two start times to catch both current and missed joins
    final_window_start = min(window_start, missed_join_window_start)
    
    # Get events that need bots to join
    # Events where:
    # - Bot exists
    # - Notetaker is enabled
    # - Meeting hasn't ended yet
    # - Meeting hasn't started too long ago (max 5 min late to catch late joins)
    # - Meeting start time is within our window
    result = await db.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.recall_bot_id.isnot(None),
                CalendarEvent.notetaker_enabled == True,
                CalendarEvent.end_time > now,  # Meeting hasn't ended
                # CalendarEvent.start_time > now - timedelta(minutes=5),  # Meeting hasn't started too long ago
                # CalendarEvent.start_time >= final_window_start,
                # CalendarEvent.start_time <= window_end
            )
        )
    )
    events_to_join = result.scalars().all()
    
    joined = 0
    skipped = 0
    errors = []
    
    for event in events_to_join:
        try:
            # Calculate when the bot should have joined
            expected_join_time = event.start_time - timedelta(minutes=minutes_before)
            time_until_join = (expected_join_time - now).total_seconds() / 60  # minutes
            
            # Only join if we're within the tolerance window (±tolerance_minutes)
            # This ensures we join at the right time regardless of minutes_before value
            if abs(time_until_join) > tolerance_minutes:
                skipped += 1
                continue
            
            # Check if bot is already joined
            bot_status = await recall_service.get_bot_status(event.recall_bot_id)
            current_state = bot_status.get("state", "").lower()
            
            if current_state in ["joined", "in_meeting", "recording"]:
                logger.debug(f"Bot {event.recall_bot_id} for event {event.id} already in state: {current_state}")
                skipped += 1
                continue
            
            # Join bot
            logger.info(f"Joining bot {event.recall_bot_id} to meeting '{event.title}' (event {event.id})")
            success = await join_bot_to_meeting(event.recall_bot_id, event, db)
            if success:
                joined += 1
                logger.info(f"Successfully joined bot {event.recall_bot_id} to meeting '{event.title}'")
            else:
                errors.append(f"Failed to join bot for event {event.id}: join_bot_to_meeting returned False")
        except Exception as e:
            error_msg = f"Error joining bot for event {event.id}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
    
    return {
        "joined": joined,
        "skipped": skipped,
        "errors": errors,
        "events_to_join": events_to_join,
        "test": "test",
        "user_id": user_id,
        "minutes_before": minutes_before,
        "tolerance_minutes": tolerance_minutes,
        "window_start": window_start,
        "window_end": window_end,
        "missed_join_cutoff": missed_join_cutoff,
        "missed_join_window_start": missed_join_window_start,
        "final_window_start": final_window_start,
        "now": now,
    }

