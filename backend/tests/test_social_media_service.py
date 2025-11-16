"""
Unit tests for Social Media Service.
Tests LinkedIn and Facebook posting functionality.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.social.factory import SocialMediaPosterFactory
from app.models.social_account import SocialPlatform


class TestSocialMediaService:
    """Test suite for SocialMediaService."""
    
    @pytest.fixture
    def linkedin_poster(self):
        """Create LinkedInPoster instance."""
        return SocialMediaPosterFactory.create(SocialPlatform.LINKEDIN)
    
    @pytest.fixture
    def facebook_poster(self):
        """Create FacebookPoster instance."""
        return SocialMediaPosterFactory.create(SocialPlatform.FACEBOOK)
    
    @pytest.mark.asyncio
    async def test_post_to_linkedin_success(self, linkedin_poster):
        """Test successful LinkedIn posting."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Mock profile response
            mock_profile_response = MagicMock()
            mock_profile_response.status_code = 200
            mock_profile_response.json.return_value = {"sub": "test_user_id"}
            
            # Mock post response
            mock_post_response = MagicMock()
            mock_post_response.status_code = 201
            mock_post_response.json.return_value = {"id": "urn:li:ugcPost:123456"}
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_profile_response)
            mock_client.post = AsyncMock(return_value=mock_post_response)
            mock_client_class.return_value = mock_client
            
            result = await linkedin_poster.post(
                access_token="test_token",
                content="Test LinkedIn post"
            )
            
            assert result["success"] is True
            assert result["platform"] == "linkedin"
            assert result["post_id"] == "urn:li:ugcPost:123456"
            mock_client.get.assert_called_once()
            mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_to_linkedin_profile_failure(self, linkedin_poster):
        """Test LinkedIn posting when profile fetch fails."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_profile_response = MagicMock()
            mock_profile_response.status_code = 401
            mock_profile_response.text = "Unauthorized"
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_profile_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                await linkedin_poster.post(
                    access_token="invalid_token",
                    content="Test post"
                )
            
            assert "Failed to get LinkedIn profile" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_post_to_linkedin_post_failure(self, linkedin_poster):
        """Test LinkedIn posting when post creation fails."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Mock profile response
            mock_profile_response = MagicMock()
            mock_profile_response.status_code = 200
            mock_profile_response.json.return_value = {"sub": "test_user_id"}
            
            # Mock post failure
            mock_post_response = MagicMock()
            mock_post_response.status_code = 400
            mock_post_response.text = "Bad Request"
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_profile_response)
            mock_client.post = AsyncMock(return_value=mock_post_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                await linkedin_poster.post(
                    access_token="test_token",
                    content="Test post"
                )
            
            assert "Failed to post to LinkedIn" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_post_to_facebook_success(self, facebook_poster):
        """Test successful Facebook posting to user timeline."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "123456789"}
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await facebook_poster.post(
                access_token="test_token",
                content="Test Facebook post"
            )
            
            assert result["success"] is True
            assert result["platform"] == "facebook"
            assert result["post_id"] == "123456789"
            mock_client.post.assert_called_once()
            # Verify endpoint
            call_args = mock_client.post.call_args
            assert "me/feed" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_post_to_facebook_page_success(self, facebook_poster):
        """Test successful Facebook posting to a page."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "987654321"}
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await facebook_poster.post(
                access_token="test_token",
                content="Test post",
                page_id="page123"
            )
            
            assert result["success"] is True
            call_args = mock_client.post.call_args
            assert "page123/feed" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_post_to_facebook_failure(self, facebook_poster):
        """Test Facebook posting failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Invalid token"
            mock_response.json.return_value = {
                "error": {
                    "message": "Invalid access token",
                    "type": "OAuthException"
                }
            }
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                await facebook_poster.post(
                    access_token="invalid_token",
                    content="Test post"
                )
            
            assert "Failed to post to Facebook" in str(exc_info.value)
            # Error message may contain "Invalid access token" or "Invalid token"
            error_msg = str(exc_info.value)
            assert "invalid" in error_msg.lower() or "token" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_post_to_facebook_failure_no_json(self, facebook_poster):
        """Test Facebook posting failure with non-JSON response."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.json.side_effect = ValueError("Not JSON")
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                await facebook_poster.post(
                    access_token="test_token",
                    content="Test post"
                )
            
            assert "Failed to post to Facebook" in str(exc_info.value)
            assert "Internal Server Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_factory_create_linkedin(self):
        """Test factory creates LinkedIn poster."""
        poster = SocialMediaPosterFactory.create(SocialPlatform.LINKEDIN)
        assert poster.platform_name == "linkedin"
    
    @pytest.mark.asyncio
    async def test_factory_create_facebook(self):
        """Test factory creates Facebook poster."""
        poster = SocialMediaPosterFactory.create(SocialPlatform.FACEBOOK)
        assert poster.platform_name == "facebook"
    
    def test_factory_unsupported_platform(self):
        """Test factory raises error for unsupported platform."""
        # Create a mock unsupported platform
        from unittest.mock import Mock
        unsupported_platform = Mock()
        unsupported_platform.value = "twitter"
        
        with pytest.raises(ValueError) as exc_info:
            SocialMediaPosterFactory.create(unsupported_platform)
        
        assert "Unsupported social media platform" in str(exc_info.value)

