from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SocialPlatform(str, enum.Enum):
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(Enum(SocialPlatform), nullable=False)
    account_id = Column(String, nullable=False)  # Platform-specific user ID
    account_name = Column(String, nullable=True)
    access_token = Column(String, nullable=False)  # Encrypted in production
    refresh_token = Column(String, nullable=True)  # Encrypted in production
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="social_accounts")

