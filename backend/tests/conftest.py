"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient
from app.main import app
from app.core.database import get_db, Base
from app.models.user import User, GoogleAccount
from app.models.calendar_event import CalendarEvent
from app.models.meeting import Meeting, Attendee
from app.models.generated_post import GeneratedPost
from datetime import datetime, timezone, timedelta

# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with database override.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user() -> User:
    """Create a mock user object."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.name = "Test User"
    user.picture = "https://example.com/picture.jpg"
    user.is_active = True
    return user


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/picture.jpg",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_google_account(db_session: AsyncSession, test_user: User) -> GoogleAccount:
    """Create a test Google account."""
    account = GoogleAccount(
        user_id=test_user.id,
        google_email="test@gmail.com",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        is_active=True
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


@pytest.fixture
async def test_calendar_event(db_session: AsyncSession, test_user: User, test_google_account: GoogleAccount) -> CalendarEvent:
    """Create a test calendar event."""
    event = CalendarEvent(
        user_id=test_user.id,
        google_account_id=test_google_account.id,
        google_event_id="test_event_123",
        title="Test Meeting",
        description="Test meeting description",
        start_time=datetime.now(timezone.utc) + timedelta(hours=1),
        end_time=datetime.now(timezone.utc) + timedelta(hours=2),
        location="Test Location",
        meeting_link="https://zoom.us/j/123456789",
        meeting_platform="zoom",
        notetaker_enabled=False
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    return event


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": "This is a generated email content."
            }
        }]
    }


@pytest.fixture
def mock_recall_api_response():
    """Mock Recall.ai API response."""
    return {
        "id": "bot_123",
        "status": "active",
        "state": "joined",
        "transcript_available": True,
        "recording_available": False,
        "meeting_url": "https://zoom.us/j/123456789",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for external API calls."""
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client
