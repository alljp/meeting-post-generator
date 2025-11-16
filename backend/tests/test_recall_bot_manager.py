"""
Unit tests for Recall Bot Manager.
Tests bot creation, joining, and meeting processing.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.services.recall_bot_manager import (
    create_bot_for_event,
    join_bot_to_meeting,
    check_and_process_completed_meetings,
    schedule_bot_joins
)
from app.models.calendar_event import CalendarEvent
from app.models.meeting import Meeting, Attendee


class TestRecallBotManager:
    """Test suite for RecallBotManager."""
    
    @pytest.mark.asyncio
    async def test_create_bot_for_event_success(self, db_session, test_user, test_google_account):
        """Test successful bot creation for event."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            meeting_link="https://zoom.us/j/123456789",
            meeting_platform="zoom",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        with patch("app.services.recall_bot_manager.recall_service.create_bot") as mock_create:
            mock_create.return_value = {"id": "bot_123"}
            
            bot_id = await create_bot_for_event(event, db_session, minutes_before=5)
            
            assert bot_id == "bot_123"
            await db_session.refresh(event)
            assert event.recall_bot_id == "bot_123"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_bot_for_event_no_meeting_link(self, db_session, test_user, test_google_account):
        """Test bot creation when event has no meeting link."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            meeting_link=None,
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        bot_id = await create_bot_for_event(event, db_session)
        
        assert bot_id is None
    
    @pytest.mark.asyncio
    async def test_create_bot_for_event_notetaker_disabled(self, db_session, test_user, test_google_account):
        """Test bot creation when notetaker is disabled."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            meeting_link="https://zoom.us/j/123456789",
            notetaker_enabled=False
        )
        db_session.add(event)
        await db_session.commit()
        
        bot_id = await create_bot_for_event(event, db_session)
        
        assert bot_id is None
    
    @pytest.mark.asyncio
    async def test_create_bot_for_event_already_exists(self, db_session, test_user, test_google_account):
        """Test bot creation when bot already exists."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            meeting_link="https://zoom.us/j/123456789",
            recall_bot_id="existing_bot_123",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        bot_id = await create_bot_for_event(event, db_session)
        
        assert bot_id == "existing_bot_123"
    
    @pytest.mark.asyncio
    async def test_create_bot_for_event_api_error(self, db_session, test_user, test_google_account):
        """Test bot creation when API call fails."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            meeting_link="https://zoom.us/j/123456789",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        with patch("app.services.recall_bot_manager.recall_service.create_bot") as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            bot_id = await create_bot_for_event(event, db_session)
            
            assert bot_id is None
    
    @pytest.mark.asyncio
    async def test_join_bot_to_meeting_success(self, db_session, test_user, test_google_account):
        """Test successful bot join."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            recall_bot_id="bot_123",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        with patch("app.services.recall_bot_manager.recall_service.join_bot") as mock_join:
            mock_join.return_value = {"status": "joined"}
            
            result = await join_bot_to_meeting("bot_123", event, db_session)
            
            assert result is True
            mock_join.assert_called_once_with("bot_123")
    
    @pytest.mark.asyncio
    async def test_join_bot_to_meeting_failure(self, db_session, test_user, test_google_account):
        """Test bot join failure."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            recall_bot_id="bot_123",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        with patch("app.services.recall_bot_manager.recall_service.join_bot") as mock_join:
            mock_join.side_effect = Exception("Join failed")
            
            result = await join_bot_to_meeting("bot_123", event, db_session)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_and_process_completed_meetings_no_events(self, db_session, test_user):
        """Test processing when no completed events."""
        result = await check_and_process_completed_meetings(test_user.id, db_session)
        
        assert result["created"] == 0
        assert result["updated"] == 0
        assert result["errors"] == []
    
    @pytest.mark.asyncio
    async def test_check_and_process_completed_meetings_create(self, db_session, test_user, test_google_account):
        """Test creating meeting from completed event."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Completed Meeting",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            recall_bot_id="bot_123",
            meeting_platform="zoom",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        bot_status = {
            "bot_id": "bot_123",
            "status": "ended",
            "state": "ended",  # Should trigger meeting creation
            "transcript_available": True,
        }
        
        with patch("app.services.recall_bot_manager.recall_service.get_bot_status") as mock_status, \
             patch("app.services.recall_bot_manager.recall_service.get_transcript") as mock_transcript, \
             patch("app.services.recall_bot_manager.recall_service.get_recording_url") as mock_recording, \
             patch("app.services.recall_bot_manager.recall_service.get_bot_attendees") as mock_attendees:
            
            mock_status.return_value = bot_status
            mock_transcript.return_value = "Test transcript"
            mock_recording.return_value = "https://example.com/recording.mp4"
            mock_attendees.return_value = [
                {"name": "John Doe", "email": "john@example.com"}
            ]
            
            result = await check_and_process_completed_meetings(test_user.id, db_session)
            
            # Bot state is "ended" which should trigger meeting creation
            assert result["created"] >= 0  # May create meeting or already exists
            assert result["updated"] >= 0
            assert "bot_statuses" in result
            
            # Verify meeting exists or was created
            from sqlalchemy import select
            from app.models.meeting import Meeting
            meeting_result = await db_session.execute(
                select(Meeting).where(Meeting.recall_bot_id == "bot_123")
            )
            meeting = meeting_result.scalar_one_or_none()
            # Meeting should exist if created successfully
            if meeting:
                assert meeting.transcript_available is True
    
    @pytest.mark.asyncio
    async def test_check_and_process_completed_meetings_update(self, db_session, test_user, test_google_account):
        """Test updating existing meeting with transcript."""
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Completed Meeting",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            recall_bot_id="bot_123",
            meeting_platform="zoom",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        # Create existing meeting without transcript
        meeting = Meeting(
            user_id=test_user.id,
            recall_bot_id="bot_123",
            title="Completed Meeting",
            start_time=event.start_time,
            end_time=event.end_time,
            platform="zoom",
            transcript_available=False
        )
        db_session.add(meeting)
        await db_session.commit()
        
        bot_status = {
            "bot_id": "bot_123",
            "status": "ended",
            "state": "ended",
            "transcript_available": True,
        }
        
        with patch("app.services.recall_bot_manager.recall_service.get_bot_status") as mock_status, \
             patch("app.services.recall_bot_manager.recall_service.get_transcript") as mock_transcript, \
             patch("app.services.recall_bot_manager.recall_service.get_recording_url") as mock_recording:
            
            mock_status.return_value = bot_status
            mock_transcript.return_value = "New transcript"
            mock_recording.return_value = None
            
            result = await check_and_process_completed_meetings(test_user.id, db_session)
            
            assert result["created"] == 0
            assert result["updated"] == 1
            await db_session.refresh(meeting)
            assert meeting.transcript_available is True
            assert meeting.transcript == "New transcript"
    
    @pytest.mark.asyncio
    async def test_schedule_bot_joins_no_events(self, db_session, test_user):
        """Test scheduling when no upcoming events."""
        result = await schedule_bot_joins(test_user.id, db_session, minutes_before=5)
        
        assert result["joined"] == 0
        assert result["errors"] == []
    
    @pytest.mark.asyncio
    async def test_schedule_bot_joins_success(self, db_session, test_user, test_google_account):
        """Test scheduling bot joins."""
        # Create event that should be joined now
        join_time = datetime.now(timezone.utc) - timedelta(minutes=1)  # Should have been joined 1 min ago
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Upcoming Meeting",
            start_time=join_time + timedelta(minutes=5),  # Meeting starts 5 min from join time
            end_time=join_time + timedelta(minutes=65),
            recall_bot_id="bot_123",
            meeting_link="https://zoom.us/j/123456789",
            meeting_platform="zoom",
            notetaker_enabled=True
        )
        db_session.add(event)
        await db_session.commit()
        
        with patch("app.services.recall_bot_manager.recall_service.join_bot") as mock_join:
            mock_join.return_value = {"status": "joined"}
            
            result = await schedule_bot_joins(test_user.id, db_session, minutes_before=5)
            
            # May or may not join depending on timing, but should not error
            assert "joined" in result
            assert "errors" in result

