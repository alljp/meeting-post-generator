from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        # Composite unique constraint: google_event_id should be unique per google_account_id
        # This allows the same event ID to exist in different Google accounts
        UniqueConstraint('google_account_id', 'google_event_id', name='uq_calendar_event_account_event'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    google_account_id = Column(Integer, ForeignKey("google_accounts.id"), nullable=False, index=True)
    google_event_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    meeting_link = Column(String, nullable=True)  # Zoom/Teams/Meet link
    meeting_platform = Column(String, nullable=True)  # "zoom", "teams", "meet"
    notetaker_enabled = Column(Boolean, default=False)
    recall_bot_id = Column(String, nullable=True)  # Recall.ai bot ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")
    google_account = relationship("GoogleAccount")

