from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
from app.services.calendar.factory import CalendarProviderFactory
from app.services.calendar.base import CalendarProvider
from app.models.user import GoogleAccount
from app.models.calendar_event import CalendarEvent
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Calendar service facade that provides high-level calendar operations.
    Delegates to CalendarProviderFactory for actual implementation.
    """
    
    def __init__(self):
        """Initialize calendar service"""
        pass
    
    async def fetch_google_calendar_events(
        self,
        google_account: GoogleAccount,
        db: AsyncSession,
        max_results: int = 50,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch events from a Google Calendar account"""
        provider: CalendarProvider = CalendarProviderFactory.create("google")
        return await provider.fetch_events(
            account=google_account,
            max_results=max_results,
            time_min=time_min,
            time_max=time_max
        )
    
    def extract_meeting_link_from_google_event(self, google_event: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Extract meeting link and platform from Google Calendar event"""
        provider: CalendarProvider = CalendarProviderFactory.create("google")
        return provider.extract_meeting_link(google_event)
    
    def refresh_google_credentials(self, google_account: GoogleAccount) -> Optional[Any]:
        """Refresh Google OAuth credentials if needed"""
        provider: CalendarProvider = CalendarProviderFactory.create("google")
        return provider.refresh_credentials(google_account)
    
    async def sync_calendar_events_for_user(
        self,
        user_id: int,
        db: AsyncSession,
        create_bots: bool = True,
        minutes_before: int = 5
    ) -> Dict[str, Any]:
        """Sync calendar events for all Google accounts of a user"""
        logger.info(f"=" * 60)
        logger.info(f"Starting calendar sync for user {user_id}")
        logger.info(f"Create bots: {create_bots}, Minutes before: {minutes_before}")
        
        # Get all active Google accounts for the user
        result = await db.execute(
            select(GoogleAccount).where(
                GoogleAccount.user_id == user_id,
                GoogleAccount.is_active == True
            )
        )
        google_accounts = result.scalars().all()
        
        logger.info(f"Found {len(google_accounts)} active Google account(s) for user {user_id}")
        for account in google_accounts:
            logger.info(f"  - Account: {account.google_email} (ID: {account.id}, Active: {account.is_active})")
        
        if not google_accounts:
            error_msg = "No active Google accounts found. Please connect a Google account first."
            logger.warning(f"{error_msg} (User ID: {user_id})")
            logger.info(f"Calendar sync completed for user {user_id}: No accounts found")
            logger.info(f"=" * 60)
            return {
                "synced": 0,
                "created": 0,
                "updated": 0,
                "errors": [error_msg],
                "create_bots": create_bots,
                "minutes_before": minutes_before,
                "bots_created": [],
                "events": []
            }
        
        provider: CalendarProvider = CalendarProviderFactory.create("google")
        
        total_synced = 0
        total_created = 0
        total_updated = 0
        errors = []
        bots_created = []
        events = []
        
        for google_account in google_accounts:
            try:
                logger.info(f"Starting sync for Google account: {google_account.google_email} (ID: {google_account.id})")
                
                # Fetch events from Google Calendar
                try:
                    google_events = await provider.fetch_events(google_account)
                except Exception as fetch_error:
                    error_msg = f"Exception while fetching events from {google_account.google_email}: {str(fetch_error)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
                    continue
                
                if google_events is None:
                    error_msg = f"fetch_events returned None for account {google_account.google_email} (this indicates an error)"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue
                
                if not google_events:
                    logger.warning(f"No events fetched from account {google_account.google_email}. This could mean:")
                    logger.warning(f"  1. The account has no events in the time range")
                    logger.warning(f"  2. Credentials are invalid or expired")
                    logger.warning(f"  3. API permissions are insufficient")
                    # Don't add this as an error - account might just not have events
                    continue
                
                logger.info(f"Fetched {len(google_events)} events from account {google_account.google_email}, processing...")
                
                for google_event in google_events:
                    try:
                        # Extract event data
                        event_id = google_event.get('id')
                        if not event_id:
                            logger.warning(f"Skipping event without ID: {google_event.get('summary', 'Unknown')}")
                            continue
                        
                        # Check if event already exists for this specific Google account
                        # Important: Check both google_event_id AND google_account_id
                        # because the same event ID could theoretically exist in different accounts
                        result = await db.execute(
                            select(CalendarEvent).where(
                                and_(
                                    CalendarEvent.google_event_id == event_id,
                                    CalendarEvent.google_account_id == google_account.id
                                )
                            )
                        )
                        existing_event = result.scalar_one_or_none()
                        
                        # Parse event times with timezone support
                        start_data = google_event.get('start', {})
                        end_data = google_event.get('end', {})
                        
                        start_dt = start_data.get('dateTime') or start_data.get('date')
                        end_dt = end_data.get('dateTime') or end_data.get('date')
                        
                        if not start_dt or not end_dt:
                            continue
                        
                        # Parse datetime with timezone support using dateutil
                        try:
                            start_time = date_parser.parse(start_dt)
                            end_time = date_parser.parse(end_dt)
                            
                            # Ensure timezone-aware (convert naive to UTC if needed)
                            from datetime import timezone
                            if start_time.tzinfo is None:
                                start_time = start_time.replace(tzinfo=timezone.utc)
                            if end_time.tzinfo is None:
                                end_time = end_time.replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError, AttributeError) as e:
                            error_msg = f"Error parsing datetime for event {event_id} (start: {start_dt}, end: {end_dt}): {str(e)}"
                            errors.append(error_msg)
                            logger.error(error_msg, exc_info=True)
                            continue
                        except Exception as e:
                            error_msg = f"Unexpected error parsing datetime for event {event_id}: {str(e)}"
                            errors.append(error_msg)
                            logger.error(error_msg, exc_info=True)
                            continue
                        
                        # Extract meeting platform and link from Google event
                        platform, meeting_link = provider.extract_meeting_link(google_event)
                        
                        # Get description and location for storage
                        description = google_event.get('description', '')
                        location = google_event.get('location', '')
                        
                        event_data = {
                            'user_id': user_id,
                            'google_account_id': google_account.id,
                            'google_event_id': event_id,
                            'title': google_event.get('summary', 'Untitled Event'),
                            'description': description,
                            'start_time': start_time,
                            'end_time': end_time,
                            'location': location,
                            'meeting_link': meeting_link,
                            'meeting_platform': platform,
                        }
                        
                        if existing_event:
                            # Update existing event
                            for key, value in event_data.items():
                                setattr(existing_event, key, value)
                            total_updated += 1
                            event_to_process = existing_event
                        else:
                            # Create new event
                            new_event = CalendarEvent(**event_data)
                            db.add(new_event)
                            await db.flush()  # Get event ID
                            total_created += 1
                            event_to_process = new_event
                        
                        events.append({
                            "meeting_link": event_to_process.meeting_link,
                            "notetaker_enabled": event_to_process.notetaker_enabled,
                            "title": event_to_process.title,
                            "start_time": event_to_process.start_time,
                            "end_time": event_to_process.end_time,
                            "location": event_to_process.location,
                            "meeting_platform": event_to_process.meeting_platform,
                            "description": event_to_process.description,
                            "google_event_id": event_to_process.google_event_id,
                            "google_event": google_event,
                            "recall_bot_id": event_to_process.recall_bot_id,
                        })
                        
                        # Create bot if meeting link exists and notetaker is enabled
                        if create_bots and event_to_process.meeting_link and event_to_process.notetaker_enabled:
                            if not event_to_process.recall_bot_id:
                                try:
                                    from app.services.recall_bot_manager import create_bot_for_event
                                    bot_id = await create_bot_for_event(event_to_process, db, minutes_before)
                                    if bot_id:
                                        event_to_process.recall_bot_id = bot_id
                                    bots_created.append(bot_id)
                                except Exception as e:
                                    errors.append(f"Error creating bot for event {event_id}: {str(e)}")
                        
                        total_synced += 1
                    except Exception as e:
                        errors.append(f"Error processing event {event_id}: {str(e)}")
                
                await db.commit()
                logger.info(f"Completed sync for account {google_account.google_email}: {total_synced} events synced")
            except Exception as e:
                error_msg = f"Error syncing account {google_account.google_email}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        logger.info(f"Calendar sync completed for user {user_id}:")
        logger.info(f"  - Total synced: {total_synced}")
        logger.info(f"  - Created: {total_created}")
        logger.info(f"  - Updated: {total_updated}")
        logger.info(f"  - Errors: {len(errors)}")
        logger.info(f"  - Bots created: {len(bots_created)}")
        logger.info(f"=" * 60)
        
        return {
            "synced": total_synced,
            "created": total_created,
            "updated": total_updated,
            "errors": errors,
            "create_bots": create_bots,
            "minutes_before": minutes_before,
            "bots_created": bots_created,
            "events": events,
        }


# Singleton instance
calendar_service = CalendarService()

