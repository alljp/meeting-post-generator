from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.meeting import Meeting, Attendee

router = APIRouter()


class AttendeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: Optional[str]


class MeetingListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    platform: str
    transcript_available: bool
    attendees: List[AttendeeResponse]


class MeetingDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    platform: str
    transcript: Optional[str]
    transcript_available: bool
    recording_url: Optional[str]
    email: Optional[str]
    email_generated_at: Optional[datetime]
    attendees: List[AttendeeResponse]
    recall_bot_id: str


@router.get("", response_model=List[MeetingListItemResponse])
async def list_meetings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: Optional[int] = Query(default=50, ge=1, le=100),
    offset: Optional[int] = Query(default=0, ge=0)
):
    """List past meetings for the current user"""
    result = await db.execute(
        select(Meeting)
        .where(
            and_(
                Meeting.user_id == current_user.id,
                Meeting.end_time < datetime.now(timezone.utc)
            )
        )
        .options(selectinload(Meeting.attendees))
        .order_by(desc(Meeting.start_time))
        .limit(limit)
        .offset(offset)
    )
    
    meetings = result.scalars().all()
    return meetings


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get meeting details"""
    result = await db.execute(
        select(Meeting)
        .where(
            and_(
                Meeting.id == meeting_id,
                Meeting.user_id == current_user.id
            )
        )
        .options(selectinload(Meeting.attendees))
    )
    
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    return meeting


@router.get("/{meeting_id}/transcript")
async def get_transcript(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get meeting transcript"""
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == meeting_id,
                Meeting.user_id == current_user.id
            )
        )
    )
    
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if not meeting.transcript_available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not available yet"
        )
    
    return {"transcript": meeting.transcript or ""}


@router.get("/{meeting_id}/email")
async def get_email(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated follow-up email"""
    from app.services.ai.service import ai_service
    
    result = await db.execute(
        select(Meeting)
        .where(
            and_(
                Meeting.id == meeting_id,
                Meeting.user_id == current_user.id
            )
        )
        .options(selectinload(Meeting.attendees))
    )
    
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if not meeting.transcript_available or not meeting.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript not available. Cannot generate email without transcript."
        )
    
    # If email already exists, return it
    if meeting.email:
        return {"email": meeting.email}
    
    # Prepare attendees data
    attendees_data = [
        {"name": attendee.name, "email": attendee.email}
        for attendee in meeting.attendees
    ]
    
    # Generate email
    email_content = await ai_service.generate_follow_up_email(
        transcript=meeting.transcript,
        meeting_title=meeting.title,
        attendees=attendees_data,
        meeting_date=meeting.start_time.strftime("%B %d, %Y")
    )
    
    # Check if generation was successful (not an error message)
    if email_content and not email_content.startswith("Error generating email"):
        # Save email to database
        from datetime import datetime, timezone
        meeting.email = email_content
        meeting.email_generated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(meeting)
    
    return {"email": email_content}


@router.get("/{meeting_id}/posts")
async def get_posts(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get generated social media posts"""
    from app.models.generated_post import GeneratedPost
    
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == meeting_id,
                Meeting.user_id == current_user.id
            )
        )
    )
    
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get generated posts for this meeting
    posts_result = await db.execute(
        select(GeneratedPost).where(GeneratedPost.meeting_id == meeting_id)
    )
    posts = posts_result.scalars().all()
    
    return {
        "posts": [
            {
                "id": post.id,
                "platform": post.platform,
                "content": post.content,
                "status": post.status.value,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "posted_at": post.posted_at.isoformat() if post.posted_at else None,
            }
            for post in posts
        ]
    }


@router.post("/{meeting_id}/generate-post")
async def generate_post(
    meeting_id: int,
    platform: str = Query(..., description="Platform: linkedin or facebook"),
    automation_id: Optional[int] = Query(None, description="Optional automation ID to use custom prompt"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a new social media post"""
    from app.services.ai.service import ai_service
    from app.models.generated_post import GeneratedPost, PostStatus
    from app.models.automation import Automation
    
    # Validate platform
    if platform.lower() not in ["linkedin", "facebook"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform must be 'linkedin' or 'facebook'"
        )
    
    # Get meeting
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == meeting_id,
                Meeting.user_id == current_user.id
            )
        )
    )
    
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if not meeting.transcript_available or not meeting.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript not available. Cannot generate post without transcript."
        )
    
    # Get automation if specified, otherwise use active automation for platform
    custom_prompt = None
    automation = None
    if automation_id:
        automation_result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id,
                    Automation.platform == platform.lower()
                )
            )
        )
        automation = automation_result.scalar_one_or_none()
    else:
        # Find active automation for this platform
        automation_result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.user_id == current_user.id,
                    Automation.platform == platform.lower(),
                    Automation.is_active == True
                )
            )
        )
        automation = automation_result.scalar_one_or_none()
    
    if automation:
        custom_prompt = automation.prompt_template
    
    # Generate post
    post_content = await ai_service.generate_social_media_post(
        transcript=meeting.transcript,
        meeting_title=meeting.title,
        platform=platform.lower(),
        custom_prompt=custom_prompt
    )
    
    # Save generated post
    generated_post = GeneratedPost(
        meeting_id=meeting_id,
        automation_id=automation.id if automation else None,
        platform=platform.lower(),
        content=post_content,
        status=PostStatus.DRAFT
    )
    db.add(generated_post)
    await db.commit()
    await db.refresh(generated_post)
    
    return {
        "id": generated_post.id,
        "platform": generated_post.platform,
        "content": generated_post.content,
        "status": generated_post.status.value,
        "message": "Post generated successfully"
    }

