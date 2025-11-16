from typing import Optional
from app.services.ai.base import AIGenerator
from app.services.ai.strategies.openai import OpenAIGenerator
from app.core.config import settings


class AIGeneratorFactory:
    """Factory for creating AI generator instances"""
    
    _generators = {
        "openai": OpenAIGenerator,
    }
    
    @classmethod
    def create(cls, provider_name: Optional[str] = None) -> AIGenerator:
        """
        Create an AI generator instance.
        
        Args:
            provider_name: Name of the AI provider (openai, claude, gemini, etc.)
                          If None, uses default from settings or 'openai'
            
        Returns:
            AIGenerator instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        if provider_name is None:
            # Get default provider from settings or use OpenAI
            provider_name = getattr(settings, 'AI_PROVIDER', 'openai')
        
        provider_name_lower = provider_name.lower()
        
        if provider_name_lower not in cls._generators:
            raise ValueError(
                f"Unsupported AI provider: {provider_name}. "
                f"Supported providers: {', '.join(cls._generators.keys())}"
            )
        
        generator_class = cls._generators[provider_name_lower]
        return generator_class()
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all supported AI provider names"""
        return list(cls._generators.keys())
    
    @classmethod
    def is_supported(cls, provider_name: str) -> bool:
        """Check if a provider is supported"""
        return provider_name.lower() in cls._generators

