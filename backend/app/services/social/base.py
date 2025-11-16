from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SocialMediaPoster(ABC):
    """Abstract base class for social media posting strategies"""
    
    @abstractmethod
    async def post(
        self,
        access_token: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Post content to the social media platform.
        
        Args:
            access_token: OAuth access token
            content: Post content text
            **kwargs: Additional platform-specific parameters
            
        Returns:
            Dictionary with post_id and other response data
            
        Raises:
            Exception if posting fails
        """
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name (e.g., 'linkedin', 'facebook')"""
        pass

