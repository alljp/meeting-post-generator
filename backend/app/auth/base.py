from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class OAuthProvider(ABC):
    """Abstract base class for OAuth providers"""
    
    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get the OAuth authorization URL.
        
        Args:
            state: Optional state parameter for OAuth flow
            
        Returns:
            Authorization URL string
        """
        pass
    
    @abstractmethod
    def get_user_info(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens and get user info.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dictionary with user info, tokens, and expiry
        """
        pass
    
    @abstractmethod
    def refresh_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh an access token if supported.
        
        Args:
            access_token: Current access token
            
        Returns:
            Dictionary with new access token and expiry, or None if not supported
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'google', 'linkedin', 'facebook')"""
        pass

