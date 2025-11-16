from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    POSTED = "posted"
    FAILED = "failed"


class GeneratedPost(Base):
    __tablename__ = "generated_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    automation_id = Column(Integer, ForeignKey("automations.id"), nullable=True)
    platform = Column(String, nullable=False)  # "linkedin", "facebook"
    content = Column(Text, nullable=False)
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    post_id = Column(String, nullable=True)  # Platform-specific post ID
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    meeting = relationship("Meeting", back_populates="generated_posts")
    automation = relationship("Automation")

