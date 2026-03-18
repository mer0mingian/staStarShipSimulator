"""
Tests for theme preference API endpoints.

Verifies CRUD operations for user theme preferences including:
- GET /api/users/me/theme - Retrieve current theme
- PUT /api/users/me/theme - Set theme to 'light' or 'dark'
- DELETE /api/users/me/theme - Clear theme preference
- Validation that only 'light' or 'dark' are accepted
"""

import pytest
from sqlalchemy import select
from sta.database.schema import CampaignPlayerRecord


@pytest.mark.api
class TestThemePreferenceCRUD:
    """Test CRUD operations for theme preference."""

    @pytest.mark.asyncio
    async def test_get_theme_preference_no_auth(self, client, sample_campaign):
        """Test that GET theme without auth returns 401."""
        client.cookies.clear()
        response = client.get("/api/users/me/theme")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_theme_preference_default_null(self, client, sample_campaign):
        """Test that new players have no theme preference set."""
        player = sample_campaign["players"][1]  # non-GM player

        client.cookies.set("sta_session_token", player.session_token)
        response = client.get("/api/users/me/theme")

        assert response.status_code == 200
        data = response.json()
        assert data["theme_preference"] is None

    @pytest.mark.asyncio
    async def test_set_theme_preference_to_dark(
        self, client, sample_campaign, test_session
    ):
        """Test setting theme preference to 'dark'."""
        player = sample_campaign["players"][1]  # non-GM player
        client.cookies.set("sta_session_token", player.session_token)

        response = client.put("/api/users/me/theme", json={"theme_preference": "dark"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["theme_preference"] == "dark"

        result = await test_session.execute(
            select(CampaignPlayerRecord).filter(CampaignPlayerRecord.id == player.id)
        )
        updated_player = result.scalars().first()
        assert updated_player.theme_preference == "dark"

    @pytest.mark.asyncio
    async def test_set_theme_preference_to_light(
        self, client, sample_campaign, test_session
    ):
        """Test setting theme preference to 'light'."""
        player = sample_campaign["players"][1]  # non-GM player
        client.cookies.set("sta_session_token", player.session_token)

        response = client.put("/api/users/me/theme", json={"theme_preference": "light"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["theme_preference"] == "light"

        result = await test_session.execute(
            select(CampaignPlayerRecord).filter(CampaignPlayerRecord.id == player.id)
        )
        updated_player = result.scalars().first()
        assert updated_player.theme_preference == "light"

    @pytest.mark.asyncio
    async def test_update_theme_preference(self, client, sample_campaign, test_session):
        """Test updating theme preference from 'dark' to 'light'."""
        player = sample_campaign["players"][1]
        client.cookies.set("sta_session_token", player.session_token)

        client.put("/api/users/me/theme", json={"theme_preference": "dark"})
        response = client.put("/api/users/me/theme", json={"theme_preference": "light"})

        assert response.status_code == 200
        data = response.json()
        assert data["theme_preference"] == "light"

        result = await test_session.execute(
            select(CampaignPlayerRecord).filter(CampaignPlayerRecord.id == player.id)
        )
        updated_player = result.scalars().first()
        assert updated_player.theme_preference == "light"

    @pytest.mark.asyncio
    async def test_delete_theme_preference(self, client, sample_campaign, test_session):
        """Test clearing theme preference."""
        player = sample_campaign["players"][1]
        client.cookies.set("sta_session_token", player.session_token)

        client.put("/api/users/me/theme", json={"theme_preference": "dark"})
        response = client.delete("/api/users/me/theme")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["theme_preference"] is None

        result = await test_session.execute(
            select(CampaignPlayerRecord).filter(CampaignPlayerRecord.id == player.id)
        )
        updated_player = result.scalars().first()
        assert updated_player.theme_preference is None

    @pytest.mark.asyncio
    async def test_delete_theme_when_not_set(
        self, client, sample_campaign, test_session
    ):
        """Test clearing theme preference when it's already null."""
        player = sample_campaign["players"][1]
        client.cookies.set("sta_session_token", player.session_token)

        response = client.delete("/api/users/me/theme")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["theme_preference"] is None


@pytest.mark.api
class TestThemePreferenceValidation:
    """Test validation for theme preference values."""

    @pytest.mark.asyncio
    async def test_set_invalid_theme_rejected(self, client, sample_campaign):
        """Test that invalid theme values are rejected."""
        player = sample_campaign["players"][1]
        client.cookies.set("sta_session_token", player.session_token)

        invalid_themes = ["blue", "dark-mode", "LIGHT", "Dark", "", "system"]

        for invalid_theme in invalid_themes:
            response = client.put(
                "/api/users/me/theme",
                json={"theme_preference": invalid_theme},
            )
            assert response.status_code == 400, (
                f"Expected 400 for theme: {invalid_theme}"
            )
            assert "Invalid theme_preference" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_set_theme_missing_value(self, client, sample_campaign):
        """Test that missing theme_preference returns 400."""
        player = sample_campaign["players"][1]
        client.cookies.set("sta_session_token", player.session_token)

        response = client.put("/api/users/me/theme", json={})
        assert response.status_code == 400
        assert "theme_preference is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_set_theme_null_value(self, client, sample_campaign):
        """Test that null theme_preference returns 400."""
        player = sample_campaign["players"][1]
        client.cookies.set("sta_session_token", player.session_token)

        response = client.put("/api/users/me/theme", json={"theme_preference": None})
        assert response.status_code == 400
        assert "theme_preference is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_set_theme_with_extra_fields(self, client, sample_campaign):
        """Test that extra fields in request are ignored."""
        player = sample_campaign["players"][1]
        client.cookies.set("sta_session_token", player.session_token)

        response = client.put(
            "/api/users/me/theme",
            json={"theme_preference": "dark", "extra_field": "ignored"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["theme_preference"] == "dark"


@pytest.mark.api
class TestThemePreferenceWithGM:
    """Test theme preference works for GM users too."""

    @pytest.mark.asyncio
    async def test_gm_can_set_theme(self, client, sample_campaign, test_session):
        """Test that GM can set theme preference."""
        gm = sample_campaign["players"][0]  # first player is GM
        client.cookies.set("sta_session_token", gm.session_token)

        response = client.put("/api/users/me/theme", json={"theme_preference": "dark"})

        assert response.status_code == 200
        data = response.json()
        assert data["theme_preference"] == "dark"

        result = await test_session.execute(
            select(CampaignPlayerRecord).filter(CampaignPlayerRecord.id == gm.id)
        )
        gm_player = result.scalars().first()
        assert gm_player.theme_preference == "dark"

    @pytest.mark.asyncio
    async def test_gm_can_get_own_theme(self, client, sample_campaign):
        """Test that GM can get their own theme preference."""
        gm = sample_campaign["players"][0]
        client.cookies.set("sta_session_token", gm.session_token)

        client.put("/api/users/me/theme", json={"theme_preference": "light"})
        response = client.get("/api/users/me/theme")

        assert response.status_code == 200
        data = response.json()
        assert data["theme_preference"] == "light"
