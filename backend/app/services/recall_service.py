from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

RECALL_API_BASE = "https://us-west-2.recall.ai/api/v1"


class RecallService:
    """Service for interacting with Recall.ai API"""
    
    def __init__(self):
        self.api_key = settings.RECALL_API_KEY
        self.base_url = RECALL_API_BASE
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
    
    async def create_bot(
        self,
        meeting_url: str,
        meeting_start_time: datetime,
        bot_name: Optional[str] = None,
        mode: Optional[str] = "prioritize_low_latency"
    ) -> Dict[str, Any]:
        """
        Create a Recall.ai bot for a meeting.
        
        Args:
            meeting_url: The meeting URL (Zoom/Teams/Meet)
            meeting_start_time: When the meeting starts
            bot_name: Optional name for the bot
        
        Returns:
            Bot creation response with bot_id
        """
        async with httpx.AsyncClient() as client:
            payload = {
                "meeting_url": meeting_url,
                "meeting_start_time": meeting_start_time.isoformat(),
                "bot_name": bot_name or f"Bot-{meeting_start_time.strftime('%Y%m%d-%H%M')}",
                "recording_config": {
                    "transcript": {
                        "provider": {
                            "recallai_streaming": {
                                "language_code": "en",
                                "mode": mode
                            }
                        }
                    }
                }
            }
            
            response = await client.post(
                f"{self.base_url}/bot/",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def get_bot(self, bot_id: str) -> Dict[str, Any]:
        """
        Get bot details by ID.
        
        Args:
            bot_id: The bot ID
        
        Returns:
            Bot details
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bot/{bot_id}/",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def join_bot(self, bot_id: str) -> Dict[str, Any]:
        """
        Join a bot to the meeting.
        
        Args:
            bot_id: The bot ID
        
        Returns:
            Join response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bots/{bot_id}/join/",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def leave_bot(self, bot_id: str) -> Dict[str, Any]:
        """
        Leave a bot from the meeting.
        
        Args:
            bot_id: The bot ID
        
        Returns:
            Leave response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bots/{bot_id}/leave/",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        """
        Get bot status.
        
        Args:
            bot_id: The bot ID
        
        Returns:
            Bot status including state, transcript availability, etc.
        """
        bot_data = await self.get_bot(bot_id)
        
        # Check if transcript is available in recordings
        transcript_available = False
        recording_available = False
        
        logger.debug(f"Bot status data for {bot_id}: {bot_data}")
        
        if "recordings" in bot_data and isinstance(bot_data["recordings"], list) and len(bot_data["recordings"]) > 0:
            recording = bot_data["recordings"][0]
            if recording.get("status", {}).get("code") == "done":
                recording_available = True
                
                # Check for transcript in media_shortcuts
                media_shortcuts = recording.get("media_shortcuts", {})
                transcript_info = media_shortcuts.get("transcript", {})
                
                if transcript_info.get("status", {}).get("code") == "done":
                    transcript_data = transcript_info.get("data", {})
                    if transcript_data.get("download_url"):
                        transcript_available = True
        
        # Determine state from status_changes
        state = "unknown"
        if "status_changes" in bot_data and isinstance(bot_data["status_changes"], list):
            last_status = bot_data["status_changes"][-1] if bot_data["status_changes"] else {}
            state = last_status.get("code", "unknown")
        
        return {
            "bot_id": bot_data.get("id"),
            "status": bot_data.get("status"),
            "state": state,
            "transcript_available": transcript_available,
            "recording_available": recording_available,
            "meeting_url": bot_data.get("meeting_url"),
            "started_at": bot_data.get("started_at"),
            "ended_at": bot_data.get("ended_at"),
        }
    
    async def get_transcript(self, bot_id: str) -> Optional[str]:
        """
        Get transcript for a bot by downloading it from the download URL in the bot response.
        
        Args:
            bot_id: The bot ID
        
        Returns:
            Transcript text or None if not available
        """
        try:
            # Get bot data to find transcript download URL
            bot_data = await self.get_bot(bot_id)
            
            # Navigate to transcript download URL: recordings[0]["media_shortcuts"]["transcript"]["data"]["download_url"]
            if "recordings" not in bot_data or not isinstance(bot_data["recordings"], list) or len(bot_data["recordings"]) == 0:
                return None
            
            recording = bot_data["recordings"][0]
            media_shortcuts = recording.get("media_shortcuts", {})
            transcript_info = media_shortcuts.get("transcript", {})
            
            # Check if transcript is done
            if transcript_info.get("status", {}).get("code") != "done":
                return None
            
            transcript_data = transcript_info.get("data", {})
            download_url = transcript_data.get("download_url")
            
            if not download_url:
                return None
            
            # Download the transcript JSON file
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, timeout=60.0)
                response.raise_for_status()
                transcript_json = response.json()
            
            # Parse the transcript JSON and extract text
            # The format is likely diarized with segments
            transcript_text = self._parse_transcript_json(transcript_json)
            
            return transcript_text if transcript_text else None
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error getting transcript for bot {bot_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            # Log error but don't fail completely
            logger.error(f"Error getting transcript for bot {bot_id}: {e}", exc_info=True)
            return None
    
    def _parse_transcript_json(self, transcript_json: Dict[str, Any]) -> Optional[str]:
        """
        Parse transcript JSON and extract text.
        Handles different transcript formats from Recall.ai.
        
        Args:
            transcript_json: The transcript JSON data (can be dict or list)
        
        Returns:
            Combined transcript text or None
        """
        try:
            # Format 1: List of participant segments with words
            # Structure: [{"participant": "name", "words": [{"text": "...", ...}, ...]}, ...]
            if isinstance(transcript_json, list) and len(transcript_json) > 0:
                first_item = transcript_json[0]
                if isinstance(first_item, dict) and "participant" in first_item and "words" in first_item:
                    # This is the diarized format with participants and words
                    transcript_lines = []
                    current_speaker = None
                    current_words = []
                    
                    for segment in transcript_json:
                        # Extract participant name (can be string or dict)
                        participant_data = segment.get("participant") or segment.get("speaker")
                        if isinstance(participant_data, dict):
                            participant = participant_data.get("name") or participant_data.get("id") or "Unknown"
                        elif isinstance(participant_data, str):
                            participant = participant_data
                        else:
                            participant = "Unknown"
                        
                        words = segment.get("words", [])
                        
                        # If speaker changed, add previous speaker's text
                        if participant != current_speaker and current_words:
                            sentence = " ".join(current_words)
                            if current_speaker and current_speaker != "Unknown":
                                transcript_lines.append(f"{current_speaker}: {sentence}")
                            else:
                                transcript_lines.append(sentence)
                            current_words = []
                        
                        current_speaker = participant
                        
                        # Extract words from this segment
                        for word_data in words:
                            if isinstance(word_data, dict):
                                word_text = word_data.get("text") or word_data.get("word") or word_data.get("content")
                                if word_text:
                                    current_words.append(word_text)
                            elif isinstance(word_data, str):
                                current_words.append(word_data)
                    
                    # Add final segment
                    if current_words:
                        sentence = " ".join(current_words)
                        if current_speaker and current_speaker != "Unknown":
                            transcript_lines.append(f"{current_speaker}: {sentence}")
                        else:
                            transcript_lines.append(sentence)
                    
                    return "\n".join(transcript_lines) if transcript_lines else None
            
            # Format 2: Direct segments array (alternative format)
            segments = []
            if isinstance(transcript_json, list):
                segments = transcript_json
            # Format 3: Object with segments/words/text
            elif isinstance(transcript_json, dict):
                # Check for common keys
                if "segments" in transcript_json:
                    segments = transcript_json["segments"]
                elif "words" in transcript_json:
                    segments = transcript_json["words"]
                elif "text" in transcript_json:
                    return transcript_json["text"]
                elif "transcript" in transcript_json:
                    return transcript_json["transcript"]
                else:
                    # Try to find any array of text segments
                    for key, value in transcript_json.items():
                        if isinstance(value, list) and len(value) > 0:
                            if isinstance(value[0], dict) and ("text" in value[0] or "word" in value[0] or "content" in value[0]):
                                segments = value
                                break
            
            # Extract text from segments (fallback for other formats)
            if segments:
                transcript_lines = []
                for segment in segments:
                    if isinstance(segment, dict):
                        # Try different possible text fields
                        text = segment.get("text") or segment.get("word") or segment.get("content") or segment.get("transcript")
                        if text:
                            # Include speaker if available
                            speaker = segment.get("speaker") or segment.get("speaker_name") or segment.get("participant")
                            if speaker:
                                transcript_lines.append(f"{speaker}: {text}")
                            else:
                                transcript_lines.append(text)
                    elif isinstance(segment, str):
                        transcript_lines.append(segment)
                
                return "\n".join(transcript_lines) if transcript_lines else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing transcript JSON: {e}", exc_info=True)
            return None
    
    async def get_recording_url(self, bot_id: str) -> Optional[str]:
        """
        Get recording URL for a bot from the recordings structure.
        
        Args:
            bot_id: The bot ID
        
        Returns:
            Recording URL or None if not available
        """
        try:
            bot_data = await self.get_bot(bot_id)
            
            # Navigate to video_mixed download URL: recordings[0]["media_shortcuts"]["video_mixed"]["data"]["download_url"]
            if "recordings" in bot_data and isinstance(bot_data["recordings"], list) and len(bot_data["recordings"]) > 0:
                recording = bot_data["recordings"][0]
                media_shortcuts = recording.get("media_shortcuts", {})
                video_info = media_shortcuts.get("video_mixed", {})
                
                if video_info.get("status", {}).get("code") == "done":
                    video_data = video_info.get("data", {})
                    download_url = video_data.get("download_url")
                    if download_url:
                        return download_url
            
            # Fallback to old format
            return bot_data.get("recording_url") or bot_data.get("video_url")
        except Exception as e:
            logger.error(f"Error getting recording URL for bot {bot_id}: {e}", exc_info=True)
            return None
    
    async def get_bot_attendees(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get attendees from a bot.
        
        Args:
            bot_id: The bot ID
        
        Returns:
            List of attendees
        """
        try:
            bot_data = await self.get_bot(bot_id)
            return bot_data.get("attendees", [])
        except Exception:
            return []


# Singleton instance
recall_service = RecallService()

