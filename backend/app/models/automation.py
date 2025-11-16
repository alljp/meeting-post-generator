from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class AutomationPlatform(str, enum.Enum):
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class Automation(Base):
    __tablename__ = "automations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    platform = Column(Enum(AutomationPlatform), nullable=False)
    prompt_template = Column(Text, nullable=False)  # AI prompt for generating posts
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="automations")

