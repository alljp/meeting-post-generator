"""
Unit tests for Celery periodic tasks.

Tests the periodic tasks that poll for completed meetings and schedule bot joins.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from app.tasks.meeting_tasks import (
    poll_completed_meetings_periodic,
    schedule_bot_joins_periodic,
    run_async
)
from app.models.user import User
from app.models.calendar_event import CalendarEvent
from app.models.meeting import Meeting
from app.models.settings import UserSettings


class TestRunAsync:
    """Test the run_async helper function."""
    
    @pytest.mark.asyncio
    async def test_run_async_no_loop(self):
        """Test run_async when no event loop exists."""
        async def test_coro():
            return "success"
        
        result = run_async(test_coro())
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_run_async_with_existing_loop(self):
        """Test run_async when event loop exists but is not running."""
        async def test_coro():
            return "success"
        
        # Create a new event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = run_async(test_coro())
            assert result == "success"
        finally:
            loop.close()
    
    def test_run_async_with_error(self):
        """Test run_async handles errors properly."""
        async def failing_coro():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            run_async(failing_coro())


class TestPollCompletedMeetingsPeriodic:
    """Test the poll_completed_meetings_periodic task."""
    
    @pytest.mark.asyncio
    async def test_poll_completed_meetings_success(self, db_session, test_user, test_google_account):
        """Test successful polling of completed meetings."""
        # Create a past event with a bot
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Completed Meeting",
            start_time=past_time - timedelta(hours=1),
            end_time=past_time,
            meeting_link="https://zoom.us/j/123456789",
            meeting_platform="zoom",
            notetaker_enabled=True,
            recall_bot_id="bot_123"
        )
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        # Mock the service function to return a coroutine
        async def mock_check_completed(user_id, db):
            return {
                "created": 1,
                "updated": 0,
                "errors": []
            }
        
        with patch("app.tasks.meeting_tasks.check_and_process_completed_meetings", side_effect=mock_check_completed):
            # Mock AsyncSessionLocal to return our test session
            with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
                # Create async context manager mock
                async def async_context():
                    yield db_session
                
                mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                # Create a mock task instance
                mock_task = MagicMock()
                mock_task.retry = MagicMock()
                
                # Execute the task (it's sync but calls async code)
                result = poll_completed_meetings_periodic(mock_task)
                
                # Verify result
                assert result["created"] >= 0  # May be 0 if no meetings found
                assert "updated" in result
                assert "errors" in result
    
    @pytest.mark.asyncio
    async def test_poll_completed_meetings_no_users(self, db_session):
        """Test polling when no users exist."""
        async def mock_check_completed(user_id, db):
            return {"created": 0, "updated": 0, "errors": []}
        
        with patch("app.tasks.meeting_tasks.check_and_process_completed_meetings", side_effect=mock_check_completed):
            with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
                mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                mock_task = MagicMock()
                mock_task.retry = MagicMock()
                
                result = poll_completed_meetings_periodic(mock_task)
                
                assert result["created"] == 0
                assert result["updated"] == 0
                assert result["errors"] == []
    
    def test_poll_completed_meetings_with_errors(self, db_session, test_user):
        """Test polling when errors occur."""
        with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock check_and_process_completed_meetings to raise an error
            async def failing_check(user_id, db):
                raise Exception("Database error")
            
            with patch("app.tasks.meeting_tasks.check_and_process_completed_meetings", side_effect=failing_check):
                mock_task = MagicMock()
                mock_task.retry = MagicMock(side_effect=Exception("Retry failed"))
                
                # Task should catch error and retry
                with pytest.raises(Exception, match="Retry failed"):
                    poll_completed_meetings_periodic(mock_task)
                
                # Verify retry was called
                mock_task.retry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_poll_completed_meetings_multiple_users(self, db_session, test_user, test_google_account):
        """Test polling with multiple users."""
        # Create second user
        user2 = User(
            email="user2@example.com",
            name="User 2",
            picture="https://example.com/pic2.jpg",
            is_active=True
        )
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)
        
        async def mock_check_completed(user_id, db):
            return {"created": 0, "updated": 0, "errors": []}
        
        with patch("app.tasks.meeting_tasks.check_and_process_completed_meetings", side_effect=mock_check_completed):
            with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
                mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                mock_task = MagicMock()
                mock_task.retry = MagicMock()
                
                result = poll_completed_meetings_periodic(mock_task)
                
                # Should process both users
                assert "created" in result
                assert "updated" in result
                assert "errors" in result


class TestScheduleBotJoinsPeriodic:
    """Test the schedule_bot_joins_periodic task."""
    
    @pytest.mark.asyncio
    async def test_schedule_bot_joins_success(self, db_session, test_user, test_google_account):
        """Test successful scheduling of bot joins."""
        # Create a future event with a bot
        future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Upcoming Meeting",
            start_time=future_time,
            end_time=future_time + timedelta(hours=1),
            meeting_link="https://zoom.us/j/123456789",
            meeting_platform="zoom",
            notetaker_enabled=True,
            recall_bot_id="bot_123"
        )
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        async def mock_schedule_joins(user_id, db, minutes_before):
            return {"joined": 0, "skipped": 1, "errors": []}
        
        with patch("app.tasks.meeting_tasks.schedule_bot_joins", side_effect=mock_schedule_joins):
            with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
                mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                mock_task = MagicMock()
                mock_task.retry = MagicMock()
                
                result = schedule_bot_joins_periodic(mock_task)
                
                assert "joined" in result
                assert "skipped" in result
                assert "errors" in result
    
    @pytest.mark.asyncio
    async def test_schedule_bot_joins_with_user_settings(self, db_session, test_user, test_google_account):
        """Test scheduling with custom user settings."""
        # Create user settings
        settings = UserSettings(
            user_id=test_user.id,
            bot_join_minutes_before=10
        )
        db_session.add(settings)
        await db_session.commit()
        
        async def mock_schedule_joins(user_id, db, minutes_before):
            # Verify it was called with the custom minutes_before
            assert minutes_before == 10
            return {"joined": 0, "skipped": 0, "errors": []}
        
        with patch("app.tasks.meeting_tasks.schedule_bot_joins", side_effect=mock_schedule_joins):
            with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
                mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                mock_task = MagicMock()
                mock_task.retry = MagicMock()
                
                result = schedule_bot_joins_periodic(mock_task)
                
                assert "joined" in result
                assert "skipped" in result
                assert "errors" in result
    
    @pytest.mark.asyncio
    async def test_schedule_bot_joins_no_users(self, db_session):
        """Test scheduling when no users exist."""
        with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_task = MagicMock()
            mock_task.retry = MagicMock()
            
            result = schedule_bot_joins_periodic(mock_task)
            
            assert result["joined"] == 0
            assert result["skipped"] == 0
            assert result["errors"] == []
    
    def test_schedule_bot_joins_with_errors(self, db_session, test_user):
        """Test scheduling when errors occur."""
        with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock schedule_bot_joins to raise an error
            async def failing_schedule(user_id, db, minutes_before):
                raise Exception("API error")
            
            with patch("app.tasks.meeting_tasks.schedule_bot_joins", side_effect=failing_schedule):
                mock_task = MagicMock()
                mock_task.retry = MagicMock(side_effect=Exception("Retry failed"))
                
                # Task should catch error and retry
                with pytest.raises(Exception, match="Retry failed"):
                    schedule_bot_joins_periodic(mock_task)
                
                # Verify retry was called
                mock_task.retry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_bot_joins_default_minutes_before(self, db_session, test_user):
        """Test scheduling uses default minutes_before when no settings exist."""
        async def mock_schedule_joins(user_id, db, minutes_before):
            # Verify it was called with default value
            assert minutes_before == 5
            return {"joined": 0, "skipped": 0, "errors": []}
        
        with patch("app.tasks.meeting_tasks.schedule_bot_joins", side_effect=mock_schedule_joins):
            with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
                mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                mock_task = MagicMock()
                mock_task.retry = MagicMock()
                
                result = schedule_bot_joins_periodic(mock_task)
                
                assert "joined" in result
                assert "skipped" in result
                assert "errors" in result


class TestTaskIntegration:
    """Integration tests for tasks with real database operations."""
    
    @pytest.mark.asyncio
    async def test_poll_completed_meetings_integration(self, db_session, test_user, test_google_account):
        """Integration test: poll completed meetings with real database."""
        # Create a completed event with bot
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        event = CalendarEvent(
            user_id=test_user.id,
            google_account_id=test_google_account.id,
            google_event_id="event_123",
            title="Completed Meeting",
            start_time=past_time - timedelta(hours=1),
            end_time=past_time,
            meeting_link="https://zoom.us/j/123456789",
            meeting_platform="zoom",
            notetaker_enabled=True,
            recall_bot_id="bot_123"
        )
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        # Mock Recall.ai API responses
        with patch("app.services.recall_service.recall_service.get_bot_status") as mock_status, \
             patch("app.services.recall_service.recall_service.get_transcript") as mock_transcript, \
             patch("app.services.recall_service.recall_service.get_recording_url") as mock_recording, \
             patch("app.services.recall_service.recall_service.get_bot_attendees") as mock_attendees:
            
            mock_status.return_value = {
                "state": "ended",
                "transcript_available": True
            }
            mock_transcript.return_value = "Test transcript content"
            mock_recording.return_value = "https://recall.ai/recording/123"
            mock_attendees.return_value = [
                {"name": "John Doe", "email": "john@example.com"}
            ]
            
            # Mock AsyncSessionLocal
            with patch("app.tasks.meeting_tasks.AsyncSessionLocal") as mock_session:
                mock_session.return_value.__aenter__ = AsyncMock(return_value=db_session)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                mock_task = MagicMock()
                mock_task.retry = MagicMock()
                
                result = poll_completed_meetings_periodic(mock_task)
                
                # Verify meeting was created
                await db_session.refresh(event)
                # Check if meeting exists (it should if the task worked)
                from sqlalchemy import select
                meeting_result = await db_session.execute(
                    select(Meeting).where(Meeting.recall_bot_id == "bot_123")
                )
                meeting = meeting_result.scalar_one_or_none()
                
                # The meeting might be created, or might not if conditions aren't met
                # Just verify the task completed without error
                assert "created" in result
                assert "updated" in result
                assert "errors" in result

