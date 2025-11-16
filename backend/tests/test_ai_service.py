"""
Unit tests for AI Service.
Tests OpenAI integration for email and social media post generation.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ai.service import AIService
from app.core.config import settings


class TestAIService:
    """Test suite for AIService."""
    
    @pytest.fixture
    def ai_service(self):
        """Create AIService instance."""
        return AIService()
    
    @pytest.mark.asyncio
    async def test_generate_follow_up_email_success(self, ai_service, mock_openai_response):
        """Test successful email generation."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Mock Responses API format
            mock_response_data = [{"type": "output_text", "text": "This is a generated email content."}]
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.generate_follow_up_email(
                transcript="Meeting transcript here",
                meeting_title="Team Sync",
                attendees=[{"name": "John Doe"}, {"name": "Jane Smith"}],
                meeting_date="2024-01-15"
            )
            
            assert "generated email" in result.lower()
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            # Check for /responses endpoint (new API) or /chat/completions (fallback)
            url = call_args[0][0]
            assert "/responses" in url or "/chat/completions" in url
    
    @pytest.mark.asyncio
    async def test_generate_follow_up_email_no_api_key(self, ai_service):
        """Test email generation when API key is missing."""
        original_key = ai_service._generator.api_key
        ai_service._generator.api_key = None
        
        result = await ai_service.generate_follow_up_email(
            transcript="Test",
            meeting_title="Test",
            attendees=[],
            meeting_date="2024-01-15"
        )
        
        assert "not configured" in result.lower()
        ai_service._generator.api_key = original_key
    
    @pytest.mark.asyncio
    async def test_generate_follow_up_email_api_error(self, ai_service):
        """Test email generation when API call fails."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(side_effect=Exception("API Error"))
            mock_client_class.return_value = mock_client
            
            result = await ai_service.generate_follow_up_email(
                transcript="Test",
                meeting_title="Test",
                attendees=[],
                meeting_date="2024-01-15"
            )
            
            assert "error" in result.lower()
    
    @pytest.mark.asyncio
    async def test_generate_social_media_post_linkedin(self, ai_service, mock_openai_response):
        """Test LinkedIn post generation."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Mock Responses API format
            mock_response_data = [{"type": "output_text", "text": "LinkedIn post content"}]
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.generate_social_media_post(
                transcript="Meeting transcript",
                meeting_title="Product Launch",
                platform="linkedin"
            )
            
            assert len(result) > 0
            call_args = mock_client.post.call_args
            url = call_args[0][0]
            assert "/responses" in url or "/chat/completions" in url
            # Check that LinkedIn is mentioned in the input/prompt
            json_data = call_args[1]["json"]
            input_text = json_data.get("input", "") or (json_data.get("messages", [{}])[-1].get("content", "") if json_data.get("messages") else "")
            assert "linkedin" in input_text.lower() or "linkedin" in str(json_data).lower()
    
    @pytest.mark.asyncio
    async def test_generate_social_media_post_facebook(self, ai_service, mock_openai_response):
        """Test Facebook post generation."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Mock Responses API format
            mock_response_data = [{"type": "output_text", "text": "Facebook post content"}]
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await ai_service.generate_social_media_post(
                transcript="Meeting transcript",
                meeting_title="Team Meeting",
                platform="facebook"
            )
            
            assert len(result) > 0
            call_args = mock_client.post.call_args
            # Check that Facebook is mentioned in the input/prompt
            json_data = call_args[1]["json"]
            input_text = json_data.get("input", "") or (json_data.get("messages", [{}])[-1].get("content", "") if json_data.get("messages") else "")
            assert "facebook" in input_text.lower() or "facebook" in str(json_data).lower()
    
    @pytest.mark.asyncio
    async def test_generate_social_media_post_custom_prompt(self, ai_service, mock_openai_response):
        """Test social media post generation with custom prompt."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Mock Responses API format
            mock_response_data = [{"type": "output_text", "text": "Custom post content"}]
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            custom_prompt = "Create a post about {transcript} for {meeting_title}"
            result = await ai_service.generate_social_media_post(
                transcript="Test transcript",
                meeting_title="Test Meeting",
                platform="linkedin",
                custom_prompt=custom_prompt
            )
            
            assert len(result) > 0
            call_args = mock_client.post.call_args
            # Verify custom prompt was used (check input field for Responses API or messages for Chat Completions)
            json_data = call_args[1]["json"]
            prompt_content = json_data.get("input", "") or (json_data.get("messages", [{}])[-1].get("content", "") if json_data.get("messages") else "")
            assert "Test transcript" in prompt_content
            assert "Test Meeting" in prompt_content
    
    @pytest.mark.asyncio
    async def test_generate_social_media_post_no_api_key(self, ai_service):
        """Test social media post generation when API key is missing."""
        original_key = ai_service._generator.api_key
        ai_service._generator.api_key = None
        
        result = await ai_service.generate_social_media_post(
            transcript="Test",
            meeting_title="Test",
            platform="linkedin"
        )
        
        assert "not configured" in result.lower()
        ai_service._generator.api_key = original_key

