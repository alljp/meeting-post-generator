from typing import Optional
from app.auth.base import OAuthProvider
from app.auth.strategies.google import GoogleOAuthProvider
from app.auth.strategies.linkedin import LinkedInOAuthProvider
from app.auth.strategies.facebook import FacebookOAuthProvider


class OAuthProviderFactory:
    """Factory for creating OAuth provider instances"""
    
    _providers = {
        "google": GoogleOAuthProvider,
        "linkedin": LinkedInOAuthProvider,
        "facebook": FacebookOAuthProvider,
    }
    
    @classmethod
    def create(cls, provider_name: str) -> OAuthProvider:
        """
        Create an OAuth provider instance.
        
        Args:
            provider_name: Name of the provider (google, linkedin, facebook)
            
        Returns:
            OAuthProvider instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        provider_name_lower = provider_name.lower()
        
        if provider_name_lower not in cls._providers:
            raise ValueError(
                f"Unsupported OAuth provider: {provider_name}. "
                f"Supported providers: {', '.join(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name_lower]
        return provider_class()
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all supported OAuth provider names"""
        return list(cls._providers.keys())
    
    @classmethod
    def is_supported(cls, provider_name: str) -> bool:
        """Check if a provider is supported"""
        return provider_name.lower() in cls._providers

