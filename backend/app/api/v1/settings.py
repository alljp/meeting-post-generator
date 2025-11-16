from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.settings import UserSettings

router = APIRouter()


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    bot_join_minutes_before: int


class SettingsUpdate(BaseModel):
    bot_join_minutes_before: Optional[int] = None


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user settings"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    # Create default settings if they don't exist
    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            bot_join_minutes_before=5
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user settings"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    # Create settings if they don't exist
    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            bot_join_minutes_before=settings_update.bot_join_minutes_before or 5
        )
        db.add(settings)
    else:
        # Update existing settings
        if settings_update.bot_join_minutes_before is not None:
            if settings_update.bot_join_minutes_before < 0 or settings_update.bot_join_minutes_before > 60:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="bot_join_minutes_before must be between 0 and 60"
                )
            settings.bot_join_minutes_before = settings_update.bot_join_minutes_before
    
    await db.commit()
    await db.refresh(settings)
    
    return settings


class AutomationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    platform: str
    prompt_template: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class AutomationCreate(BaseModel):
    name: str
    platform: str  # "linkedin" or "facebook"
    prompt_template: str
    is_active: bool = True


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    prompt_template: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/automations", response_model=List[AutomationResponse])
async def list_automations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List automations for the current user"""
    from app.models.automation import Automation
    
    result = await db.execute(
        select(Automation).where(Automation.user_id == current_user.id)
    )
    automations = result.scalars().all()
    return automations


@router.post("/automations", response_model=AutomationResponse, status_code=status.HTTP_201_CREATED)
async def create_automation(
    automation_data: AutomationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new automation"""
    from app.models.automation import Automation, AutomationPlatform
    
    # Validate platform
    if automation_data.platform.lower() not in ["linkedin", "facebook"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform must be 'linkedin' or 'facebook'"
        )
    
    # Check if user already has an automation for this platform
    existing = await db.execute(
        select(Automation).where(
            and_(
                Automation.user_id == current_user.id,
                Automation.platform == automation_data.platform.lower()
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have an automation for {automation_data.platform}. Please update the existing one or delete it first."
        )
    
    automation = Automation(
        user_id=current_user.id,
        name=automation_data.name,
        platform=AutomationPlatform(automation_data.platform.lower()),
        prompt_template=automation_data.prompt_template,
        is_active=automation_data.is_active
    )
    db.add(automation)
    await db.commit()
    await db.refresh(automation)
    
    return automation


@router.patch("/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: int,
    automation_data: AutomationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an automation"""
    from app.models.automation import Automation
    
    result = await db.execute(
        select(Automation).where(
            and_(
                Automation.id == automation_id,
                Automation.user_id == current_user.id
            )
        )
    )
    automation = result.scalar_one_or_none()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Update fields
    if automation_data.name is not None:
        automation.name = automation_data.name
    if automation_data.prompt_template is not None:
        automation.prompt_template = automation_data.prompt_template
    if automation_data.is_active is not None:
        automation.is_active = automation_data.is_active
    
    await db.commit()
    await db.refresh(automation)
    
    return automation


@router.delete("/automations/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an automation"""
    from app.models.automation import Automation
    
    result = await db.execute(
        select(Automation).where(
            and_(
                Automation.id == automation_id,
                Automation.user_id == current_user.id
            )
        )
    )
    automation = result.scalar_one_or_none()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    await db.delete(automation)
    await db.commit()
    
    return None

