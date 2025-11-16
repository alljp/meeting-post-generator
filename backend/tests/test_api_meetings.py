"""
Unit tests for Meetings API endpoints.
Tests meeting listing, details, transcript, email generation, and post generation.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.meeting import Meeting, Attendee
from app.models.generated_post import GeneratedPost, PostStatus
from app.utils.jwt import create_access_token


class TestMeetingsAPI:
    """Test suite for Meetings API endpoints."""
    
    @pytest.fixture
    def auth_token(self, test_user):
        """Create auth token for test user."""
        return create_access_token({"sub": str(test_user.id)})
    
    @pytest.fixture
    async def test_attendee(self, db_session):
        """Create a test attendee."""
        attendee = Attendee(
            name="John Doe",
            email="john@example.com"
        )
        db_session.add(attendee)
        await db_session.commit()
        await db_session.refresh(attendee)
        return attendee
    
    @pytest.fixture
    async def test_meeting(self, db_session, test_user, test_attendee):
        """Create a test meeting (past meeting)."""
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select, insert
        from app.models.meeting import meeting_attendees
        
        # Set attendees before adding to avoid lazy loading
        meeting = Meeting(
            user_id=test_user.id,
            recall_bot_id="bot_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            platform="zoom",
            transcript="This is a test transcript.",
            transcript_available=True,
            recording_url="https://example.com/recording.mp4",
            attendees=[test_attendee]  # Set before adding to session
        )
        db_session.add(meeting)
        await db_session.commit()
        
        # Refresh with eager loading to avoid lazy load issues
        result = await db_session.execute(
            select(Meeting)
            .where(Meeting.id == meeting.id)
            .options(selectinload(Meeting.attendees))
        )
        meeting = result.scalar_one()
        return meeting
    
    @pytest.mark.asyncio
    async def test_list_meetings_success(
        self, client: AsyncClient, test_user, test_meeting, auth_token
    ):
        """Test listing past meetings."""
        response = await client.get(
            "/api/v1/meetings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["id"] == test_meeting.id
        assert data[0]["title"] == "Test Meeting"
        assert "attendees" in data[0]
    
    @pytest.mark.asyncio
    async def test_list_meetings_with_pagination(
        self, client: AsyncClient, test_user, test_meeting, auth_token
    ):
        """Test listing meetings with pagination."""
        response = await client.get(
            "/api/v1/meetings?limit=10&offset=0",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    @pytest.mark.asyncio
    async def test_list_meetings_empty(self, client: AsyncClient, test_user, auth_token):
        """Test listing meetings when none exist."""
        response = await client.get(
            "/api/v1/meetings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_list_meetings_only_past(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test that only past meetings are returned."""
        # Create a future meeting
        future_meeting = Meeting(
            user_id=test_user.id,
            recall_bot_id="bot_future",
            title="Future Meeting",
            start_time=datetime.now(timezone.utc) + timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            platform="zoom",
            transcript_available=False
        )
        db_session.add(future_meeting)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/meetings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Future meeting should not be in the list
        meeting_ids = [m["id"] for m in data]
        assert future_meeting.id not in meeting_ids
    
    @pytest.mark.asyncio
    async def test_get_meeting_success(
        self, client: AsyncClient, test_user, test_meeting, auth_token
    ):
        """Test getting meeting details."""
        response = await client.get(
            f"/api/v1/meetings/{test_meeting.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_meeting.id
        assert data["title"] == "Test Meeting"
        assert data["platform"] == "zoom"
        assert "attendees" in data
        assert len(data["attendees"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_meeting_not_found(self, client: AsyncClient, test_user, auth_token):
        """Test getting non-existent meeting."""
        response = await client.get(
            "/api/v1/meetings/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_meeting_unauthorized(self, client: AsyncClient, db_session, test_user, test_meeting):
        """Test getting meeting of another user."""
        # Create another user
        from app.models.user import User
        other_user = User(
            email="other@example.com",
            name="Other User"
        )
        db_session.add(other_user)
        await db_session.commit()
        
        other_token = create_access_token({"sub": str(other_user.id)})
        
        response = await client.get(
            f"/api/v1/meetings/{test_meeting.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 404  # Should not reveal existence
    
    @pytest.mark.asyncio
    async def test_get_transcript_success(
        self, client: AsyncClient, test_user, test_meeting, auth_token
    ):
        """Test getting meeting transcript."""
        response = await client.get(
            f"/api/v1/meetings/{test_meeting.id}/transcript",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "transcript" in data
        assert data["transcript"] == "This is a test transcript."
    
    @pytest.mark.asyncio
    async def test_get_transcript_not_available(
        self, client: AsyncClient, db_session, test_user, auth_token
    ):
        """Test getting transcript when not available."""
        meeting = Meeting(
            user_id=test_user.id,
            recall_bot_id="bot_no_transcript",
            title="No Transcript Meeting",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            platform="zoom",
            transcript_available=False
        )
        db_session.add(meeting)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/meetings/{meeting.id}/transcript",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not available" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_email_success(
        self, client: AsyncClient, test_user, test_meeting, test_attendee, auth_token
    ):
        """Test generating and getting email."""
        with patch("app.services.ai.service.ai_service.generate_follow_up_email") as mock_generate:
            # Mock returns OpenAI response format (list with text)
            mock_generate.return_value = "Subject: Follow-up\n\nThis is the email content."
            
            response = await client.get(
                f"/api/v1/meetings/{test_meeting.id}/email",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            # Check for any part of the email content
            assert "Follow-up" in data["email"] or "follow" in data["email"].lower()
            
            # Verify AI service was called
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1]["transcript"] == "This is a test transcript."
            assert call_args[1]["meeting_title"] == "Test Meeting"
    
    @pytest.mark.asyncio
    async def test_get_email_already_generated(
        self, client: AsyncClient, db_session, test_user, test_meeting, auth_token
    ):
        """Test getting already generated email."""
        test_meeting.email = "Subject: Existing Email\n\nExisting content."
        test_meeting.email_generated_at = datetime.now(timezone.utc)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/meetings/{test_meeting.id}/email",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Existing Email" in data["email"]
    
    @pytest.mark.asyncio
    async def test_get_email_no_transcript(
        self, client: AsyncClient, db_session, test_user, auth_token
    ):
        """Test getting email when transcript not available."""
        meeting = Meeting(
            user_id=test_user.id,
            recall_bot_id="bot_no_transcript",
            title="No Transcript",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            platform="zoom",
            transcript_available=False
        )
        db_session.add(meeting)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/meetings/{meeting.id}/email",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "transcript not available" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_posts_success(
        self, client: AsyncClient, db_session, test_user, test_meeting, auth_token
    ):
        """Test getting generated posts."""
        post1 = GeneratedPost(
            meeting_id=test_meeting.id,
            platform="linkedin",
            content="LinkedIn post content",
            status=PostStatus.DRAFT
        )
        post2 = GeneratedPost(
            meeting_id=test_meeting.id,
            platform="facebook",
            content="Facebook post content",
            status=PostStatus.DRAFT
        )
        db_session.add_all([post1, post2])
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/meetings/{test_meeting.id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        assert len(data["posts"]) == 2
        assert data["posts"][0]["platform"] in ["linkedin", "facebook"]
    
    @pytest.mark.asyncio
    async def test_get_posts_empty(self, client: AsyncClient, test_user, test_meeting, auth_token):
        """Test getting posts when none exist."""
        response = await client.get(
            f"/api/v1/meetings/{test_meeting.id}/posts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["posts"] == []
    
    @pytest.mark.asyncio
    async def test_generate_post_linkedin_success(
        self, client: AsyncClient, test_user, test_meeting, test_attendee, auth_token
    ):
        """Test generating LinkedIn post."""
        with patch("app.services.ai.service.ai_service.generate_social_media_post") as mock_generate:
            mock_generate.return_value = "Excited to share insights from our meeting! #LinkedIn"
            
            response = await client.post(
                f"/api/v1/meetings/{test_meeting.id}/generate-post?platform=linkedin",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["platform"] == "linkedin"
            assert data["status"] == "draft"
            assert "content" in data
            assert "message" in data
            
            # Verify AI service was called
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1]["platform"] == "linkedin"
            assert call_args[1]["transcript"] == "This is a test transcript."
    
    @pytest.mark.asyncio
    async def test_generate_post_facebook_success(
        self, client: AsyncClient, test_user, test_meeting, auth_token
    ):
        """Test generating Facebook post."""
        with patch("app.services.ai.service.ai_service.generate_social_media_post") as mock_generate:
            mock_generate.return_value = "Great meeting today! #Facebook"
            
            response = await client.post(
                f"/api/v1/meetings/{test_meeting.id}/generate-post?platform=facebook",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["platform"] == "facebook"
            assert data["status"] == "draft"
    
    @pytest.mark.asyncio
    async def test_generate_post_invalid_platform(
        self, client: AsyncClient, test_user, test_meeting, auth_token
    ):
        """Test generating post with invalid platform."""
        response = await client.post(
            f"/api/v1/meetings/{test_meeting.id}/generate-post?platform=twitter",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "platform must be" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_post_no_transcript(
        self, client: AsyncClient, db_session, test_user, auth_token
    ):
        """Test generating post when transcript not available."""
        meeting = Meeting(
            user_id=test_user.id,
            recall_bot_id="bot_no_transcript",
            title="No Transcript",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            platform="zoom",
            transcript_available=False
        )
        db_session.add(meeting)
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/meetings/{meeting.id}/generate-post?platform=linkedin",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "transcript not available" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_post_with_automation(
        self, client: AsyncClient, db_session, test_user, test_meeting, auth_token
    ):
        """Test generating post with automation."""
        from app.models.automation import Automation
        
        automation = Automation(
            user_id=test_user.id,
            name="Test Automation",
            platform="linkedin",
            prompt_template="Create a post: {transcript} for {meeting_title}",
            is_active=True
        )
        db_session.add(automation)
        await db_session.commit()
        
        with patch("app.services.ai.service.ai_service.generate_social_media_post") as mock_generate:
            mock_generate.return_value = "Generated post"
            
            response = await client.post(
                f"/api/v1/meetings/{test_meeting.id}/generate-post?platform=linkedin",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            # Verify automation was used
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1]["custom_prompt"] is not None
    
    @pytest.mark.asyncio
    async def test_list_meetings_unauthorized(self, client: AsyncClient):
        """Test listing meetings without authentication."""
        response = await client.get("/api/v1/meetings")
        assert response.status_code == 401

