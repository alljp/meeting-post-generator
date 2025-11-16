# Backend Testing Guide

## Testing Framework: pytest

The backend uses **pytest** as the primary testing framework, with **pytest-asyncio** for testing asynchronous code.

### Why pytest?

- **Simple syntax**: Easy to write and read tests
- **Powerful fixtures**: Reusable test data and setup
- **Async support**: Built-in support for async/await with pytest-asyncio
- **Rich plugin ecosystem**: Extensible with many plugins
- **Detailed output**: Clear test results and failure messages

### Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py          # Shared fixtures and configuration
├── test_ai_service.py    # AI service unit tests
├── test_recall_service.py # Recall service unit tests
├── test_calendar_service.py # Calendar service unit tests
└── test_api_calendar.py # API endpoint tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_ai_service.py

# Run specific test
pytest tests/test_ai_service.py::TestAIService::test_generate_follow_up_email_success

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Database

Tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) to avoid affecting the development database. Each test gets a fresh database session.

### Fixtures

Common fixtures available in `conftest.py`:

- `db_session`: Fresh database session for each test
- `client`: FastAPI test client with database override
- `test_user`: Creates a test user in the database
- `test_google_account`: Creates a test Google account
- `test_calendar_event`: Creates a test calendar event
- `mock_openai_response`: Mock OpenAI API response
- `mock_recall_api_response`: Mock Recall.ai API response

### Writing Tests

#### Basic Test Example

```python
import pytest
from app.services.ai_service import AIService

class TestAIService:
    @pytest.fixture
    def ai_service(self):
        return AIService()
    
    @pytest.mark.asyncio
    async def test_something(self, ai_service):
        result = await ai_service.some_method()
        assert result == expected_value
```

#### Testing Async Code

Use `@pytest.mark.asyncio` decorator for async tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

#### Mocking External APIs

Use `unittest.mock` to mock external API calls:

```python
from unittest.mock import AsyncMock, patch

@patch("httpx.AsyncClient")
async def test_api_call(mock_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "test"}
    mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
    
    result = await service.call_api()
    assert result == expected
```

### Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies (APIs, databases)
3. **Fixtures**: Use fixtures for common setup
4. **Naming**: Use descriptive test names
5. **Assertions**: Use clear, specific assertions
6. **Coverage**: Aim for high code coverage (>80%)

### Test Categories

- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test interactions between components
- **API Tests**: Test HTTP endpoints with FastAPI test client

