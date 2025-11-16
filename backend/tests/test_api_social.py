"""
Unit tests for Social Media API endpoints.
Tests social account management and posting functionality.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from app.models.social_account import SocialAccount, SocialPlatform
from app.models.generated_post import GeneratedPost, PostStatus
from app.models.meeting import Meeting
from app.utils.jwt import create_access_token


class TestSocialAPI:
    """Test suite for Social API endpoints."""
    
    @pytest.fixture
    def auth_token(self, test_user):
        """Create auth token for test user."""
        return create_access_token({"sub": str(test_user.id)})
    
    @pytest.fixture
    async def test_social_account(self, db_session, test_user):
        """Create a test social account."""
        from datetime import datetime, timezone, timedelta
        # Ensure timezone-aware datetime
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.LINKEDIN,
            account_id="linkedin_123",
            account_name="Test User LinkedIn",
            access_token="test_access_token",
            token_expires_at=expires_at,
            is_active=True
        )
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        
        # Ensure token_expires_at is timezone-aware after refresh (SQLite might lose timezone)
        if account.token_expires_at and account.token_expires_at.tzinfo is None:
            account.token_expires_at = account.token_expires_at.replace(tzinfo=timezone.utc)
        
        return account
    
    @pytest.fixture
    async def test_meeting_for_post(self, db_session, test_user):
        """Create a test meeting for post generation."""
        from app.models.meeting import Meeting
        meeting = Meeting(
            user_id=test_user.id,
            recall_bot_id="bot_123",
            title="Test Meeting",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            platform="zoom",
            transcript="Test transcript",
            transcript_available=True
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)
        return meeting
    
    @pytest.fixture
    async def test_generated_post(self, db_session, test_meeting_for_post):
        """Create a test generated post."""
        post = GeneratedPost(
            meeting_id=test_meeting_for_post.id,
            platform="linkedin",
            content="Test LinkedIn post content",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        return post
    
    @pytest.mark.asyncio
    async def test_list_social_accounts_success(
        self, client: AsyncClient, test_user, test_social_account, auth_token
    ):
        """Test listing social accounts."""
        response = await client.get(
            "/api/v1/social/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["platform"] == "linkedin"
        assert data[0]["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_list_social_accounts_empty(self, client: AsyncClient, test_user, auth_token):
        """Test listing accounts when none exist."""
        response = await client.get(
            "/api/v1/social/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_connect_linkedin(self, client: AsyncClient, test_user, auth_token):
        """Test LinkedIn connection initiation."""
        from unittest.mock import MagicMock
        mock_provider = MagicMock()
        mock_provider.get_authorization_url.return_value = "https://linkedin.com/oauth?state=test"
        
        with patch("app.api.v1.social.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/social/linkedin/connect",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            mock_factory.assert_called_once_with("linkedin")
            mock_provider.get_authorization_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_facebook(self, client: AsyncClient, test_user, auth_token):
        """Test Facebook connection initiation."""
        from unittest.mock import MagicMock
        mock_provider = MagicMock()
        mock_provider.get_authorization_url.return_value = "https://facebook.com/oauth?state=test"
        
        with patch("app.api.v1.social.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/social/facebook/connect",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            mock_factory.assert_called_once_with("facebook")
            mock_provider.get_authorization_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_social_account_success(
        self, client: AsyncClient, test_user, test_social_account, auth_token, db_session
    ):
        """Test disconnecting a social account."""
        response = await client.delete(
            f"/api/v1/social/accounts/{test_social_account.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "disconnected successfully" in data["message"].lower()
        
        await db_session.refresh(test_social_account)
        assert test_social_account.is_active is False
    
    @pytest.mark.asyncio
    async def test_disconnect_social_account_not_found(
        self, client: AsyncClient, test_user, auth_token
    ):
        """Test disconnecting non-existent account."""
        response = await client.delete(
            "/api/v1/social/accounts/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_post_to_social_linkedin_success(
        self, client: AsyncClient, test_user, test_social_account, 
        test_generated_post, auth_token, db_session
    ):
        """Test posting to LinkedIn."""
        from unittest.mock import MagicMock, AsyncMock
        mock_poster = AsyncMock()
        mock_poster.post.return_value = {
            "post_id": "urn:li:ugcPost:123456",
            "platform": "linkedin",
            "success": True
        }
        
        with patch("app.api.v1.social.SocialMediaPosterFactory.create") as mock_factory:
            mock_factory.return_value = mock_poster
            
            response = await client.post(
                f"/api/v1/social/posts/{test_generated_post.id}/post",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "published to linkedin successfully" in data["message"].lower()
            assert data["status"] == "posted"
            
            await db_session.refresh(test_generated_post)
            assert test_generated_post.status == PostStatus.POSTED
            assert test_generated_post.post_id == "urn:li:ugcPost:123456"
    
    @pytest.mark.asyncio
    async def test_post_to_social_facebook_success(
        self, client: AsyncClient, db_session, test_user, test_meeting_for_post, auth_token
    ):
        """Test posting to Facebook."""
        # Create Facebook account and post
        facebook_account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.FACEBOOK,
            account_id="facebook_123",
            account_name="Test User Facebook",
            access_token="test_facebook_token",
            token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True
        )
        db_session.add(facebook_account)
        
        post = GeneratedPost(
            meeting_id=test_meeting_for_post.id,
            platform="facebook",
            content="Test Facebook post",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        
        from unittest.mock import MagicMock, AsyncMock
        mock_poster = AsyncMock()
        mock_poster.post.return_value = {
            "post_id": "123456789",
            "platform": "facebook",
            "success": True
        }
        
        with patch("app.api.v1.social.SocialMediaPosterFactory.create") as mock_factory:
            mock_factory.return_value = mock_poster
            
            response = await client.post(
                f"/api/v1/social/posts/{post.id}/post",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "published to facebook successfully" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_post_to_social_no_account(
        self, client: AsyncClient, test_user, test_generated_post, auth_token
    ):
        """Test posting when no social account connected."""
        response = await client.post(
            f"/api/v1/social/posts/{test_generated_post.id}/post",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "no active" in response.json()["detail"].lower()
        assert "account connected" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_post_to_social_expired_token(
        self, client: AsyncClient, db_session, test_user, test_meeting_for_post, auth_token
    ):
        """Test posting with expired token."""
        account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.LINKEDIN,
            account_id="linkedin_123",
            access_token="expired_token",
            token_expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
            is_active=True
        )
        db_session.add(account)
        
        post = GeneratedPost(
            meeting_id=test_meeting_for_post.id,
            platform="linkedin",
            content="Test post",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        
        response = await client.post(
            f"/api/v1/social/posts/{post.id}/post",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 401
        assert "token expired" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_post_to_social_posting_failure(
        self, client: AsyncClient, test_user, test_social_account,
        test_generated_post, auth_token, db_session
    ):
        """Test posting failure."""
        from unittest.mock import MagicMock, AsyncMock
        mock_poster = AsyncMock()
        mock_poster.post.side_effect = Exception("Posting failed")
        
        with patch("app.api.v1.social.SocialMediaPosterFactory.create") as mock_factory:
            mock_factory.return_value = mock_poster
            
            response = await client.post(
                f"/api/v1/social/posts/{test_generated_post.id}/post",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 500
            assert "failed to post" in response.json()["detail"].lower()
            
            await db_session.refresh(test_generated_post)
            assert test_generated_post.status == PostStatus.FAILED
            assert test_generated_post.error_message is not None
    
    @pytest.mark.asyncio
    async def test_post_to_social_post_not_found(
        self, client: AsyncClient, test_user, auth_token
    ):
        """Test posting non-existent post."""
        response = await client.post(
            "/api/v1/social/posts/99999/post",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_post_success(
        self, client: AsyncClient, test_user, test_generated_post, auth_token
    ):
        """Test getting a post by ID."""
        response = await client.get(
            f"/api/v1/social/posts/{test_generated_post.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_generated_post.id
        assert data["platform"] == "linkedin"
        assert data["content"] == "Test LinkedIn post content"
        assert data["status"] == "draft"
    
    @pytest.mark.asyncio
    async def test_get_post_not_found(
        self, client: AsyncClient, test_user, auth_token
    ):
        """Test getting non-existent post."""
        response = await client.get(
            "/api/v1/social/posts/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_post_unauthorized(
        self, client: AsyncClient, db_session, test_user, test_generated_post
    ):
        """Test getting post from another user."""
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
            f"/api/v1/social/posts/{test_generated_post.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_list_social_accounts_unauthorized(self, client: AsyncClient):
        """Test listing accounts without authentication."""
        response = await client.get("/api/v1/social/accounts")
        assert response.status_code == 401

