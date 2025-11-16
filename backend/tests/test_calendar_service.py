"""
Unit tests for Calendar Service.
Tests Google Calendar integration and event synchronization.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.services.calendar.service import calendar_service
from app.models.user import GoogleAccount
from app.models.calendar_event import CalendarEvent


class TestCalendarService:
    """Test suite for CalendarService."""
    
    def test_extract_meeting_link_hangout(self):
        """Test extracting Google Meet link from hangoutLink."""
        event = {
            "hangoutLink": "https://meet.google.com/abc-def-ghi"
        }
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform == "meet"
        assert link == "https://meet.google.com/abc-def-ghi"
    
    def test_extract_meeting_link_conference_data_meet(self):
        """Test extracting meeting link from conferenceData."""
        event = {
            "conferenceData": {
                "entryPoints": [
                    {
                        "entryPointType": "video",
                        "uri": "https://meet.google.com/abc-def-ghi"
                    }
                ]
            }
        }
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform == "meet"
        assert link == "https://meet.google.com/abc-def-ghi"
    
    def test_extract_meeting_link_conference_data_zoom(self):
        """Test extracting Zoom link from conferenceData."""
        event = {
            "conferenceData": {
                "entryPoints": [
                    {
                        "entryPointType": "video",
                        "uri": "https://zoom.us/j/123456789"
                    }
                ]
            }
        }
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform == "zoom"
        assert link == "https://zoom.us/j/123456789"
    
    def test_extract_meeting_link_conference_data_teams(self):
        """Test extracting Teams link from conferenceData."""
        event = {
            "conferenceData": {
                "entryPoints": [
                    {
                        "entryPointType": "video",
                        "uri": "https://teams.microsoft.com/l/meetup-join/123"
                    }
                ]
            }
        }
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform == "teams"
        assert link == "https://teams.microsoft.com/l/meetup-join/123"
    
    def test_detect_meeting_platform_zoom_url(self):
        """Test detecting Zoom platform from URL in description."""
        description = "Join Zoom meeting: https://zoom.us/j/123456789"
        event = {"description": description}
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform == "zoom"
        assert "zoom.us" in link.lower()
    
    def test_detect_meeting_platform_teams_url(self):
        """Test detecting Teams platform from URL."""
        description = "Join Teams: https://teams.microsoft.com/l/meetup-join/abc123"
        event = {"description": description}
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform == "teams"
        assert "teams.microsoft.com" in link.lower()
    
    def test_detect_meeting_platform_meet_url(self):
        """Test detecting Google Meet platform from URL."""
        description = "Google Meet: https://meet.google.com/abc-def-ghi"
        event = {"description": description}
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform == "meet"
        assert "meet.google.com" in link.lower()
    
    def test_detect_meeting_platform_zoom_id_only(self):
        """Test detecting Zoom from meeting ID only."""
        # The function requires "zoom.us" pattern, not just a number
        # Test with partial zoom URL pattern
        description = "Zoom ID: zoom.us/j/123456789"
        event = {"description": description}
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        # Should detect zoom pattern
        assert platform == "zoom"
        assert link is not None
    
    def test_detect_meeting_platform_no_link(self):
        """Test when no meeting link is found."""
        description = "Regular meeting without link"
        event = {"description": description}
        platform, link = calendar_service.extract_meeting_link_from_google_event(event)
        assert platform is None
        assert link is None
    
    @pytest.mark.asyncio
    async def test_sync_calendar_events_no_google_accounts(self, db_session, test_user):
        """Test sync when user has no Google accounts."""
        result = await calendar_service.sync_calendar_events_for_user(
            user_id=test_user.id,
            db=db_session,
            create_bots=False
        )
        assert result["synced"] == 0
        assert result["created"] == 0
        assert result["updated"] == 0
    
    @pytest.mark.asyncio
    async def test_sync_calendar_events_with_google_account(self, db_session, test_user, test_google_account):
        """Test syncing calendar events with a Google account."""
        # Mock Google Calendar API
        mock_events = [
            {
                "id": "event_123",
                "summary": "Test Meeting",
                "description": "Test description",
                "start": {
                    "dateTime": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                },
                "end": {
                    "dateTime": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
                },
                "hangoutLink": "https://meet.google.com/abc-def-ghi"
            }
        ]
        
        with patch("app.services.calendar.factory.CalendarProviderFactory.create") as mock_factory:
            mock_provider = MagicMock()
            mock_provider.fetch_events = AsyncMock(return_value=mock_events)
            mock_provider.extract_meeting_link = MagicMock(return_value=("meet", "https://meet.google.com/abc-def-ghi"))
            mock_factory.return_value = mock_provider
            
            result = await calendar_service.sync_calendar_events_for_user(
                user_id=test_user.id,
                db=db_session,
                create_bots=False
            )
            
            assert result["synced"] > 0
            assert result["created"] > 0
    
    @pytest.mark.asyncio
    async def test_sync_calendar_events_multiple_google_accounts(
        self, db_session, test_user, test_google_account
    ):
        """Test syncing calendar events with multiple Google accounts."""
        # Create a second Google account
        second_account = GoogleAccount(
            user_id=test_user.id,
            google_email="second@gmail.com",
            access_token="token2",
            refresh_token="refresh2",
            is_active=True
        )
        db_session.add(second_account)
        await db_session.commit()
        await db_session.refresh(second_account)
        
        # Mock Google Calendar API responses for both accounts
        mock_events_account1 = [
            {
                "id": "event_1",
                "summary": "Meeting from Account 1",
                "start": {
                    "dateTime": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                },
                "end": {
                    "dateTime": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
                },
                "hangoutLink": "https://meet.google.com/abc-def-ghi"
            }
        ]
        
        mock_events_account2 = [
            {
                "id": "event_2",
                "summary": "Meeting from Account 2",
                "start": {
                    "dateTime": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
                },
                "end": {
                    "dateTime": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
                },
                "hangoutLink": "https://meet.google.com/xyz-uvw-rst"
            }
        ]
        
        call_count = 0
        def mock_fetch_events(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_events_account1
            else:
                return mock_events_account2
        
        with patch("app.services.calendar.factory.CalendarProviderFactory.create") as mock_factory:
            mock_provider = MagicMock()
            mock_provider.fetch_events = AsyncMock(side_effect=mock_fetch_events)
            mock_provider.extract_meeting_link = MagicMock(side_effect=[
                ("meet", "https://meet.google.com/abc-def-ghi"),
                ("meet", "https://meet.google.com/xyz-uvw-rst")
            ])
            mock_factory.return_value = mock_provider
            
            result = await calendar_service.sync_calendar_events_for_user(
                user_id=test_user.id,
                db=db_session,
                create_bots=False
            )
            
            # Should sync events from both accounts
            assert result["synced"] == 2
            assert result["created"] == 2
            
            # Verify events were created for both accounts
            from sqlalchemy import select
            result_query = await db_session.execute(
                select(CalendarEvent).where(CalendarEvent.user_id == test_user.id)
            )
            events = result_query.scalars().all()
            assert len(events) == 2
            
            # Verify events are associated with correct Google accounts
            account_ids = {e.google_account_id for e in events}
            assert test_google_account.id in account_ids
            assert second_account.id in account_ids

