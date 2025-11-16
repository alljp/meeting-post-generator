from typing import Optional, Dict, Any
import httpx
from app.core.config import settings
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta
from app.auth.base import OAuthProvider


class FacebookOAuthProvider(OAuthProvider):
    """Facebook OAuth provider implementation"""
    
    @property
    def provider_name(self) -> str:
        return "facebook"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get the Facebook OAuth authorization URL"""
        params = {
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "state": state or "facebook_oauth",
            "scope": "email,public_profile,pages_manage_posts,pages_read_engagement",  # Permissions for posting
            "response_type": "code",
        }
        return f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
    
    def get_user_info(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens and get user info"""
        # Exchange code for access token
        token_response = httpx.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "client_id": settings.FACEBOOK_CLIENT_ID,
                "client_secret": settings.FACEBOOK_CLIENT_SECRET,
                "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
                "code": code,
            },
        )
        
        if token_response.status_code != 200:
            raise Exception(f"Failed to get Facebook token: {token_response.text}")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
        
        if not access_token:
            raise Exception("No access token in Facebook response")
        
        # Get user info
        user_response = httpx.get(
            "https://graph.facebook.com/v18.0/me",
            params={
                "fields": "id,name,email,picture",
                "access_token": access_token,
            },
        )
        
        if user_response.status_code != 200:
            raise Exception(f"Failed to get Facebook user info: {user_response.text}")
        
        user_data = user_response.json()
        
        # Calculate token expiry
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        return {
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "picture": user_data.get("picture", {}).get("data", {}).get("url") if user_data.get("picture") else None,
            "facebook_id": user_data.get("id"),
            "access_token": access_token,
            "refresh_token": None,  # Facebook uses long-lived tokens, not refresh tokens
            "token_expiry": token_expires_at.isoformat(),
        }
    
    def refresh_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get long-lived Facebook token"""
        try:
            response = httpx.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.FACEBOOK_CLIENT_ID,
                    "client_secret": settings.FACEBOOK_CLIENT_SECRET,
                    "fb_exchange_token": access_token,
                },
            )
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 5184000)  # 60 days in seconds
                
                token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                return {
                    "access_token": new_access_token,
                    "token_expiry": token_expires_at.isoformat(),
                }
        except Exception:
            pass
        
        return None

