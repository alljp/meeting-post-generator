from app.services.social.base import SocialMediaPoster
from app.services.social.strategies.linkedin import LinkedInPoster
from app.services.social.strategies.facebook import FacebookPoster
from app.models.social_account import SocialPlatform


class SocialMediaPosterFactory:
    """Factory for creating social media poster instances"""
    
    _posters = {
        SocialPlatform.LINKEDIN: LinkedInPoster,
        SocialPlatform.FACEBOOK: FacebookPoster,
    }
    
    @classmethod
    def create(cls, platform: SocialPlatform) -> SocialMediaPoster:
        """
        Create a social media poster instance.
        
        Args:
            platform: Social platform enum (LINKEDIN or FACEBOOK)
            
        Returns:
            SocialMediaPoster instance
            
        Raises:
            ValueError: If platform is not supported
        """
        if platform not in cls._posters:
            raise ValueError(
                f"Unsupported social media platform: {platform}. "
                f"Supported platforms: {', '.join([p.value for p in cls._posters.keys()])}"
            )
        
        poster_class = cls._posters[platform]
        return poster_class()
    
    @classmethod
    def list_platforms(cls) -> list[SocialPlatform]:
        """List all supported social media platforms"""
        return list(cls._posters.keys())
    
    @classmethod
    def is_supported(cls, platform: SocialPlatform) -> bool:
        """Check if a platform is supported"""
        return platform in cls._posters

