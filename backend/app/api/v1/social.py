from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.social_account import SocialAccount, SocialPlatform
from app.models.generated_post import GeneratedPost, PostStatus
from app.services.social.factory import SocialMediaPosterFactory
from app.auth.factory import OAuthProviderFactory
from app.utils.jwt import create_access_token

router = APIRouter()


class SocialAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    platform: str
    account_name: str | None
    is_active: bool
    created_at: datetime | None


@router.get("/accounts", response_model=List[SocialAccountResponse])
async def list_social_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List connected social media accounts"""
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.user_id == current_user.id)
    )
    accounts = result.scalars().all()
    
    return [
        SocialAccountResponse(
            id=account.id,
            platform=account.platform.value,
            account_name=account.account_name,
            is_active=account.is_active,
            created_at=account.created_at
        )
        for account in accounts
    ]


@router.get("/linkedin/connect")
async def connect_linkedin(
    current_user: User = Depends(get_current_user)
):
    """Initiate LinkedIn OAuth connection"""
    # Pass user token in state for callback authentication
    user_token = create_access_token(data={"sub": str(current_user.id)})
    provider = OAuthProviderFactory.create("linkedin")
    authorization_url = provider.get_authorization_url(state=user_token)
    return {"authorization_url": authorization_url}


@router.get("/facebook/connect")
async def connect_facebook(
    current_user: User = Depends(get_current_user)
):
    """Initiate Facebook OAuth connection"""
    # Pass user token in state for callback authentication
    user_token = create_access_token(data={"sub": str(current_user.id)})
    provider = OAuthProviderFactory.create("facebook")
    authorization_url = provider.get_authorization_url(state=user_token)
    return {"authorization_url": authorization_url}


@router.delete("/accounts/{account_id}")
async def disconnect_social_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect a social media account"""
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found"
        )
    
    # Soft delete: set is_active to False to preserve historical posts
    account.is_active = False
    await db.commit()
    
    return {"message": "Account disconnected successfully"}


@router.post("/posts/{post_id}/post")
async def post_to_social(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Post generated post to social media"""
    # Get the generated post
    result = await db.execute(
        select(GeneratedPost)
        .where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Verify the post belongs to a meeting owned by the user
    from app.models.meeting import Meeting
    meeting_result = await db.execute(
        select(Meeting).where(Meeting.id == post.meeting_id)
    )
    meeting = meeting_result.scalar_one_or_none()
    
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to post this"
        )
    
    # Get the user's social account for this platform
    platform = SocialPlatform(post.platform.lower())
    account_result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == platform,
            SocialAccount.is_active == True
        )
    )
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active {platform.value} account connected. Please connect your account in settings."
        )
    
    # Check if token is expired (simplified check)
    if account.token_expires_at and account.token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Social media account token expired. Please reconnect your account."
        )
    
    try:
        # Post to social media using factory
        poster = SocialMediaPosterFactory.create(platform)
        post_result = await poster.post(
            access_token=account.access_token,
            content=post.content
        )
        
        # Update post status
        post.status = PostStatus.POSTED
        post.posted_at = datetime.now(timezone.utc)
        post.post_id = post_result.get("post_id")
        post.error_message = None
        
        await db.commit()
        await db.refresh(post)
        
        return {
            "message": f"Post published to {platform.value} successfully",
            "post_id": post_result.get("post_id"),
            "status": post.status.value
        }
        
    except Exception as e:
        # Update post status to failed
        post.status = PostStatus.FAILED
        post.error_message = str(e)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post to {platform.value}: {str(e)}"
        )


@router.get("/posts/{post_id}")
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a generated post by ID"""
    result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Verify the post belongs to a meeting owned by the user
    from app.models.meeting import Meeting
    meeting_result = await db.execute(
        select(Meeting).where(Meeting.id == post.meeting_id)
    )
    meeting = meeting_result.scalar_one_or_none()
    
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this post"
        )
    
    return {
        "id": post.id,
        "meeting_id": post.meeting_id,
        "platform": post.platform,
        "content": post.content,
        "status": post.status.value,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "posted_at": post.posted_at.isoformat() if post.posted_at else None,
        "post_id": post.post_id,
        "error_message": post.error_message,
    }
