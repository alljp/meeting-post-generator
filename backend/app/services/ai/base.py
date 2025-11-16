from abc import ABC, abstractmethod
from typing import Optional


class AIGenerator(ABC):
    """Abstract base class for AI content generation strategies"""
    
    @abstractmethod
    async def generate_follow_up_email(
        self,
        transcript: str,
        meeting_title: str,
        attendees: list,
        meeting_date: str
    ) -> str:
        """
        Generate a follow-up email from meeting transcript.
        
        Args:
            transcript: Meeting transcript text
            meeting_title: Title of the meeting
            attendees: List of attendee dictionaries with name/email
            meeting_date: Date of the meeting
            
        Returns:
            Generated email content
        """
        pass
    
    @abstractmethod
    async def generate_social_media_post(
        self,
        transcript: str,
        meeting_title: str,
        platform: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a social media post from meeting transcript.
        
        Args:
            transcript: Meeting transcript text
            meeting_title: Title of the meeting
            platform: Platform name (linkedin or facebook)
            custom_prompt: Optional custom prompt template
            
        Returns:
            Generated post content
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the AI provider name (e.g., 'openai', 'claude', 'gemini')"""
        pass

