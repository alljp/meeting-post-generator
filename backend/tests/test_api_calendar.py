"""
Unit tests for Calendar API endpoints.
Tests calendar event listing, syncing, and notetaker toggling.
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from app.models.calendar_event import CalendarEvent
from app.utils.jwt import create_access_token


class TestCalendarAPI:
    """Test suite for Calendar API endpoints."""
    
    @pytest.fixture
    def auth_token(self, test_user):
        """Create auth token for test user."""
        return create_access_token({"sub": str(test_user.id)})
    
    @pytest.mark.asyncio
    async def test_list_events_success(self, client: AsyncClient, test_user, test_calendar_event, auth_token):
        """Test listing calendar events."""
        response = await client.get(
            "/api/v1/calendar/events",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "title" in data[0]
            assert "start_time" in data[0]
    
    @pytest.mark.asyncio
    async def test_list_events_with_limit(self, client: AsyncClient, test_user, auth_token):
        """Test listing events with limit parameter."""
        response = await client.get(
            "/api/v1/calendar/events?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    @pytest.mark.asyncio
    async def test_list_events_unauthorized(self, client: AsyncClient):
        """Test listing events without authentication."""
        response = await client.get("/api/v1/calendar/events")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_toggle_notetaker_enable(self, client: AsyncClient, test_user, test_calendar_event, auth_token, db_session):
        """Test enabling notetaker for an event."""
        response = await client.patch(
            f"/api/v1/calendar/events/{test_calendar_event.id}/notetaker?enabled=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notetaker_enabled"] is True
        
        # Verify in database
        await db_session.refresh(test_calendar_event)
        assert test_calendar_event.notetaker_enabled is True
    
    @pytest.mark.asyncio
    async def test_toggle_notetaker_disable(self, client: AsyncClient, test_user, test_calendar_event, auth_token, db_session):
        """Test disabling notetaker for an event."""
        # First enable it
        test_calendar_event.notetaker_enabled = True
        await db_session.commit()
        
        response = await client.patch(
            f"/api/v1/calendar/events/{test_calendar_event.id}/notetaker?enabled=false",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notetaker_enabled"] is False
    
    @pytest.mark.asyncio
    async def test_toggle_notetaker_event_not_found(self, client: AsyncClient, test_user, auth_token):
        """Test toggling notetaker for non-existent event."""
        response = await client.patch(
            "/api/v1/calendar/events/99999/notetaker?enabled=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_sync_calendar_success(self, client: AsyncClient, test_user, test_google_account, auth_token):
        """Test manual calendar sync."""
        # Mock the sync function to avoid Google API calls
        from unittest.mock import AsyncMock
        with patch("app.services.calendar.service.calendar_service.sync_calendar_events_for_user", new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = {
                "synced": 5,
                "created": 3,
                "updated": 2,
                "errors": [],
                "create_bots": True,
                "minutes_before": 5,
                "bots_created": [],
                "events": []
            }
            
            response = await client.post(
                "/api/v1/calendar/sync",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["synced"] == 5
            assert data["created"] == 3
            assert data["updated"] == 2
    
    @pytest.mark.asyncio
    async def test_sync_calendar_unauthorized(self, client: AsyncClient):
        """Test calendar sync without authentication."""
        response = await client.post("/api/v1/calendar/sync")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_events_filters_past_events(
        self, client: AsyncClient, test_user, auth_token, db_session, test_google_account
    ):
        """Test that past events are filtered out."""
        # Create a past event
        past_event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="past_event",
            title="Past Meeting",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc) - timedelta(hours=23),
            meeting_link="https://zoom.us/j/111",
            meeting_platform="zoom"
        )
        db_session.add(past_event)
        
        # Create a future event
        future_event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="future_event",
            title="Future Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(days=1),
            end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
            meeting_link="https://zoom.us/j/222",
            meeting_platform="zoom"
        )
        db_session.add(future_event)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/calendar/events",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should only return future events
        event_ids = [e["id"] for e in data]
        assert future_event.id in event_ids
        assert past_event.id not in event_ids
    
    @pytest.mark.asyncio
    async def test_list_events_with_days_ahead(
        self, client: AsyncClient, test_user, auth_token, db_session, test_google_account
    ):
        """Test listing events with days_ahead parameter."""
        # Create event far in the future
        far_future_event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="far_future",
            title="Far Future Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(days=60),
            end_time=datetime.now(timezone.utc) + timedelta(days=60, hours=1),
            meeting_link="https://zoom.us/j/333",
            meeting_platform="zoom"
        )
        db_session.add(far_future_event)
        await db_session.commit()
        
        # Request events with 30 days ahead (should not include far future event)
        response = await client.get(
            "/api/v1/calendar/events?days_ahead=30",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        event_ids = [e["id"] for e in data]
        assert far_future_event.id not in event_ids
    
    @pytest.mark.asyncio
    async def test_toggle_notetaker_wrong_user(
        self, client: AsyncClient, db_session, test_user, auth_token
    ):
        """Test toggling notetaker for another user's event."""
        from app.models.user import User, GoogleAccount
        
        other_user = User(
            email="other@example.com",
            name="Other User",
            is_active=True
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)
        
        other_account = GoogleAccount(
            user_id=other_user.id,
            google_email="other@gmail.com",
            access_token="token",
            is_active=True
        )
        db_session.add(other_account)
        await db_session.commit()
        await db_session.refresh(other_account)
        
        other_event = CalendarEvent(
            user_id=other_user.id,
            google_account_id=other_account.id,
            google_event_id="other_event",
            title="Other Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            meeting_link="https://zoom.us/j/999",
            meeting_platform="zoom"
        )
        db_session.add(other_event)
        await db_session.commit()
        await db_session.refresh(other_event)
        
        response = await client.patch(
            f"/api/v1/calendar/events/{other_event.id}/notetaker?enabled=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404  # Should not find it (belongs to different user)

