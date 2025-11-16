from typing import Optional, Dict, Any
import httpx
from app.core.config import settings
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta
from app.auth.base import OAuthProvider


class LinkedInOAuthProvider(OAuthProvider):
    """LinkedIn OAuth provider implementation"""
    
    @property
    def provider_name(self) -> str:
        return "linkedin"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get the LinkedIn OAuth authorization URL"""
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "state": state or "linkedin_oauth",
            "scope": "openid profile email w_member_social",  # w_member_social is for posting
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    
    def get_user_info(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens and get user info"""
        # Exchange code for access token
        token_response = httpx.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if token_response.status_code != 200:
            raise Exception(f"Failed to get LinkedIn token: {token_response.text}")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
        
        if not access_token:
            raise Exception("No access token in LinkedIn response")
        
        # Get user info
        user_response = httpx.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if user_response.status_code != 200:
            raise Exception(f"Failed to get LinkedIn user info: {user_response.text}")
        
        user_data = user_response.json()
        
        # Calculate token expiry
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        return {
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "picture": user_data.get("picture"),
            "linkedin_id": user_data.get("sub"),
            "access_token": access_token,
            "refresh_token": None,  # LinkedIn doesn't provide refresh tokens in OAuth 2.0
            "token_expiry": token_expires_at.isoformat(),
        }
    
    def refresh_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Refresh LinkedIn token if possible (LinkedIn has limited refresh token support)"""
        # LinkedIn doesn't provide refresh tokens in standard OAuth 2.0 flow
        # Token refresh would require re-authorization
        return None

