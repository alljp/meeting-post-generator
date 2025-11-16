"""
Unit tests for Recall API endpoints.
Tests bot creation, status checking, polling, and scheduling.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from app.models.calendar_event import CalendarEvent
from app.models.meeting import Meeting
from app.models.settings import UserSettings
from app.utils.jwt import create_access_token
from sqlalchemy import select


class TestRecallAPI:
    """Test suite for Recall API endpoints."""
    
    @pytest.fixture
    def auth_token(self, test_user):
        """Create auth token for test user."""
        return create_access_token({"sub": str(test_user.id)})
    
    @pytest.fixture
    async def test_settings(self, db_session, test_user):
        """Create test user settings."""
        settings = UserSettings(
            user_id=test_user.id,
            bot_join_minutes_before=5
        )
        db_session.add(settings)
        await db_session.commit()
        await db_session.refresh(settings)
        return settings
    
    @pytest.fixture
    async def test_event_with_meeting_link(
        self, db_session, test_user, test_google_account, test_settings
    ):
        """Create a test calendar event with meeting link and notetaker enabled."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="test_event_with_link",
            title="Test Meeting",
            description="Test meeting with Zoom link",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            location="Test Location",
            meeting_link="https://zoom.us/j/123456789",
            meeting_platform="zoom",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        return event
    
    @pytest.mark.asyncio
    async def test_create_bot_success(
        self, client: AsyncClient, test_user, auth_token, test_event_with_meeting_link, db_session
    ):
        """Test creating a bot for a calendar event."""
        mock_bot_id = "bot_12345"
        
        with patch("app.api.v1.recall.create_bot_for_event") as mock_create:
            mock_create.return_value = mock_bot_id
            
            response = await client.post(
                f"/api/v1/recall/events/{test_event_with_meeting_link.id}/create-bot",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            # The bot_id comes from the mocked function
            assert data["bot_id"] == mock_bot_id
            assert "created successfully" in data["message"].lower()
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_bot_event_not_found(self, client: AsyncClient, test_user, auth_token):
        """Test creating a bot for non-existent event."""
        response = await client.post(
            "/api/v1/recall/events/99999/create-bot",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        detail = response.json()["detail"].lower()
        assert "not found" in detail
    
    @pytest.mark.asyncio
    async def test_create_bot_no_meeting_link(
        self, client: AsyncClient, test_user, auth_token, test_calendar_event, db_session
    ):
        """Test creating a bot for event without meeting link."""
        # Update event to have no meeting link
        test_calendar_event.meeting_link = None
        test_calendar_event.notetaker_enabled = True
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/recall/events/{test_calendar_event.id}/create-bot",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "meeting link" in detail
    
    @pytest.mark.asyncio
    async def test_create_bot_notetaker_disabled(
        self, client: AsyncClient, test_user, auth_token, test_event_with_meeting_link, db_session
    ):
        """Test creating a bot when notetaker is disabled."""
        test_event_with_meeting_link.notetaker_enabled = False
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/recall/events/{test_event_with_meeting_link.id}/create-bot",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "notetaker" in detail or "not enabled" in detail
    
    @pytest.mark.asyncio
    async def test_create_bot_unauthorized(self, client: AsyncClient, test_event_with_meeting_link):
        """Test creating a bot without authentication."""
        response = await client.post(
            f"/api/v1/recall/events/{test_event_with_meeting_link.id}/create-bot"
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_bot_wrong_user(
        self, client: AsyncClient, db_session, test_user, auth_token
    ):
        """Test creating a bot for another user's event."""
        # Create another user and event
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
            meeting_link="https://zoom.us/j/999999",
            meeting_platform="zoom",
            notetaker_enabled=True
        )
        db_session.add(other_event)
        await db_session.commit()
        await db_session.refresh(other_event)
        
        response = await client.post(
            f"/api/v1/recall/events/{other_event.id}/create-bot",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404  # Should not find it (belongs to different user)
    
    @pytest.mark.asyncio
    async def test_create_bot_failure(
        self, client: AsyncClient, test_user, auth_token, test_event_with_meeting_link
    ):
        """Test bot creation failure."""
        with patch("app.api.v1.recall.create_bot_for_event") as mock_create:
            mock_create.return_value = None  # Bot creation failed
            
            response = await client.post(
                f"/api/v1/recall/events/{test_event_with_meeting_link.id}/create-bot",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # When create_bot_for_event returns None, the endpoint should return 500
            assert response.status_code == 500
            detail = response.json()["detail"].lower()
            assert "failed" in detail
    
    @pytest.mark.asyncio
    async def test_get_bot_status_success(
        self, client: AsyncClient, test_user, auth_token, test_event_with_meeting_link, db_session
    ):
        """Test getting bot status."""
        bot_id = "bot_12345"
        test_event_with_meeting_link.recall_bot_id = bot_id
        await db_session.commit()
        
        mock_status = {
            "bot_id": bot_id,
            "status": "active",
            "state": "joined",
            "transcript_available": True,
            "recording_available": False
        }
        
        with patch("app.services.recall_service.recall_service.get_bot_status") as mock_get_status:
            mock_get_status.return_value = mock_status
            
            response = await client.get(
                f"/api/v1/recall/bot/{bot_id}/status",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["bot_id"] == bot_id
            assert data["status"] == "active"
            assert data["state"] == "joined"
            assert data["transcript_available"] is True
    
    @pytest.mark.asyncio
    async def test_get_bot_status_not_found(self, client: AsyncClient, test_user, auth_token):
        """Test getting status for non-existent bot."""
        response = await client.get(
            "/api/v1/recall/bot/nonexistent_bot/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        detail = response.json()["detail"].lower()
        assert "not found" in detail
    
    @pytest.mark.asyncio
    async def test_get_bot_status_unauthorized(self, client: AsyncClient):
        """Test getting bot status without authentication."""
        response = await client.get("/api/v1/recall/bot/bot_123/status")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_bot_status_wrong_user(
        self, client: AsyncClient, db_session, test_user, auth_token
    ):
        """Test getting bot status for another user's bot."""
        # Create another user with event and bot
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
            meeting_link="https://zoom.us/j/999999",
            meeting_platform="zoom",
            recall_bot_id="other_bot_123"
        )
        db_session.add(other_event)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/recall/bot/other_bot_123/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404  # Should not find it (belongs to different user)
    
    @pytest.mark.asyncio
    async def test_poll_completed_meetings_success(
        self, client: AsyncClient, test_user, auth_token, test_event_with_meeting_link, db_session
    ):
        """Test polling for completed meetings."""
        bot_id = "bot_12345"
        test_event_with_meeting_link.recall_bot_id = bot_id
        # Set end_time in the past so it's considered completed
        test_event_with_meeting_link.end_time = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.commit()
        
        mock_result = {
            "created": 1,
            "updated": 0,
            "errors": []
        }
        
        with patch("app.api.v1.recall.check_and_process_completed_meetings") as mock_poll:
            mock_poll.return_value = mock_result
            
            response = await client.post(
                "/api/v1/recall/poll-completed",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["created"] == 1
            assert data["updated"] == 0
            mock_poll.assert_called_once_with(test_user.id, db_session)
    
    @pytest.mark.asyncio
    async def test_poll_completed_meetings_unauthorized(self, client: AsyncClient):
        """Test polling without authentication."""
        response = await client.post("/api/v1/recall/poll-completed")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_schedule_joins_success(
        self, client: AsyncClient, test_user, auth_token, test_settings, db_session
    ):
        """Test scheduling bot joins."""
        mock_result = {
            "joined": 2,
            "skipped": 3,
            "errors": []
        }
        
        with patch("app.api.v1.recall.schedule_bot_joins") as mock_schedule:
            mock_schedule.return_value = mock_result
            
            response = await client.post(
                "/api/v1/recall/schedule-joins",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["joined"] == 2
            assert data["skipped"] == 3
            # Verify it was called with correct minutes_before from settings
            mock_schedule.assert_called_once_with(test_user.id, db_session, 5)
    
    @pytest.mark.asyncio
    async def test_schedule_joins_default_minutes(
        self, client: AsyncClient, test_user, auth_token, db_session
    ):
        """Test scheduling bot joins with default minutes_before when no settings exist."""
        mock_result = {
            "joined": 0,
            "skipped": 0,
            "errors": []
        }
        
        with patch("app.api.v1.recall.schedule_bot_joins") as mock_schedule:
            mock_schedule.return_value = mock_result
            
            response = await client.post(
                "/api/v1/recall/schedule-joins",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            # Verify default value of 5 minutes was used
            mock_schedule.assert_called_once_with(test_user.id, db_session, 5)
    
    @pytest.mark.asyncio
    async def test_schedule_joins_unauthorized(self, client: AsyncClient):
        """Test scheduling joins without authentication."""
        response = await client.post("/api/v1/recall/schedule-joins")
        assert response.status_code == 401

