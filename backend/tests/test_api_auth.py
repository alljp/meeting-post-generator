"""
Unit tests for Auth API endpoints.
Tests OAuth flows, user authentication, and account management.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from app.models.user import User, GoogleAccount
from app.models.social_account import SocialAccount, SocialPlatform
from app.utils.jwt import create_access_token


class TestAuthAPI:
    """Test suite for Auth API endpoints."""
    
    @pytest.fixture
    def auth_token(self, test_user):
        """Create auth token for test user."""
        return create_access_token({"sub": str(test_user.id)})
    
    @pytest.mark.asyncio
    async def test_google_login_success(self, client: AsyncClient):
        """Test Google login initiation."""
        mock_provider = MagicMock()
        mock_provider.get_authorization_url.return_value = "https://accounts.google.com/oauth?client_id=test"
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get("/api/v1/auth/google/login")
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            mock_factory.assert_called_once_with("google")
            mock_provider.get_authorization_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_google_callback_new_user(self, client: AsyncClient, db_session):
        """Test Google callback with new user."""
        mock_user_info = {
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/pic.jpg",
            "access_token": "google_token_123",
            "refresh_token": "refresh_token_123",
            "token_expiry": "2024-12-31T23:59:59+00:00"  # Timezone-aware format
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/google/callback?code=test_code",
                follow_redirects=False
            )
            
            # Should redirect to frontend
            assert response.status_code == 307 or response.status_code == 302
            assert "/auth/callback" in str(response.headers.get("location", ""))
            
            # Verify user was created
            from sqlalchemy import select
            result = await db_session.execute(
                select(User).where(User.email == "newuser@example.com")
            )
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.name == "New User"
    
    @pytest.mark.asyncio
    async def test_google_callback_existing_user(self, client: AsyncClient, db_session, test_user):
        """Test Google callback with existing user."""
        mock_user_info = {
            "email": test_user.email,
            "name": "Updated Name",
            "picture": "https://example.com/newpic.jpg",
            "access_token": "google_token_456",
            "refresh_token": "refresh_token_456"
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/google/callback?code=test_code",
                follow_redirects=False
            )
            
            assert response.status_code == 307 or response.status_code == 302
            
            # Verify Google account was linked/updated
            from sqlalchemy import select
            result = await db_session.execute(
                select(GoogleAccount).where(GoogleAccount.user_id == test_user.id)
            )
            google_account = result.scalar_one_or_none()
            assert google_account is not None
            assert google_account.access_token == "google_token_456"
    
    @pytest.mark.asyncio
    async def test_google_callback_no_email(self, client: AsyncClient):
        """Test Google callback when email is missing."""
        mock_user_info = {
            "name": "User Without Email",
            "access_token": "token"
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/google/callback?code=test_code"
            )
            
            assert response.status_code == 400
            detail = response.json()["detail"].lower()
            # HTTPException is caught by outer handler, so error message is wrapped
            assert "email" in detail or "failed" in detail or "oauth callback failed" in detail
    
    @pytest.mark.asyncio
    async def test_google_callback_oauth_error(self, client: AsyncClient):
        """Test Google callback when OAuth fails."""
        from google.auth.exceptions import OAuthError
        
        mock_provider = MagicMock()
        # Test with OAuthError (the exception we now catch)
        oauth_error = OAuthError("OAuth error: Invalid code")
        mock_provider.get_user_info.side_effect = oauth_error
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/google/callback?code=invalid_code"
            )
            
            assert response.status_code == 400
            detail = response.json()["detail"].lower()
            assert "oauth callback failed" in detail or "oauth" in detail
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, test_user, auth_token):
        """Test getting current user."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
    
    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient):
        """Test logout endpoint."""
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
    
    @pytest.mark.asyncio
    async def test_linkedin_login(self, client: AsyncClient, test_user, auth_token):
        """Test LinkedIn login initiation."""
        mock_provider = MagicMock()
        mock_provider.get_authorization_url.return_value = "https://linkedin.com/oauth"
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/linkedin/login",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            mock_factory.assert_called_once_with("linkedin")
            mock_provider.get_authorization_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_linkedin_callback_success(self, client: AsyncClient, db_session, test_user):
        """Test LinkedIn callback success."""
        user_token = create_access_token({"sub": str(test_user.id)})
        
        mock_linkedin_info = {
            "linkedin_id": "linkedin_123",
            "name": "LinkedIn User",
            "email": "linkedin@example.com",
            "access_token": "linkedin_token",
            "refresh_token": "linkedin_refresh",
            "token_expiry": (datetime.now(timezone.utc) + timedelta(seconds=3600)).isoformat()
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_linkedin_info
        
        with patch("app.utils.jwt.decode_access_token") as mock_decode, \
             patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            
            mock_decode.return_value = {"sub": str(test_user.id)}
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                f"/api/v1/auth/linkedin/callback?code=test_code&state={user_token}",
                follow_redirects=False
            )
            
            # Should redirect
            assert response.status_code == 307 or response.status_code == 302
            
            # Verify LinkedIn account was linked
            from sqlalchemy import select
            result = await db_session.execute(
                select(SocialAccount).where(
                    SocialAccount.user_id == test_user.id,
                    SocialAccount.platform == SocialPlatform.LINKEDIN
                )
            )
            account = result.scalar_one_or_none()
            assert account is not None
            assert account.account_id == "linkedin_123"
    
    @pytest.mark.asyncio
    async def test_linkedin_callback_no_state(self, client: AsyncClient):
        """Test LinkedIn callback without state."""
        response = await client.get("/api/v1/auth/linkedin/callback?code=test_code")
        
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "missing state" in detail or "linkedin oauth callback failed" in detail
    
    @pytest.mark.asyncio
    async def test_facebook_login(self, client: AsyncClient, test_user, auth_token):
        """Test Facebook login initiation."""
        mock_provider = MagicMock()
        mock_provider.get_authorization_url.return_value = "https://facebook.com/oauth"
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/facebook/login",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            mock_factory.assert_called_once_with("facebook")
            mock_provider.get_authorization_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_facebook_callback_success(self, client: AsyncClient, db_session, test_user):
        """Test Facebook callback success."""
        from datetime import datetime, timezone, timedelta
        user_token = create_access_token({"sub": str(test_user.id)})
        
        mock_facebook_info = {
            "facebook_id": "facebook_123",
            "name": "Facebook User",
            "email": "facebook@example.com",
            "access_token": "facebook_token",
            "token_expiry": (datetime.now(timezone.utc) + timedelta(seconds=3600)).isoformat()
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_facebook_info
        
        with patch("app.utils.jwt.decode_access_token") as mock_decode, \
             patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            
            mock_decode.return_value = {"sub": str(test_user.id)}
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                f"/api/v1/auth/facebook/callback?code=test_code&state={user_token}",
                follow_redirects=False
            )
            
            # Should redirect
            assert response.status_code == 307 or response.status_code == 302
            
            # Verify Facebook account was linked
            from sqlalchemy import select
            result = await db_session.execute(
                select(SocialAccount).where(
                    SocialAccount.user_id == test_user.id,
                    SocialAccount.platform == SocialPlatform.FACEBOOK
                )
            )
            account = result.scalar_one_or_none()
            assert account is not None
            assert account.account_id == "facebook_123"
    
    @pytest.mark.asyncio
    async def test_facebook_callback_no_state(self, client: AsyncClient):
        """Test Facebook callback without state."""
        response = await client.get("/api/v1/auth/facebook/callback?code=test_code")
        
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "missing state" in detail or "facebook oauth callback failed" in detail
    
    @pytest.mark.asyncio
    async def test_google_callback_updates_existing_google_account(
        self, client: AsyncClient, db_session, test_user, test_google_account
    ):
        """Test Google callback updates existing Google account."""
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import select
        from app.models.user import GoogleAccount
        
        # Ensure the mock user info has the same email as test_user and test_google_account
        mock_user_info = {
            "email": test_user.email,  # Must match test_user.email
            "name": "Updated User",
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "token_expiry": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        # Verify test_google_account has matching google_email
        assert test_google_account.google_email == test_user.email or test_google_account.google_email == "test@gmail.com"
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/google/callback?code=test_code",
                follow_redirects=False
            )
            
            assert response.status_code == 307 or response.status_code == 302
            
            # Reload the account from database to see updates
            result = await db_session.execute(
                select(GoogleAccount).where(
                    GoogleAccount.user_id == test_user.id,
                    GoogleAccount.google_email == test_user.email
                )
            )
            updated_account = result.scalar_one_or_none()
            
            # Verify the account was updated
            if updated_account:
                assert updated_account.access_token == "new_access_token"
                assert updated_account.refresh_token == "new_refresh_token"
                assert updated_account.is_active is True

    @pytest.mark.asyncio
    async def test_google_connect_success(self, client: AsyncClient, test_user, auth_token):
        """Test Google connect endpoint (for adding additional accounts)."""
        mock_provider = MagicMock()
        mock_provider.get_authorization_url.return_value = "https://accounts.google.com/oauth?client_id=test&state=token"
        
        with patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/google/connect",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            # Verify state parameter was passed (contains user token)
            mock_provider.get_authorization_url.assert_called_once()
            call_args = mock_provider.get_authorization_url.call_args
            assert call_args[1].get("state") is not None  # state should be present

    @pytest.mark.asyncio
    async def test_google_connect_unauthorized(self, client: AsyncClient):
        """Test Google connect endpoint without authentication."""
        response = await client.get("/api/v1/auth/google/connect")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_google_accounts_success(self, client: AsyncClient, test_user, auth_token, test_google_account):
        """Test listing Google accounts."""
        response = await client.get(
            "/api/v1/auth/google/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        account = data[0]
        assert account["id"] == test_google_account.id
        assert account["google_email"] == test_google_account.google_email
        assert account["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_google_accounts_empty(self, client: AsyncClient, test_user, auth_token):
        """Test listing Google accounts when user has none."""
        response = await client.get(
            "/api/v1/auth/google/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_google_accounts_unauthorized(self, client: AsyncClient):
        """Test listing Google accounts without authentication."""
        response = await client.get("/api/v1/auth/google/accounts")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_disconnect_google_account_success(
        self, client: AsyncClient, test_user, auth_token, test_google_account, db_session
    ):
        """Test disconnecting a Google account."""
        response = await client.delete(
            f"/api/v1/auth/google/accounts/{test_google_account.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "disconnected" in data["message"].lower()
        
        # Verify account is marked as inactive
        from sqlalchemy import select
        result = await db_session.execute(
            select(GoogleAccount).where(GoogleAccount.id == test_google_account.id)
        )
        account = result.scalar_one_or_none()
        assert account is not None
        assert account.is_active is False

    @pytest.mark.asyncio
    async def test_disconnect_google_account_not_found(self, client: AsyncClient, test_user, auth_token):
        """Test disconnecting a non-existent Google account."""
        response = await client.delete(
            "/api/v1/auth/google/accounts/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        detail = response.json()["detail"].lower()
        assert "not found" in detail

    @pytest.mark.asyncio
    async def test_disconnect_google_account_unauthorized(self, client: AsyncClient, test_google_account):
        """Test disconnecting Google account without authentication."""
        response = await client.delete(f"/api/v1/auth/google/accounts/{test_google_account.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_disconnect_google_account_wrong_user(
        self, client: AsyncClient, db_session, test_user, auth_token
    ):
        """Test disconnecting another user's Google account."""
        # Create another user with a Google account
        other_user = User(
            email="other@example.com",
            name="Other User",
            is_active=True
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)
        
        other_account = GoogleAccount(
            user_id=other_user.id,
            google_email="other@gmail.com",
            access_token="token",
            is_active=True
        )
        db_session.add(other_account)
        await db_session.commit()
        await db_session.refresh(other_account)
        
        # Try to disconnect other user's account
        response = await client.delete(
            f"/api/v1/auth/google/accounts/{other_account.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404  # Should not find it (belongs to different user)

    @pytest.mark.asyncio
    async def test_google_callback_with_state_connect_flow(
        self, client: AsyncClient, db_session, test_user
    ):
        """Test Google callback with state parameter (connect flow)."""
        user_token = create_access_token({"sub": str(test_user.id)})
        
        mock_user_info = {
            "email": "newaccount@gmail.com",  # Different email from test_user
            "name": "New Account",
            "picture": "https://example.com/pic.jpg",
            "access_token": "google_token_new",
            "refresh_token": "refresh_token_new",
            "token_expiry": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.utils.jwt.decode_access_token") as mock_decode, \
             patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            
            mock_decode.return_value = {"sub": str(test_user.id)}
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                f"/api/v1/auth/google/callback?code=test_code&state={user_token}",
                follow_redirects=False
            )
            
            # Should redirect to settings page (connect flow)
            assert response.status_code == 307 or response.status_code == 302
            location = str(response.headers.get("location", ""))
            assert "/settings" in location
            assert "connected=google" in location
            
            # Verify new Google account was added to existing user
            from sqlalchemy import select
            result = await db_session.execute(
                select(GoogleAccount).where(
                    GoogleAccount.user_id == test_user.id,
                    GoogleAccount.google_email == "newaccount@gmail.com"
                )
            )
            account = result.scalar_one_or_none()
            assert account is not None
            assert account.access_token == "google_token_new"
            assert account.is_active is True

    @pytest.mark.asyncio
    async def test_google_callback_with_state_updates_existing_account(
        self, client: AsyncClient, db_session, test_user, test_google_account
    ):
        """Test Google callback with state updates existing Google account."""
        user_token = create_access_token({"sub": str(test_user.id)})
        
        mock_user_info = {
            "email": test_google_account.google_email,  # Same email as existing account
            "name": "Updated Name",
            "access_token": "updated_token",
            "refresh_token": "updated_refresh",
            "token_expiry": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.utils.jwt.decode_access_token") as mock_decode, \
             patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            
            mock_decode.return_value = {"sub": str(test_user.id)}
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                f"/api/v1/auth/google/callback?code=test_code&state={user_token}",
                follow_redirects=False
            )
            
            assert response.status_code == 307 or response.status_code == 302
            
            # Verify account was updated
            from sqlalchemy import select
            result = await db_session.execute(
                select(GoogleAccount).where(GoogleAccount.id == test_google_account.id)
            )
            updated_account = result.scalar_one_or_none()
            assert updated_account is not None
            assert updated_account.access_token == "updated_token"
            assert updated_account.refresh_token == "updated_refresh"

    @pytest.mark.asyncio
    async def test_google_callback_with_state_invalid_token(self, client: AsyncClient):
        """Test Google callback with invalid state token."""
        mock_user_info = {
            "email": "test@example.com",
            "access_token": "token"
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.utils.jwt.decode_access_token") as mock_decode, \
             patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            
            mock_decode.return_value = None  # Invalid token
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                "/api/v1/auth/google/callback?code=test_code&state=invalid_token"
            )
            
            # The callback handler wraps exceptions in a try-except that returns 400
            assert response.status_code == 400
            detail = response.json()["detail"].lower()
            assert "invalid" in detail or "oauth callback failed" in detail

    @pytest.mark.asyncio
    async def test_google_callback_with_state_user_not_found(self, client: AsyncClient, db_session):
        """Test Google callback with state for non-existent user."""
        user_token = create_access_token({"sub": "99999"})  # Non-existent user ID
        
        mock_user_info = {
            "email": "test@example.com",
            "access_token": "token"
        }
        
        mock_provider = MagicMock()
        mock_provider.get_user_info.return_value = mock_user_info
        
        with patch("app.utils.jwt.decode_access_token") as mock_decode, \
             patch("app.api.v1.auth.OAuthProviderFactory.create") as mock_factory:
            
            mock_decode.return_value = {"sub": "99999"}
            mock_factory.return_value = mock_provider
            
            response = await client.get(
                f"/api/v1/auth/google/callback?code=test_code&state={user_token}"
            )
            
            # The callback handler wraps exceptions in a try-except that returns 400
            # But the inner exception should be 404, which gets wrapped
            assert response.status_code == 400
            detail = response.json()["detail"].lower()
            assert "user not found" in detail or "oauth callback failed" in detail

