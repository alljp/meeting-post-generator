from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association table for many-to-many relationship
meeting_attendees = Table(
    "meeting_attendees",
    Base.metadata,
    Column("meeting_id", Integer, ForeignKey("meetings.id"), primary_key=True),
    Column("attendee_id", Integer, ForeignKey("attendees.id"), primary_key=True),
)


class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    calendar_event_id = Column(Integer, ForeignKey("calendar_events.id"), nullable=True)
    recall_bot_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    platform = Column(String, nullable=False)  # "zoom", "teams", "meet"
    transcript = Column(Text, nullable=True)
    transcript_available = Column(Boolean, default=False)
    recording_url = Column(String, nullable=True)
    email = Column(Text, nullable=True)  # AI-generated follow-up email
    email_generated_at = Column(DateTime(timezone=True), nullable=True)  # When email was generated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="meetings")
    attendees = relationship("Attendee", secondary=meeting_attendees, back_populates="meetings")
    generated_posts = relationship("GeneratedPost", back_populates="meeting", cascade="all, delete-orphan")


class Attendee(Base):
    __tablename__ = "attendees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    meetings = relationship("Meeting", secondary=meeting_attendees, back_populates="attendees")

