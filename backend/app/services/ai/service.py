from typing import Optional
from app.services.ai.factory import AIGeneratorFactory
from app.services.ai.base import AIGenerator


class AIService:
    """
    AI Service facade that maintains backward compatibility.
    Delegates to AIGeneratorFactory for actual implementation.
    """
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize AI service with optional provider.
        
        Args:
            provider_name: Optional AI provider name (defaults to OpenAI)
        """
        self._generator: AIGenerator = AIGeneratorFactory.create(provider_name)
    
    async def generate_follow_up_email(
        self,
        transcript: str,
        meeting_title: str,
        attendees: list,
        meeting_date: str
    ) -> str:
        """Generate a follow-up email from meeting transcript"""
        return await self._generator.generate_follow_up_email(
            transcript=transcript,
            meeting_title=meeting_title,
            attendees=attendees,
            meeting_date=meeting_date
        )
    
    async def generate_social_media_post(
        self,
        transcript: str,
        meeting_title: str,
        platform: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Generate a social media post from meeting transcript"""
        return await self._generator.generate_social_media_post(
            transcript=transcript,
            meeting_title=meeting_title,
            platform=platform,
            custom_prompt=custom_prompt
        )


# Singleton instance for backward compatibility
ai_service = AIService()

