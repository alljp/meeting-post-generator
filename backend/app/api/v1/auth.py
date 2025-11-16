from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional, List
from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_user
from app.models.user import User, GoogleAccount
from app.auth.factory import OAuthProviderFactory
from app.utils.jwt import create_access_token
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    name: str | None
    picture: str | None


class GoogleAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    google_email: str
    is_active: bool
    created_at: datetime | None


@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth flow (for initial login)"""
    # Always use the backend redirect URI (must match Google Console config)
    # Google will redirect to our backend callback, which then redirects to frontend
    try:
        provider = OAuthProviderFactory.create("google")
        authorization_url = provider.get_authorization_url()
        return {"authorization_url": authorization_url}
    except ValueError as e:
        # Pass through validation errors with detailed messages
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google OAuth configuration error: {str(e)}"
        )


@router.get("/google/connect")
async def google_connect(
    current_user: User = Depends(get_current_user)
):
    """Initiate Google OAuth flow to connect additional account (requires auth)"""
    try:
        # Pass user token in state for callback authentication
        # Use a longer expiry for OAuth state token (30 minutes should be enough for OAuth flow)
        from datetime import timedelta
        user_token = create_access_token(
            data={"sub": str(current_user.id)},
            expires_delta=timedelta(minutes=30)
        )
        provider = OAuthProviderFactory.create("google")
        authorization_url = provider.get_authorization_url(state=user_token)
        return {"authorization_url": authorization_url}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google OAuth configuration error: {str(e)}"
        )


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Google OAuth callback - handles both login and connect flows"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Google OAuth callback received. State: {state[:50] if state else None}...")
        
        # Always use the backend redirect URI (must match what was used in login)
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        logger.debug(f"Using redirect URI: {redirect_uri}")
        
        # Get user info from Google
        provider = OAuthProviderFactory.create("google")
        logger.debug("Exchanging authorization code for tokens...")
        google_user_info = provider.get_user_info(code, redirect_uri)
        logger.info(f"Successfully obtained user info. Email: {google_user_info.get('email')}")
        logger.debug(f"Google user info keys: {list(google_user_info.keys())}")
        
        if not google_user_info.get("email"):
            logger.error(f"Missing email in Google user info. Available keys: {list(google_user_info.keys())}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user email from Google"
            )
        
        if not google_user_info.get("access_token"):
            logger.error(f"Missing access_token in Google user info. Available keys: {list(google_user_info.keys())}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from Google"
            )
        
        email = google_user_info["email"]
        google_email = google_user_info["email"]
        
        # Check if this is a connect flow (state contains user JWT token) or login flow
        # Try to decode state as JWT - if it succeeds and has a valid user ID, it's a connect flow
        # Otherwise, treat it as login flow (state might be Google's CSRF token)
        is_connect_flow = False
        user_id = None
        
        if state:
            from app.utils.jwt import decode_access_token
            payload = decode_access_token(state)
            
            # If we successfully decoded a JWT payload, we're in connect flow
            # Check if it's valid (has user ID and user exists)
            if payload and payload.get("sub"):
                try:
                    user_id = int(payload.get("sub"))
                    # Verify user exists
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user:
                        is_connect_flow = True
                    else:
                        # State token decoded successfully but user doesn't exist - this is an error
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="OAuth callback failed: User not found. Invalid state token."
                        )
                except (ValueError, TypeError):
                    # Invalid user ID format in decoded token - treat as login flow
                    # (This could be a malformed token, but we can't distinguish from Google's CSRF)
                    pass
            elif payload is None:
                # State was provided but we couldn't decode it
                # JWT tokens always have exactly 2 dots (header.payload.signature)
                # Google OAuth CSRF tokens are random alphanumeric strings with no dots
                # If state has dots, it's likely a malformed JWT token for connect flow - return error
                # If state has no dots, it's likely Google's CSRF token - treat as login flow
                if '.' in state:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="OAuth callback failed: Invalid state token. Please try connecting again."
                    )
                # No dots means it's likely Google's CSRF token - treat as login flow
        
        if is_connect_flow:
            # Connect flow: Add account to existing user
            # user already retrieved and verified above in the try block
            # Check if Google account already linked to this user
            result = await db.execute(
                select(GoogleAccount).where(
                    GoogleAccount.google_email == google_email,
                    GoogleAccount.user_id == user.id
                )
            )
            google_account = result.scalar_one_or_none()
            
            if google_account:
                # Update existing Google account
                google_account.access_token = google_user_info["access_token"]
                google_account.refresh_token = google_user_info.get("refresh_token")
                token_expiry = google_user_info.get("token_expiry")
                if token_expiry:
                    try:
                        google_account.token_expires_at = datetime.fromisoformat(token_expiry)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse token_expiry '{token_expiry}': {e}")
                        google_account.token_expires_at = None
                else:
                    google_account.token_expires_at = None
                google_account.is_active = True
            else:
                # Create new Google account link
                token_expiry = google_user_info.get("token_expiry")
                token_expires_at = None
                if token_expiry:
                    try:
                        token_expires_at = datetime.fromisoformat(token_expiry)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse token_expiry '{token_expiry}': {e}")
                        token_expires_at = None
                
                google_account = GoogleAccount(
                    user_id=user.id,
                    google_email=google_email,
                    access_token=google_user_info["access_token"],
                    refresh_token=google_user_info.get("refresh_token"),
                    token_expires_at=token_expires_at,
                )
                db.add(google_account)
            
            await db.commit()
            
            # Redirect to frontend settings page with success message
            frontend_url = f"{settings.FRONTEND_URL}/settings?connected=google"
            return RedirectResponse(url=frontend_url)
        else:
            # Login flow: Create/update user and return JWT (state is either None or Google's CSRF token)
            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if user is None:
                # Create new user
                user = User(
                    email=email,
                    name=google_user_info.get("name"),
                    picture=google_user_info.get("picture"),
                )
                db.add(user)
                await db.flush()  # Get user ID
            
            # Check if Google account already linked
            result = await db.execute(
                select(GoogleAccount).where(
                    GoogleAccount.google_email == google_email,
                    GoogleAccount.user_id == user.id
                )
            )
            google_account = result.scalar_one_or_none()
            
            if google_account:
                # Update existing Google account
                google_account.access_token = google_user_info["access_token"]
                google_account.refresh_token = google_user_info.get("refresh_token")
                token_expiry = google_user_info.get("token_expiry")
                if token_expiry:
                    try:
                        google_account.token_expires_at = datetime.fromisoformat(token_expiry)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse token_expiry '{token_expiry}': {e}")
                        google_account.token_expires_at = None
                else:
                    google_account.token_expires_at = None
                google_account.is_active = True
            else:
                # Create new Google account link
                token_expiry = google_user_info.get("token_expiry")
                token_expires_at = None
                if token_expiry:
                    try:
                        token_expires_at = datetime.fromisoformat(token_expiry)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse token_expiry '{token_expiry}': {e}")
                        token_expires_at = None
                
                google_account = GoogleAccount(
                    user_id=user.id,
                    google_email=google_email,
                    access_token=google_user_info["access_token"],
                    refresh_token=google_user_info.get("refresh_token"),
                    token_expires_at=token_expires_at,
                )
                db.add(google_account)
            
            await db.commit()
            await db.refresh(user)
            
            # Create JWT token (user.id is int, JWT expects it as int)
            access_token = create_access_token(data={"sub": str(user.id)})
            
            # Redirect to frontend with token
            frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
            return RedirectResponse(url=frontend_url)
        
    except ValueError as e:
        # Pass through validation errors with detailed messages
        logger.error(f"ValueError in Google OAuth callback: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in Google OAuth callback: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user


@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Logged out successfully"}


@router.get("/google/accounts", response_model=List[GoogleAccountResponse])
async def list_google_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List connected Google accounts for current user"""
    result = await db.execute(
        select(GoogleAccount).where(GoogleAccount.user_id == current_user.id)
    )
    accounts = result.scalars().all()
    
    return [
        GoogleAccountResponse(
            id=account.id,
            google_email=account.google_email,
            is_active=account.is_active,
            created_at=account.created_at
        )
        for account in accounts
    ]


