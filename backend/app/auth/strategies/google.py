from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError, OAuthError, GoogleAuthError
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.auth.base import OAuthProvider


# Google OAuth2 scopes
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider implementation"""
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    def _get_oauth_flow(self, redirect_uri: Optional[str] = None) -> Flow:
        """Create and return a Google OAuth2 flow"""
        # Validate credentials are set
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError(
                "Google OAuth credentials are not configured. "
                "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file. "
                "See GOOGLE_OAUTH_SETUP.md for setup instructions."
            )
        
        # Validate credentials format (basic check)
        if not settings.GOOGLE_CLIENT_ID.strip() or not settings.GOOGLE_CLIENT_SECRET.strip():
            raise ValueError(
                "Google OAuth credentials are empty. "
                "Please set valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file."
            )
        
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri or settings.GOOGLE_REDIRECT_URI],
            }
        }
        
        try:
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=redirect_uri or settings.GOOGLE_REDIRECT_URI,
            )
            return flow
        except Exception as e:
            raise ValueError(
                f"Failed to create Google OAuth flow. "
                f"This usually means GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is invalid. "
                f"Error: {str(e)}"
            ) from e
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get the Google OAuth authorization URL"""
        flow = self._get_oauth_flow()
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent to get refresh token
            state=state,
        )
        return authorization_url
    
    def get_user_info(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchange authorization code for tokens and get user info"""
        actual_redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
        flow = self._get_oauth_flow(actual_redirect_uri)
        
        try:
            # Exchange code for tokens - must use the same redirect_uri
            flow.fetch_token(code=code)
            credentials = flow.credentials
        except (OAuthError, GoogleAuthError) as e:
            error_msg = str(e)
            if "invalid_client" in error_msg.lower() or "401" in error_msg:
                raise ValueError(
                    "Google OAuth Error 401: invalid_client. "
                    "This means your GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is incorrect. "
                    "Please verify:\n"
                    "1. GOOGLE_CLIENT_ID matches the Client ID in Google Cloud Console\n"
                    "2. GOOGLE_CLIENT_SECRET matches the Client Secret in Google Cloud Console\n"
                    "3. The OAuth 2.0 Client ID is enabled in Google Cloud Console\n"
                    "4. The redirect URI in your .env matches what's configured in Google Cloud Console\n"
                    f"   Current redirect URI: {actual_redirect_uri}\n"
                    f"Original error: {error_msg}"
                ) from e
            elif "redirect_uri_mismatch" in error_msg.lower():
                raise ValueError(
                    f"Redirect URI mismatch. "
                    f"Your redirect URI '{actual_redirect_uri}' must exactly match "
                    f"one of the authorized redirect URIs in Google Cloud Console. "
                    f"Original error: {error_msg}"
                ) from e
            else:
                raise ValueError(
                    f"Failed to exchange authorization code for tokens: {error_msg}"
                ) from e
        
        try:
            # Get user info using the token
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
        except HttpError as e:
            raise ValueError(
                f"Failed to get user info from Google: {str(e)}"
            ) from e
        
        return {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "google_id": user_info.get("id"),
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh a Google OAuth token"""
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
            )
            creds.refresh(Request())
            
            return {
                "access_token": creds.token,
                "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
            }
        except RefreshError as e:
            error_msg = str(e)
            if "invalid_client" in error_msg.lower() or "401" in error_msg:
                raise ValueError(
                    "Google OAuth Error 401: invalid_client when refreshing token. "
                    "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET may be incorrect. "
                    f"Original error: {error_msg}"
                ) from e
            # If token is invalid/expired, return None (caller will handle)
            return None
        except Exception as e:
            # Log other errors but don't raise - let caller handle
            return None

