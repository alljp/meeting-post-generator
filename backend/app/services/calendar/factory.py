from typing import Optional
from app.services.calendar.base import CalendarProvider
from app.services.calendar.strategies.google import GoogleCalendarProvider


class CalendarProviderFactory:
    """Factory for creating calendar provider instances"""
    
    _providers = {
        "google": GoogleCalendarProvider,
    }
    
    @classmethod
    def create(cls, provider_name: str) -> CalendarProvider:
        """
        Create a calendar provider instance.
        
        Args:
            provider_name: Name of the calendar provider (google, outlook, apple, etc.)
            
        Returns:
            CalendarProvider instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        provider_name_lower = provider_name.lower()
        
        if provider_name_lower not in cls._providers:
            raise ValueError(
                f"Unsupported calendar provider: {provider_name}. "
                f"Supported providers: {', '.join(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name_lower]
        return provider_class()
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all supported calendar provider names"""
        return list(cls._providers.keys())
    
    @classmethod
    def is_supported(cls, provider_name: str) -> bool:
        """Check if a provider is supported"""
        return provider_name.lower() in cls._providers