@router.delete("/google/accounts/{account_id}")
async def disconnect_google_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect a Google account"""
    result = await db.execute(
        select(GoogleAccount).where(
            GoogleAccount.id == account_id,
            GoogleAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google account not found"
        )
    
    # Soft delete: set is_active to False to preserve historical events
    account.is_active = False
    await db.commit()
    
    return {"message": "Google account disconnected successfully"}


@router.get("/linkedin/login")
async def linkedin_login(
    current_user: User = Depends(get_current_user)
):
    """Initiate LinkedIn OAuth flow"""
    # Pass user token in state for callback authentication
    # Use a longer expiry for OAuth state token (30 minutes should be enough for OAuth flow)
    from app.utils.jwt import create_access_token
    from datetime import timedelta
    user_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=30)
    )
    provider = OAuthProviderFactory.create("linkedin")
    authorization_url = provider.get_authorization_url(state=user_token)
    return {"authorization_url": authorization_url}


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """LinkedIn OAuth callback - connects LinkedIn account to user"""
    try:
        # Extract user token from state (passed during OAuth initiation)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing state parameter"
            )
        
        # URL decode state in case it was encoded
        import urllib.parse
        state = urllib.parse.unquote(state)
        
        # Decode user token from state
        from app.utils.jwt import decode_access_token
        import logging
        logger = logging.getLogger(__name__)
        
        payload = decode_access_token(state)
        if not payload:
            logger.warning(f"Failed to decode state token. State length: {len(state) if state else 0}")
            # Check if token might be expired or invalid format
            if state and not state.startswith('eyJ'):  # JWT tokens start with 'eyJ'
                logger.error(f"State doesn't appear to be a JWT token: {state[:50]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired state token. Please try connecting again."
            )
        
        user_id = int(payload.get("sub"))
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get LinkedIn user info
        provider = OAuthProviderFactory.create("linkedin")
        linkedin_info = provider.get_user_info(code)
        
        if not linkedin_info.get("linkedin_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get LinkedIn user ID"
            )
        
        from app.models.social_account import SocialAccount, SocialPlatform
        
        # Check if LinkedIn account already linked
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user.id,
                SocialAccount.platform == SocialPlatform.LINKEDIN
            )
        )
        social_account = result.scalar_one_or_none()
        
        if social_account:
            # Update existing LinkedIn account
            social_account.account_id = linkedin_info["linkedin_id"]
            social_account.account_name = linkedin_info.get("name")
            social_account.access_token = linkedin_info["access_token"]
            if linkedin_info.get("token_expiry"):
                social_account.token_expires_at = datetime.fromisoformat(
                    linkedin_info["token_expiry"]
                )
            social_account.is_active = True
        else:
            # Create new LinkedIn account link
            social_account = SocialAccount(
                user_id=user.id,
                platform=SocialPlatform.LINKEDIN,
                account_id=linkedin_info["linkedin_id"],
                account_name=linkedin_info.get("name"),
                access_token=linkedin_info["access_token"],
                token_expires_at=datetime.fromisoformat(linkedin_info["token_expiry"])
                if linkedin_info.get("token_expiry") else None,
            )
            db.add(social_account)
        
        await db.commit()
        await db.refresh(social_account)
        
        # Redirect to frontend settings page
        frontend_url = f"{settings.FRONTEND_URL}/settings?connected=linkedin"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LinkedIn OAuth callback failed: {str(e)}"
        )


@router.get("/facebook/login")
async def facebook_login(
    current_user: User = Depends(get_current_user)
):
    """Initiate Facebook OAuth flow"""
    # Pass user token in state for callback authentication
    # Use a longer expiry for OAuth state token (30 minutes should be enough for OAuth flow)
    from app.utils.jwt import create_access_token
    from datetime import timedelta
    user_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=30)
    )
    provider = OAuthProviderFactory.create("facebook")
    authorization_url = provider.get_authorization_url(state=user_token)
    return {"authorization_url": authorization_url}


@router.get("/facebook/callback")
async def facebook_callback(
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Facebook OAuth callback - connects Facebook account to user"""
    try:
        # Extract user token from state (passed during OAuth initiation)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing state parameter"
            )
        
        # URL decode state in case it was encoded
        import urllib.parse
        state = urllib.parse.unquote(state)
        
        # Decode user token from state
        from app.utils.jwt import decode_access_token
        import logging
        logger = logging.getLogger(__name__)
        
        payload = decode_access_token(state)
        if not payload:
            logger.warning(f"Failed to decode state token. State length: {len(state) if state else 0}")
            # Check if token might be expired or invalid format
            if state and not state.startswith('eyJ'):  # JWT tokens start with 'eyJ'
                logger.error(f"State doesn't appear to be a JWT token: {state[:50]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired state token. Please try connecting again."
            )
        
        user_id = int(payload.get("sub"))
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get Facebook user info
        provider = OAuthProviderFactory.create("facebook")
        facebook_info = provider.get_user_info(code)
        
        if not facebook_info.get("facebook_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get Facebook user ID"
            )
        
        from app.models.social_account import SocialAccount, SocialPlatform
        
        # Check if Facebook account already linked
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user.id,
                SocialAccount.platform == SocialPlatform.FACEBOOK
            )
        )
        social_account = result.scalar_one_or_none()
        
        if social_account:
            # Update existing Facebook account
            social_account.account_id = facebook_info["facebook_id"]
            social_account.account_name = facebook_info.get("name")
            social_account.access_token = facebook_info["access_token"]
            if facebook_info.get("token_expiry"):
                social_account.token_expires_at = datetime.fromisoformat(
                    facebook_info["token_expiry"]
                )
            social_account.is_active = True
        else:
            # Create new Facebook account link
            social_account = SocialAccount(
                user_id=user.id,
                platform=SocialPlatform.FACEBOOK,
                account_id=facebook_info["facebook_id"],
                account_name=facebook_info.get("name"),
                access_token=facebook_info["access_token"],
                token_expires_at=datetime.fromisoformat(facebook_info["token_expiry"])
                if facebook_info.get("token_expiry") else None,
            )
            db.add(social_account)
        
        await db.commit()
        await db.refresh(social_account)
        
        # Redirect to frontend settings page
        frontend_url = f"{settings.FRONTEND_URL}/settings?connected=facebook"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Facebook OAuth callback failed: {str(e)}"
        )

