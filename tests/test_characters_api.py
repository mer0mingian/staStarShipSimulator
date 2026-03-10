"""
Tests for Character Management API endpoints.

Tests verify:
- Character CRUD operations
- Validation (attributes 7-12, disciplines 0-5, stress 0-max)
- Stress/determination adjustments
- Character state management
- Talent management
"""

import json
import pytest
from sta.database.schema import CampaignRecord, CampaignPlayerRecord
from sta.database.vtt_schema import VTTCharacterRecord


class TestCharacterCRUD:
    """Tests for Character CRUD endpoints."""

    def test_create_character(self, client, test_session):
        """Test creating a new character with validation."""
        response = client.post(
            "/api/characters",
            json={
                "name": "Test Character",
                "attributes": {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                },
                "disciplines": {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                },
                "stress": 3,
                "stress_max": 5,
                "determination": 1,
                "determination_max": 3,
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "Test Character"
        assert data["stress"] == 3
        assert data["determination"] == 1

    def test_create_character_invalid_attribute(self, client, test_session):
        """Test creating character with invalid attribute (outside 7-12)."""
        response = client.post(
            "/api/characters",
            json={
                "name": "Invalid Character",
                "attributes": {
                    "control": 15,  # Invalid - too high
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                },
                "disciplines": {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                },
            },
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "must be between 7-12" in json.loads(response.data)["error"]

    def test_create_character_invalid_discipline(self, client, test_session):
        """Test creating character with invalid discipline (outside 0-5)."""
        response = client.post(
            "/api/characters",
            json={
                "name": "Invalid Character",
                "attributes": {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                },
                "disciplines": {
                    "command": 6,  # Invalid - too high
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                },
            },
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "must be between 0-5" in json.loads(response.data)["error"]

    def test_create_character_invalid_stress(self, client, test_session):
        """Test creating character with invalid stress (above max)."""
        response = client.post(
            "/api/characters",
            json={
                "name": "Invalid Character",
                "attributes": {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                },
                "disciplines": {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                },
                "stress": 10,  # Invalid - above max
                "stress_max": 5,
            },
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "Stress must be between" in json.loads(response.data)["error"]

    def test_list_characters(self, client, test_session):
        """Test listing all characters."""
        # Create test characters
        char1 = VTTCharacterRecord(
            name="Character 1",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        char2 = VTTCharacterRecord(
            name="Character 2",
            attributes_json=json.dumps(
                {
                    "control": 8,
                    "fitness": 9,
                    "daring": 10,
                    "insight": 8,
                    "presence": 10,
                    "reason": 8,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(char1)
        test_session.add(char2)
        test_session.commit()

        response = client.get("/api/characters")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2

    def test_list_characters_filter_by_campaign(self, client, test_session):
        """Test filtering characters by campaign_id."""
        # Create campaign
        campaign = CampaignRecord(
            campaign_id="test-campaign", name="Test Campaign", is_active=True
        )
        test_session.add(campaign)
        test_session.flush()

        # Create characters with and without campaign
        char1 = VTTCharacterRecord(
            name="Campaign Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            campaign_id=campaign.id,
        )
        char2 = VTTCharacterRecord(
            name="Orphan Character",
            attributes_json=json.dumps(
                {
                    "control": 8,
                    "fitness": 9,
                    "daring": 10,
                    "insight": 8,
                    "presence": 10,
                    "reason": 8,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(char1)
        test_session.add(char2)
        test_session.commit()

        response = client.get(f"/api/characters?campaign_id={campaign.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["name"] == "Campaign Character"

    def test_get_character(self, client, test_session):
        """Test getting a single character."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            stress=3,
            stress_max=5,
        )
        test_session.add(char)
        test_session.commit()

        response = client.get(f"/api/characters/{char.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test Character"
        assert data["stress"] == 3

    def test_get_character_not_found(self, client, test_session):
        """Test getting non-existent character returns 404."""
        response = client.get("/api/characters/99999")
        assert response.status_code == 404

    def test_update_character(self, client, test_session):
        """Test updating a character."""
        char = VTTCharacterRecord(
            name="Original Name",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}",
            json={"name": "Updated Name", "stress": 4},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Name"
        assert data["stress"] == 4

    def test_delete_character(self, client, test_session):
        """Test deleting a character (GM only)."""
        # Create campaign with GM
        campaign = CampaignRecord(
            campaign_id="test-campaign", name="Test Campaign", is_active=True
        )
        test_session.add(campaign)
        test_session.flush()

        gm = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="GM",
            session_token="gm-token-123",
            is_gm=True,
        )
        test_session.add(gm)

        # Create character in campaign
        char = VTTCharacterRecord(
            name="To Delete",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            campaign_id=campaign.id,
        )
        test_session.add(char)
        test_session.commit()

        # Set GM cookie
        client.set_cookie("sta_session_token", "gm-token-123")

        response = client.delete(f"/api/characters/{char.id}")
        assert response.status_code == 200

        # Verify character is deleted
        response = client.get(f"/api/characters/{char.id}")
        assert response.status_code == 404


class TestCharacterModel:
    """Tests for character model conversion."""

    def test_get_character_model(self, client, test_session):
        """Test returning character as legacy Character model."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            talents_json=json.dumps(["Bold (Command)", "Tough"]),
            focuses_json=json.dumps(["Diplomacy", "First Aid"]),
            stress=3,
            stress_max=5,
            determination=1,
            determination_max=3,
            rank="Lieutenant",
            species="Human",
            role="Command",
        )
        test_session.add(char)
        test_session.commit()

        response = client.get(f"/api/characters/{char.id}/model")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test Character"
        assert data["attributes"]["control"] == 9
        assert data["disciplines"]["command"] == 2
        assert data["talents"] == ["Bold (Command)", "Tough"]
        assert data["focuses"] == ["Diplomacy", "First Aid"]
        assert data["rank"] == "Lieutenant"
        assert data["species"] == "Human"


class TestStressDetermination:
    """Tests for stress and determination adjustment endpoints."""

    def test_adjust_stress_increase(self, client, test_session):
        """Test increasing stress."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            stress=3,
            stress_max=5,
        )
        test_session.add(char)
        test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/stress",
            json={"adjustment": 2},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["stress"] == 5  # Capped at max

    def test_adjust_stress_decrease(self, client, test_session):
        """Test decreasing stress."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            stress=3,
            stress_max=5,
        )
        test_session.add(char)
        test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/stress",
            json={"adjustment": -2},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["stress"] == 1

    def test_adjust_stress_min_zero(self, client, test_session):
        """Test stress cannot go below zero."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            stress=1,
            stress_max=5,
        )
        test_session.add(char)
        test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/stress",
            json={"adjustment": -5},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["stress"] == 0

    def test_adjust_determination(self, client, test_session):
        """Test adjusting determination."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            determination=1,
            determination_max=3,
        )
        test_session.add(char)
        test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/determination",
            json={"adjustment": 1},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["determination"] == 2


class TestCharacterState:
    """Tests for character state management."""

    def test_update_character_state(self, client, test_session):
        """Test updating character state."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            state="Ok",
        )
        test_session.add(char)
        test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/state",
            json={"state": "Injured"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["state"] == "Injured"

    def test_update_character_state_invalid(self, client, test_session):
        """Test updating character state with invalid value."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/state",
            json={"state": "InvalidState"},
            content_type="application/json",
        )
        assert response.status_code == 400


class TestCharacterTalents:
    """Tests for character talent management."""

    def test_list_talents(self, client, test_session):
        """Test listing available talents."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            talents_json=json.dumps(["Bold (Command)"]),
        )
        test_session.add(char)
        test_session.commit()

        response = client.get(f"/api/characters/{char.id}/talents")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "Bold (Command)" in data["character_talents"]
        assert "Bold (Conn)" in data["available_talents"]

    def test_add_talent(self, client, test_session):
        """Test adding a talent to character."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            talents_json=json.dumps([]),
        )
        test_session.add(char)
        test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/talents",
            json={"talent_name": "Tough"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "Tough" in data["talents"]

    def test_add_talent_already_has(self, client, test_session):
        """Test adding a talent character already has."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            talents_json=json.dumps(["Tough"]),
        )
        test_session.add(char)
        test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/talents",
            json={"talent_name": "Tough"},
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "already has this talent" in json.loads(response.data)["error"]

    def test_add_talent_invalid(self, client, test_session):
        """Test adding an invalid talent."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            talents_json=json.dumps([]),
        )
        test_session.add(char)
        test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/talents",
            json={"talent_name": "InvalidTalent"},
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "Unknown talent" in json.loads(response.data)["error"]
