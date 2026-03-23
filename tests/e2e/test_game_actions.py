"""E2E tests for STA VTT game actions.

Tests game mechanics including dice rolls, values, and resources.
"""

import json
import pytest
from fastapi.testclient import TestClient


class TestDiceMechanics:
    """Test dice rolling and mechanics."""

    def test_roll_api_returns_valid_structure(self, client: TestClient):
        """Verify roll API returns expected structure."""
        roll_data = {
            "attribute": 8,
            "discipline": 3,
            "difficulty": 1,
            "focus": False,
            "bonus_dice": 0,
        }

        response = client.post("/api/roll", json=roll_data)
        assert response.status_code == 200
        result = response.json()

        required_fields = [
            "rolls",
            "target_number",
            "successes",
            "complications",
            "difficulty",
            "succeeded",
            "momentum_generated",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_target_number_calculation(self, client: TestClient):
        """Verify target number = Attribute + Discipline."""
        test_cases = [
            {"attribute": 7, "discipline": 1, "expected_tn": 8},
            {"attribute": 10, "discipline": 5, "expected_tn": 15},
            {"attribute": 12, "discipline": 5, "expected_tn": 17},
        ]

        for tc in test_cases:
            roll_data = {
                "attribute": tc["attribute"],
                "discipline": tc["discipline"],
                "difficulty": 1,
                "focus": False,
                "bonus_dice": 0,
            }
            response = client.post("/api/roll", json=roll_data)
            result = response.json()
            assert result["target_number"] == tc["expected_tn"]

    def test_successes_calculation(self, client: TestClient):
        """Test successes are calculated correctly (roll <= target = 1 success, roll = 1 = 2 successes)."""
        roll_data = {
            "attribute": 8,
            "discipline": 3,
            "difficulty": 2,
            "focus": False,
            "bonus_dice": 0,
        }

        response = client.post("/api/roll", json=roll_data)
        result = response.json()
        rolls = result["rolls"]
        target = result["target_number"]

        expected_successes = 0
        for roll in rolls:
            if roll == 1:
                expected_successes += 2
            elif roll <= target:
                expected_successes += 1

        assert result["successes"] == expected_successes

    def test_momentum_generated_calculation(self, client: TestClient):
        """Test momentum = max(0, successes - difficulty)."""
        roll_data = {
            "attribute": 10,
            "discipline": 5,
            "difficulty": 3,
            "focus": False,
            "bonus_dice": 0,
        }

        response = client.post("/api/roll", json=roll_data)
        result = response.json()

        successes = result["successes"]
        difficulty = result["difficulty"]
        expected_momentum = max(0, successes - difficulty)

        assert result["momentum_generated"] == expected_momentum

    def test_assisted_roll(self, client: TestClient):
        """Test assisted task roll with system and department."""
        roll_data = {
            "attribute": 8,
            "discipline": 3,
            "system": 10,
            "department": 3,
            "difficulty": 1,
            "focus": False,
            "bonus_dice": 0,
        }

        response = client.post("/api/roll-assisted", json=roll_data)
        assert response.status_code == 200
        result = response.json()

        assert "rolls" in result
        assert "target_number" in result


class TestValueMechanics:
    """Test Value interaction mechanics."""

    @pytest.fixture
    def character_for_values(self, client: TestClient):
        """Create character with values for testing."""
        data = {
            "step": "final",
            "character": {
                "name": "Value Mechanics Test",
                "species": "Human",
                "attributes": {
                    "control": 8,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 9,
                    "presence": 9,
                    "reason": 9,
                },
                "disciplines": {
                    "command": 3,
                    "conn": 2,
                    "engineering": 3,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                },
                "values": [
                    {
                        "name": "Integrity",
                        "description": "I uphold my principles.",
                        "helpful": True,
                    },
                    {
                        "name": "Loyalty",
                        "description": "I remain true to my friends.",
                        "helpful": True,
                    },
                    {
                        "name": "Courage",
                        "description": "I face danger without fear.",
                        "helpful": True,
                    },
                ],
            },
            "campaign_id": None,
        }
        response = client.post("/api/characters/wizard", json=data)
        return response.json()["character"]["id"]

    def test_challenge_value_grants_determination(
        self, client: TestClient, character_for_values
    ):
        """Test Challenge Value → +1 Determination."""
        char_id = character_for_values

        response = client.put(
            f"/api/characters/{char_id}/values/integrity/challenge", json={}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["determination"] == 2

    def test_comply_value_grants_determination(
        self, client: TestClient, character_for_values
    ):
        """Test Comply Value → +1 Determination."""
        char_id = character_for_values

        response = client.put(
            f"/api/characters/{char_id}/values/loyalty/comply", json={}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["determination"] == 2

    def test_use_value_once_per_session(self, client: TestClient, character_for_values):
        """Test Use Value (once per session) - allows spending Determination."""
        char_id = character_for_values

        response = client.put(f"/api/characters/{char_id}/values/courage/use", json={})
        assert response.status_code == 200
        result = response.json()
        assert result["used_this_session"] is True

        response = client.put(f"/api/characters/{char_id}/values/courage/use", json={})
        assert response.status_code == 400
        assert "already been used" in response.json()["detail"].lower()

    def test_determination_max_enforced(self, client: TestClient, character_for_values):
        """Test Determination doesn't exceed max of 3."""
        char_id = character_for_values

        client.put(f"/api/characters/{char_id}/values/integrity/challenge", json={})
        client.put(f"/api/characters/{char_id}/values/loyalty/comply", json={})

        response = client.put(
            f"/api/characters/{char_id}/values/courage/challenge", json={}
        )
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()

    def test_value_session_reset(self, client: TestClient, character_for_values):
        """Test resetting Values for new session."""
        char_id = character_for_values

        client.put(f"/api/characters/{char_id}/values/courage/use", json={})

        response = client.post(
            f"/api/characters/{char_id}/values/reset-session", json={}
        )
        assert response.status_code == 200

        response = client.put(f"/api/characters/{char_id}/values/courage/use", json={})
        assert response.status_code == 200


class TestStressAndDetermination:
    """Test Stress and Determination mechanics."""

    @pytest.fixture
    def character_with_resources(self, client: TestClient):
        """Create character with stress and determination."""
        data = {
            "step": "final",
            "character": {
                "name": "Resource Test Character",
                "species": "Human",
                "attributes": {
                    "control": 8,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 9,
                    "presence": 9,
                    "reason": 9,
                },
                "disciplines": {
                    "command": 3,
                    "conn": 2,
                    "engineering": 3,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                },
                "values": [
                    {"name": "Test", "description": "Test", "helpful": True},
                    {"name": "Test2", "description": "Test", "helpful": True},
                ],
            },
            "campaign_id": None,
        }
        response = client.post("/api/characters/wizard", json=data)
        return response.json()["character"]["id"]

    def test_stress_adjustment(self, client: TestClient, character_with_resources):
        """Test adjusting stress."""
        char_id = character_with_resources

        response = client.put(
            f"/api/characters/{char_id}/stress", json={"adjustment": 2}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["stress"] == 2

        response = client.put(
            f"/api/characters/{char_id}/stress", json={"adjustment": -1}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["stress"] == 1

    def test_stress_max_enforced(self, client: TestClient, character_with_resources):
        """Test stress cannot exceed max."""
        char_id = character_with_resources

        response = client.put(
            f"/api/characters/{char_id}/stress", json={"adjustment": 100}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["stress"] == result["stress_max"]

    def test_determination_adjustment(
        self, client: TestClient, character_with_resources
    ):
        """Test adjusting determination."""
        char_id = character_with_resources

        response = client.put(
            f"/api/characters/{char_id}/determination", json={"adjustment": 1}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["determination"] == 2


class TestCharacterAttributesAndDisciplines:
    """Test attribute and discipline validation."""

    def test_attribute_range_validation(self, client: TestClient):
        """Test attributes must be 7-12."""
        char_data = {
            "name": "Test",
            "species": "Human",
            "attributes": {
                "control": 5,
                "daring": 9,
                "fitness": 8,
                "insight": 11,
                "presence": 12,
                "reason": 10,
            },
            "disciplines": {
                "command": 3,
                "conn": 2,
                "engineering": 3,
                "medicine": 1,
                "science": 4,
                "security": 2,
            },
        }

        response = client.post("/api/characters", json=char_data)
        assert response.status_code == 400
        assert "7-12" in response.json()["detail"]

    def test_discipline_range_validation(self, client: TestClient):
        """Test disciplines must be 0-5."""
        char_data = {
            "name": "Test",
            "species": "Human",
            "attributes": {
                "control": 10,
                "daring": 9,
                "fitness": 8,
                "insight": 11,
                "presence": 12,
                "reason": 10,
            },
            "disciplines": {
                "command": 6,
                "conn": 2,
                "engineering": 3,
                "medicine": 1,
                "science": 4,
                "security": 2,
            },
        }

        response = client.post("/api/characters", json=char_data)
        assert response.status_code == 400
        assert "0-5" in response.json()["detail"]


class TestCharacterCRUD:
    """Test basic character CRUD operations."""

    def test_create_character_direct(self, client: TestClient):
        """Test creating a character directly via API."""
        char_data = {
            "name": "Direct Create Test",
            "species": "Human",
            "rank": "Lieutenant",
            "role": "Science Officer",
            "attributes": {
                "control": 10,
                "daring": 9,
                "fitness": 8,
                "insight": 11,
                "presence": 12,
                "reason": 10,
            },
            "disciplines": {
                "command": 2,
                "conn": 2,
                "engineering": 2,
                "medicine": 2,
                "science": 4,
                "security": 2,
            },
            "stress": 0,
            "stress_max": 8,
            "determination": 1,
            "determination_max": 3,
        }

        response = client.post("/api/characters", json=char_data)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Direct Create Test"
        assert result["species"] == "Human"

    def test_list_characters(self, client: TestClient):
        """Test listing characters."""
        response = client.get("/api/characters")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_character(self, client: TestClient):
        """Test getting a specific character."""
        char_data = {
            "name": "Get Test",
            "species": "Human",
            "attributes": {
                "control": 10,
                "daring": 9,
                "fitness": 8,
                "insight": 11,
                "presence": 12,
                "reason": 10,
            },
            "disciplines": {
                "command": 2,
                "conn": 2,
                "engineering": 2,
                "medicine": 2,
                "science": 4,
                "security": 2,
            },
        }

        create_response = client.post("/api/characters", json=char_data)
        char_id = create_response.json()["id"]

        response = client.get(f"/api/characters/{char_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Get Test"

    def test_update_character(self, client: TestClient):
        """Test updating a character."""
        char_data = {
            "name": "Update Test",
            "species": "Human",
            "attributes": {
                "control": 10,
                "daring": 9,
                "fitness": 8,
                "insight": 11,
                "presence": 12,
                "reason": 10,
            },
            "disciplines": {
                "command": 2,
                "conn": 2,
                "engineering": 2,
                "medicine": 2,
                "science": 4,
                "security": 2,
            },
        }

        create_response = client.post("/api/characters", json=char_data)
        char_id = create_response.json()["id"]

        update_data = {"name": "Updated Name"}
        response = client.put(f"/api/characters/{char_id}", data=update_data)
        assert response.status_code == 200


class TestCampaignBasics:
    """Test basic campaign operations."""

    def test_create_campaign_with_defaults(self, client: TestClient):
        """Test campaign creation with default values."""
        data = {
            "name": "Basic Campaign",
            "description": "Test",
            "gm_name": "TestGM",
        }

        response = client.post("/campaigns/new", data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["campaign_name"] == "Basic Campaign"
        assert "gm_token" in result
        assert "campaign_id" in result

    def test_list_campaigns(self, client: TestClient):
        """Test listing campaigns."""
        response = client.get("/campaigns/api/campaigns")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_get_campaign_details(self, client: TestClient):
        """Test getting campaign details."""
        data = {"name": "Detail Test", "description": "Test", "gm_name": "GM"}
        response = client.post("/campaigns/new", data=data)
        campaign_id = response.json()["campaign_id"]

        response = client.get(f"/campaigns/api/campaign/{campaign_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["campaign_id"] == campaign_id
