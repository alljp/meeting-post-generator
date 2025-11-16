"""
Unit tests for Recall Service.
Tests Recall.ai API integration for bot management and transcript retrieval.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.services.recall_service import RecallService


class TestRecallService:
    """Test suite for RecallService."""
    
    @pytest.fixture
    def recall_service(self):
        """Create RecallService instance."""
        return RecallService()
    
    @pytest.mark.asyncio
    async def test_create_bot_success(self, recall_service, mock_recall_api_response):
        """Test successful bot creation."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_recall_api_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            meeting_time = datetime.now(timezone.utc) + timedelta(hours=1)
            result = await recall_service.create_bot(
                meeting_url="https://zoom.us/j/123456789",
                meeting_start_time=meeting_time,
                bot_name="Test Bot"
            )
            
            assert result["id"] == "bot_123"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "bot/" in call_args[0][0]
            assert call_args[1]["json"]["meeting_url"] == "https://zoom.us/j/123456789"
    
    @pytest.mark.asyncio
    async def test_create_bot_default_name(self, recall_service, mock_recall_api_response):
        """Test bot creation with default name generation."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_recall_api_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            meeting_time = datetime.now(timezone.utc)
            await recall_service.create_bot(
                meeting_url="https://zoom.us/j/123456789",
                meeting_start_time=meeting_time
            )
            
            call_args = mock_client.post.call_args
            assert "bot_name" in call_args[1]["json"]
            assert call_args[1]["json"]["bot_name"].startswith("Bot-")
    
    @pytest.mark.asyncio
    async def test_get_bot_success(self, recall_service, mock_recall_api_response):
        """Test successful bot retrieval."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_recall_api_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await recall_service.get_bot("bot_123")
            
            assert result["id"] == "bot_123"
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "bot/bot_123" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_join_bot_success(self, recall_service):
        """Test successful bot join."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "joined"}
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await recall_service.join_bot("bot_123")
            
            assert result["status"] == "joined"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "bots/bot_123/join" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_leave_bot_success(self, recall_service):
        """Test successful bot leave."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "left"}
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await recall_service.leave_bot("bot_123")
            
            assert result["status"] == "left"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "bots/bot_123/leave" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_get_bot_status_success(self, recall_service, mock_recall_api_response):
        """Test bot status retrieval."""
        # Update mock to include status_changes for state
        mock_response_data = {
            **mock_recall_api_response,
            "status_changes": [{"code": "joined"}],
            "recordings": [{
                "status": {"code": "done"},
                "media_shortcuts": {
                    "transcript": {
                        "status": {"code": "done"},
                        "data": {"download_url": "https://example.com/transcript.txt"}
                    }
                }
            }]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await recall_service.get_bot_status("bot_123")
            
            assert result["bot_id"] == "bot_123"
            assert result["status"] == "active"
            assert result["state"] == "joined"  # Should be from status_changes
            assert result["transcript_available"] is True
    
    @pytest.mark.asyncio
    async def test_get_transcript_success(self, recall_service):
        """Test transcript retrieval."""
        # Mock bot data with transcript download URL
        bot_data_with_transcript = {
            "id": "bot_123",
            "recordings": [{
                "status": {"code": "done"},
                "media_shortcuts": {
                    "transcript": {
                        "status": {"code": "done"},
                        "data": {"download_url": "https://example.com/transcript.json"}
                    }
                }
            }]
        }
        
        # Mock transcript JSON response (typical format)
        transcript_json = {
            "segments": [
                {"speaker": "Speaker 1", "text": "This is the transcript text."}
            ]
        }
        
        # Mock get_bot to return bot data
        with patch.object(recall_service, "get_bot", return_value=bot_data_with_transcript):
            # Mock httpx for downloading transcript
            with patch("httpx.AsyncClient") as mock_client_class:
                transcript_response = MagicMock()
                transcript_response.json.return_value = transcript_json
                transcript_response.raise_for_status = MagicMock()
                
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.get = AsyncMock(return_value=transcript_response)
                mock_client_class.return_value = mock_client
                
                result = await recall_service.get_transcript("bot_123")
                
                # Should extract text from transcript JSON
                assert result is not None
                assert "transcript" in result.lower() or len(result) > 0
                mock_client.get.assert_called_once()  # Only download call
    
    @pytest.mark.asyncio
    async def test_get_transcript_not_found(self, recall_service):
        """Test transcript retrieval when not available."""
        import httpx
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 404
            http_error = httpx.HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=http_error)
            mock_client_class.return_value = mock_client
            
            result = await recall_service.get_transcript("bot_123")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_recording_url_success(self, recall_service):
        """Test recording URL retrieval."""
        bot_data = {
            "id": "bot_123",
            "recording_url": "https://example.com/recording.mp4"
        }
        with patch.object(recall_service, "get_bot", return_value=bot_data):
            result = await recall_service.get_recording_url("bot_123")
            assert result == "https://example.com/recording.mp4"
    
    @pytest.mark.asyncio
    async def test_get_bot_attendees_success(self, recall_service):
        """Test attendees retrieval."""
        bot_data = {
            "id": "bot_123",
            "attendees": [
                {"name": "John Doe", "email": "john@example.com"},
                {"name": "Jane Smith", "email": "jane@example.com"}
            ]
        }
        with patch.object(recall_service, "get_bot", return_value=bot_data):
            result = await recall_service.get_bot_attendees("bot_123")
            assert len(result) == 2
            assert result[0]["name"] == "John Doe"

