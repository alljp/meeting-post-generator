"""
Unit tests for Settings API endpoints.
Tests user settings and automation management.
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app.models.settings import UserSettings
from app.models.automation import Automation, AutomationPlatform
from app.utils.jwt import create_access_token


class TestSettingsAPI:
    """Test suite for Settings API endpoints."""
    
    @pytest.fixture
    def auth_token(self, test_user):
        """Create auth token for test user."""
        return create_access_token({"sub": str(test_user.id)})
    
    @pytest.mark.asyncio
    async def test_get_settings_creates_default(self, client: AsyncClient, test_user, auth_token, db_session):
        """Test getting settings creates default if not exists."""
        response = await client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_join_minutes_before"] == 5  # Default value
        
        # Verify settings were created in database
        from sqlalchemy import select
        result = await db_session.execute(
            select(UserSettings).where(UserSettings.user_id == test_user.id)
        )
        settings = result.scalar_one()
        assert settings.bot_join_minutes_before == 5
    
    @pytest.mark.asyncio
    async def test_get_settings_existing(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test getting existing settings."""
        settings = UserSettings(
            user_id=test_user.id,
            bot_join_minutes_before=10
        )
        db_session.add(settings)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_join_minutes_before"] == 10
    
    @pytest.mark.asyncio
    async def test_update_settings_success(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test updating settings."""
        settings = UserSettings(
            user_id=test_user.id,
            bot_join_minutes_before=5
        )
        db_session.add(settings)
        await db_session.commit()
        
        response = await client.patch(
            "/api/v1/settings",
            json={"bot_join_minutes_before": 10},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_join_minutes_before"] == 10
        
        await db_session.refresh(settings)
        assert settings.bot_join_minutes_before == 10
    
    @pytest.mark.asyncio
    async def test_update_settings_creates_if_not_exists(self, client: AsyncClient, test_user, auth_token, db_session):
        """Test updating settings creates them if not exist."""
        response = await client.patch(
            "/api/v1/settings",
            json={"bot_join_minutes_before": 15},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bot_join_minutes_before"] == 15
    
    @pytest.mark.asyncio
    async def test_update_settings_invalid_value_too_low(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test updating settings with invalid value (too low)."""
        # Create settings first
        settings = UserSettings(
            user_id=test_user.id,
            bot_join_minutes_before=5
        )
        db_session.add(settings)
        await db_session.commit()
        
        response = await client.patch(
            "/api/v1/settings",
            json={"bot_join_minutes_before": -1},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "must be between 0 and 60" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_settings_invalid_value_too_high(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test updating settings with invalid value (too high)."""
        # Create settings first
        settings = UserSettings(
            user_id=test_user.id,
            bot_join_minutes_before=5
        )
        db_session.add(settings)
        await db_session.commit()
        
        response = await client.patch(
            "/api/v1/settings",
            json={"bot_join_minutes_before": 61},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "must be between 0 and 60" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_list_automations_empty(self, client: AsyncClient, test_user, auth_token):
        """Test listing automations when none exist."""
        response = await client.get(
            "/api/v1/settings/automations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_list_automations_success(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test listing automations."""
        automation = Automation(
            user_id=test_user.id,
            name="Test Automation",
            platform=AutomationPlatform.LINKEDIN,
            prompt_template="Test template: {transcript}",
            is_active=True
        )
        db_session.add(automation)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/settings/automations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Automation"
        assert data[0]["platform"] == "linkedin"
    
    @pytest.mark.asyncio
    async def test_create_automation_success(self, client: AsyncClient, test_user, auth_token, db_session):
        """Test creating automation."""
        response = await client.post(
            "/api/v1/settings/automations",
            json={
                "name": "New Automation",
                "platform": "linkedin",
                "prompt_template": "Create post: {transcript}",
                "is_active": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Automation"
        assert data["platform"] == "linkedin"
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_create_automation_invalid_platform(self, client: AsyncClient, test_user, auth_token):
        """Test creating automation with invalid platform."""
        response = await client.post(
            "/api/v1/settings/automations",
            json={
                "name": "Test",
                "platform": "twitter",  # Invalid
                "prompt_template": "Test"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "platform must be" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_create_automation_duplicate(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test creating duplicate automation."""
        automation = Automation(
            user_id=test_user.id,
            name="Existing Automation",
            platform=AutomationPlatform.LINKEDIN,
            prompt_template="Existing template",
            is_active=True
        )
        db_session.add(automation)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/settings/automations",
            json={
                "name": "New Automation",
                "platform": "linkedin",  # Duplicate platform
                "prompt_template": "New template"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        assert "already have an automation" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_automation_success(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test updating automation."""
        automation = Automation(
            user_id=test_user.id,
            name="Original Name",
            platform=AutomationPlatform.LINKEDIN,
            prompt_template="Original template",
            is_active=True
        )
        db_session.add(automation)
        await db_session.commit()
        
        response = await client.patch(
            f"/api/v1/settings/automations/{automation.id}",
            json={
                "name": "Updated Name",
                "prompt_template": "Updated template",
                "is_active": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["prompt_template"] == "Updated template"
        assert data["is_active"] is False
        
        await db_session.refresh(automation)
        assert automation.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_automation_partial(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test partial update of automation."""
        automation = Automation(
            user_id=test_user.id,
            name="Original Name",
            platform=AutomationPlatform.LINKEDIN,
            prompt_template="Original template",
            is_active=True
        )
        db_session.add(automation)
        await db_session.commit()
        
        response = await client.patch(
            f"/api/v1/settings/automations/{automation.id}",
            json={"name": "Updated Name"},  # Only update name
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["prompt_template"] == "Original template"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_automation_not_found(self, client: AsyncClient, test_user, auth_token):
        """Test updating non-existent automation."""
        response = await client.patch(
            "/api/v1/settings/automations/99999",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_automation_success(self, client: AsyncClient, db_session, test_user, auth_token):
        """Test deleting automation."""
        automation = Automation(
            user_id=test_user.id,
            name="To Delete",
            platform=AutomationPlatform.LINKEDIN,
            prompt_template="Template",
            is_active=True
        )
        db_session.add(automation)
        await db_session.commit()
        automation_id = automation.id
        
        response = await client.delete(
            f"/api/v1/settings/automations/{automation_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(Automation).where(Automation.id == automation_id)
        )
        assert result.scalar_one_or_none() is None
    
    @pytest.mark.asyncio
    async def test_delete_automation_not_found(self, client: AsyncClient, test_user, auth_token):
        """Test deleting non-existent automation."""
        response = await client.delete(
            "/api/v1/settings/automations/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_settings_unauthorized(self, client: AsyncClient):
        """Test getting settings without authentication."""
        response = await client.get("/api/v1/settings")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_settings_unauthorized(self, client: AsyncClient):
        """Test updating settings without authentication."""
        response = await client.patch("/api/v1/settings", json={"bot_join_minutes_before": 10})
        assert response.status_code == 401

