from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import asyncio
from app.models.user import GoogleAccount
from app.services.calendar.base import CalendarProvider
from app.core.config import settings
from dateutil import parser as date_parser
import re

logger = logging.getLogger(__name__)


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar provider implementation"""
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    def refresh_credentials(self, account: GoogleAccount) -> Optional[Credentials]:
        """Refresh Google OAuth credentials if needed"""
        try:
            logger.debug(f"Refreshing credentials for account {account.google_email}")
            
            # Validate that we have required fields
            if not account.access_token:
                logger.error(f"No access token for {account.google_email}")
                return None
            
            if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
                logger.error("Google OAuth credentials not configured in settings")
                return None
            
            # Import scopes from auth strategy
            from app.auth.strategies.google import SCOPES
            
            creds = Credentials(
                token=account.access_token,
                refresh_token=account.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=SCOPES,  # Explicitly set scopes
            )
            
            # Always validate/refresh credentials to ensure they're valid
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    logger.info(f"Credentials expired for {account.google_email}, refreshing...")
                    creds.refresh(Request())
                    logger.info(f"Successfully refreshed credentials for {account.google_email}")
                    # Note: In production, update the database with new token
                else:
                    logger.error(f"Credentials invalid and no refresh token for {account.google_email}")
                    return None
            
            # Verify credentials have calendar scope
            if creds.scopes and 'calendar.readonly' not in str(creds.scopes):
                logger.warning(f"Credentials may not have calendar scope for {account.google_email}, scopes: {creds.scopes}")
            
            return creds
        except Exception as e:
            logger.error(f"Error refreshing credentials for {account.google_email}: {e}", exc_info=True)
            return None
    
    async def fetch_events(
        self,
        account: GoogleAccount,
        max_results: int = 50,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch events from Google Calendar"""
        try:
            logger.info(f"Fetching events from Google Calendar for account {account.google_email}")
            
            # Refresh credentials
            creds = self.refresh_credentials(account)
            if not creds:
                error_msg = f"Failed to refresh credentials for {account.google_email}"
                logger.error(error_msg)
                # Raise an exception instead of returning empty list so caller knows it's an error
                raise ValueError(f"Authentication failed: Unable to refresh credentials for {account.google_email}. Please reconnect your Google account.")
            
            logger.debug(f"Credentials valid for {account.google_email}, building calendar service...")
            
            # Build Calendar API service - run in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            service = await loop.run_in_executor(
                None,
                lambda: build('calendar', 'v3', credentials=creds)
            )
            
            # Set time range (default: now to 30 days ahead)
            if not time_min:
                time_min = datetime.now(timezone.utc)
            if not time_max:
                time_max = time_min + timedelta(days=30)
            
            # Ensure timezone-aware
            if time_min.tzinfo is None:
                time_min = time_min.replace(tzinfo=timezone.utc)
            if time_max.tzinfo is None:
                time_max = time_max.replace(tzinfo=timezone.utc)
            
            # Convert to UTC and format
            time_min_utc = time_min.astimezone(timezone.utc)
            time_max_utc = time_max.astimezone(timezone.utc)
            
            # Format as ISO 8601 with Z suffix (Google Calendar API format)
            time_min_str = time_min_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            time_max_str = time_max_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            logger.debug(f"Fetching events from {time_min_str} to {time_max_str} for {account.google_email}")
            
            # Execute API call in thread pool since it's synchronous
            # Note: orderBy='startTime' requires singleEvents=True, but all-day events don't have startTime
            # We'll handle this by catching errors and retrying without orderBy if needed
            def _fetch_events_sync():
                try:
                    # First try with orderBy for better results
                    request = service.events().list(
                        calendarId='primary',
                        timeMin=time_min_str,
                        timeMax=time_max_str,
                        maxResults=max_results,
                        singleEvents=True,
                        orderBy='startTime'
                    )
                    return request.execute()
                except HttpError as e:
                    # If orderBy fails (e.g., all-day events), retry without it
                    if e.resp.status == 400 and 'orderBy' in str(e):
                        logger.warning(f"Retrying calendar API call without orderBy for {account.google_email}")
                        request = service.events().list(
                            calendarId='primary',
                            timeMin=time_min_str,
                            timeMax=time_max_str,
                            maxResults=max_results,
                            singleEvents=True
                        )
                        return request.execute()
                    raise
            
            logger.debug(f"Executing Google Calendar API call for {account.google_email}")
            events_result = await loop.run_in_executor(None, _fetch_events_sync)
            
            if not events_result:
                logger.warning(f"Google Calendar API returned empty result for {account.google_email}")
                return []
            
            events = events_result.get('items', [])
            next_page_token = events_result.get('nextPageToken')
            
            logger.debug(f"API returned {len(events)} events for {account.google_email}")
            
            # Handle pagination if there are more results
            total_events = len(events)
            while next_page_token and total_events < max_results:
                def _fetch_next_page():
                    request = service.events().list(
                        calendarId='primary',
                        timeMin=time_min_str,
                        timeMax=time_max_str,
                        maxResults=min(max_results - total_events, max_results),
                        singleEvents=True,
                        pageToken=next_page_token
                    )
                    return request.execute()
                
                next_result = await loop.run_in_executor(None, _fetch_next_page)
                next_events = next_result.get('items', [])
                events.extend(next_events)
                total_events = len(events)
                next_page_token = next_result.get('nextPageToken')
            
            logger.info(f"Successfully fetched {len(events)} events from {account.google_email}")
            
            if len(events) == 0:
                logger.warning(f"No events found for {account.google_email} between {time_min_str} and {time_max_str}")
            
            return events
        except HttpError as e:
            error_code = e.resp.status if hasattr(e, 'resp') else 'unknown'
            error_msg = f"HTTP error {error_code} fetching calendar events for {account.google_email}: {e}"
            logger.error(error_msg, exc_info=True)
            
            # Provide specific error messages based on status code
            if error_code == 401:
                logger.error("Unauthorized - Credentials are invalid or expired. Please reconnect Google account.")
            elif error_code == 403:
                logger.error("Forbidden - Calendar API access denied. Check OAuth scopes and permissions.")
            elif error_code == 404:
                logger.error("Calendar not found - Primary calendar may not exist.")
            
            # Log the error details
            if hasattr(e, 'content'):
                error_content = e.content.decode('utf-8') if isinstance(e.content, bytes) else str(e.content)
                logger.error(f"HTTP error content: {error_content}")
            
            # Try to get error reason from response
            try:
                error_details = e.error_details if hasattr(e, 'error_details') else None
                if error_details:
                    logger.error(f"Error details: {error_details}")
            except:
                pass
            
            # Re-raise HttpError so caller can handle it specifically
            raise
        except Exception as e:
            error_msg = f"Unexpected error fetching calendar events for {account.google_email}: {e}"
            logger.error(error_msg, exc_info=True)
            # Re-raise the exception so caller knows about the error
            raise RuntimeError(f"Failed to fetch calendar events: {str(e)}") from e
    
    def extract_meeting_link(self, event: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract meeting link and platform from Google Calendar event.
        Checks hangoutLink, conferenceData, description, and location.
        Returns (platform, link) tuple.
        """
        # Priority 1: Check hangoutLink (Google Meet)
        hangout_link = event.get('hangoutLink')
        if hangout_link:
            return ('meet', hangout_link)
        
        # Priority 2: Check conferenceData.entryPoints (Google Meet, Zoom, Teams)
        conference_data = event.get('conferenceData', {})
        entry_points = conference_data.get('entryPoints', [])
        if entry_points:
            # Get the first video entry point
            for entry_point in entry_points:
                if entry_point.get('entryPointType') == 'video':
                    uri = entry_point.get('uri')
                    if uri:
                        # Determine platform from URI
                        uri_lower = uri.lower()
                        if 'meet.google.com' in uri_lower:
                            return ('meet', uri)
                        elif 'zoom.us' in uri_lower:
                            return ('zoom', uri)
                        elif 'teams.microsoft.com' in uri_lower or 'web.microsoft.com' in uri_lower:
                            return ('teams', uri)
                        # Return as-is if we can't determine platform
                        return (None, uri)
        
        # Priority 3: Check description and location (fallback to regex detection)
        description = event.get('description', '')
        location = event.get('location', '')
        return self._detect_meeting_platform(description, location)
    
    def _detect_meeting_platform(self, description: Optional[str], location: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect meeting platform and extract meeting link from description or location.
        Returns (platform, link) tuple.
        """
        text = f"{description or ''} {location or ''}".lower()
        
        # Zoom patterns
        zoom_patterns = [
            r'https?://(?:[a-z0-9-]+\.)?zoom\.us/j/(\d+)',
            r'https?://(?:[a-z0-9-]+\.)?zoom\.us/my/([a-z0-9]+)',
            r'zoom\.us/j/(\d+)',
            r'zoom\.us/my/([a-z0-9]+)',
        ]
        for pattern in zoom_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(0).startswith('http'):
                    return ('zoom', match.group(0))
                else:
                    return ('zoom', f"https://zoom.us/j/{match.group(1)}")
        
        # Microsoft Teams patterns
        teams_patterns = [
            r'https?://teams\.microsoft\.com/l/meetup-join/[^\s<>"\'\)]+',
            r'https?://[a-z0-9-]+\.web\.microsoft\.com/meet/[^\s<>"\'\)]+',
        ]
        for pattern in teams_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return ('teams', match.group(0))
        
        # Google Meet patterns
        meet_patterns = [
            r'https?://meet\.google\.com/[a-z]+-[a-z]+-[a-z]+',
            r'meet\.google\.com/[a-z]+-[a-z]+-[a-z]+',
        ]
        for pattern in meet_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(0).startswith('http'):
                    return ('meet', match.group(0))
                else:
                    return ('meet', f"https://{match.group(0)}")
        
        return (None, None)

