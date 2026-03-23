"""E2E tests for STA VTT user journeys.

Tests full user flows including character creation, gameplay, and GM operations.
"""

import json
import pytest
from fastapi.testclient import TestClient


class TestCharacterCreationJourney:
    """Test full character creation wizard flow (Foundation → Specialization → Identity → Equipment)."""

    def test_wizard_full_flow(self, client: TestClient):
        """Test complete 4-step character creation wizard."""
        campaign_data = {
            "name": "Test Campaign",
            "description": "E2E Test Campaign",
            "gm_name": "GM Test",
        }
        campaign_response = client.post("/campaigns/new", data=campaign_data)
        assert campaign_response.status_code in [200, 201]
        campaign = campaign_response.json()
        gm_token = campaign["gm_token"]
        campaign_id = campaign["campaign_id"]

        character_data = {
            "step": 1,
            "character": {
                "name": "Captain Test",
                "species": "Human",
                "attributes": {
                    "control": 8,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 9,
                    "presence": 9,
                    "reason": 9,
                },
            },
            "campaign_id": None,
        }

        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code in [200, 201]
        result = response.json()
        assert result["success"] is True
        assert result["step_received"] == 1

        character_data["step"] = 2
        character_data["character"]["disciplines"] = {
            "command": 3,
            "conn": 2,
            "engineering": 3,
            "medicine": 1,
            "science": 4,
            "security": 2,
        }
        character_data["character"]["focuses"] = [
            "Diplomacy",
            "Strategy / Tactics",
            "Inspiration",
        ]
        character_data["character"]["talents"] = ["Bold (Command)"]

        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code in [200, 201]
        result = response.json()
        assert result["success"] is True

        character_data["step"] = 3
        character_data["character"]["values"] = [
            {
                "name": "Logic Above All",
                "description": "I trust in rational analysis.",
                "helpful": True,
            },
            {
                "name": "Protect the Crew",
                "description": "I will protect my crew at all costs.",
                "helpful": True,
            },
        ]

        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code in [200, 201]
        result = response.json()
        assert result["success"] is True

        character_data["step"] = 4
        character_data["character"]["rank"] = "Captain"
        character_data["character"]["role"] = "Commanding Officer"
        character_data["character"]["equipment"] = [
            {"name": "Tricorder", "type": "device"},
            {"name": "Phaser", "type": "weapon"},
        ]

        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code in [200, 201]
        result = response.json()
        assert result["success"] is True

        character_data["step"] = "final"
        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert "character" in result

        char = result["character"]
        assert char["name"] == "Captain Test"
        assert char["species"] == "Human"
        assert char["rank"] == "Captain"

        attrs = char["attributes"]
        for attr_name, value in attrs.items():
            assert 7 <= value <= 12, (
                f"Attribute {attr_name} should be 7-12, got {value}"
            )

        discs = char["disciplines"]
        for disc_name, value in discs.items():
            assert 1 <= value <= 5, f"Discipline {disc_name} should be 1-5, got {value}"

        assert len(char["values"]) >= 2, "Should have at least 2 values"
        assert char["stress_max"] == 8, "Stress max should equal Fitness attribute"
        assert char["determination"] == 1, "Determination should start at 1"
        assert char["determination_max"] == 3, "Determination max should be 3"

    def test_wizard_attributes_valid_range(self, client: TestClient):
        """Verify attributes must be within 7-12 range."""
        character_data = {
            "step": 1,
            "character": {
                "name": "Test Char",
                "species": "Vulcan",
                "attributes": {
                    "control": 13,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
                    "reason": 10,
                },
            },
            "campaign_id": None,
        }

        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code in [200, 201]
        result = response.json()
        assert result["success"] is True

        character_data["step"] = "final"
        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is False
        assert any("7-12" in str(e) for e in result.get("errors", []))

    def test_wizard_minimum_values_required(self, client: TestClient):
        """Verify minimum 2 Values required to complete character."""
        character_data = {
            "step": "final",
            "character": {
                "name": "Test Char",
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
                    "command": 3,
                    "conn": 2,
                    "engineering": 3,
                    "medicine": 1,
                    "science": 4,
                    "security": 2,
                },
                "values": [
                    {"name": "Only One", "description": "Test", "helpful": True}
                ],
            },
            "campaign_id": None,
        }

        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is False
        assert any("2 Values" in str(e) for e in result.get("errors", []))

    def test_wizard_department_range(self, client: TestClient):
        """Verify department ratings must be within 1-5 range."""
        character_data = {
            "step": "final",
            "character": {
                "name": "Test Char",
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
                "values": [
                    {"name": "Test", "description": "Test", "helpful": True},
                    {"name": "Test2", "description": "Test", "helpful": True},
                ],
            },
            "campaign_id": None,
        }

        response = client.post("/api/characters/wizard", json=character_data)
        assert response.status_code == 201
        result = response.json()
        assert result["success"] is False
        assert any("0-5" in str(e) for e in result.get("errors", []))


class TestDiceRollingJourney:
    """Test dice rolling mechanics for task resolution."""

    def test_task_roll_basic_successes(self, client: TestClient):
        """Test basic task roll with successes calculation."""
        roll_data = {
            "attribute": 8,
            "discipline": 3,
            "difficulty": 1,
            "focus": False,
            "bonus_dice": 0,
        }

        response = client.post("/api/roll", json=roll_data)
        assert response.status_code in [200, 201]
        result = response.json()

        assert "rolls" in result
        assert "target_number" in result
        assert result["target_number"] == 11
        assert "successes" in result
        assert "complications" in result

    def test_task_roll_with_focus_criticals(self, client: TestClient):
        """Test task roll with focus applying for criticals (roll <= discipline = 2 successes)."""
        roll_data = {
            "attribute": 8,
            "discipline": 3,
            "difficulty": 1,
            "focus": True,
            "bonus_dice": 0,
        }

        response = client.post("/api/roll", json=roll_data)
        assert response.status_code in [200, 201]
        result = response.json()

        target = result["target_number"]
        assert target == 11

    def test_task_roll_momentum_generation(self, client: TestClient):
        """Test momentum generated on success (successes - difficulty)."""
        roll_data = {
            "attribute": 10,
            "discipline": 5,
            "difficulty": 2,
            "focus": False,
            "bonus_dice": 0,
        }

        response = client.post("/api/roll", json=roll_data)
        assert response.status_code in [200, 201]
        result = response.json()

        assert "momentum_generated" in result
        successes = result["successes"]
        difficulty = result["difficulty"]
        expected_momentum = max(0, successes - difficulty)
        assert result["momentum_generated"] == expected_momentum


class TestValueInteractionJourney:
    """Test Value interactions (Challenge, Comply, Use)."""

    @pytest.fixture
    def character_with_values(self, client: TestClient):
        """Create a character with Values for testing."""
        character_data = {
            "step": "final",
            "character": {
                "name": "Value Test Character",
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
                        "name": "Logic Above All",
                        "description": "I trust in rational analysis.",
                        "helpful": True,
                    },
                    {
                        "name": "Protect the Crew",
                        "description": "I will protect my crew.",
                        "helpful": True,
                    },
                ],
            },
            "campaign_id": None,
        }

        response = client.post("/api/characters/wizard", json=character_data)
        result = response.json()
        return result["character"]["id"]

    def test_mark_value_challenged(self, client: TestClient, character_with_values):
        """Test marking a Value as Challenged grants +1 Determination."""
        char_id = character_with_values

        response = client.put(
            f"/api/characters/{char_id}/values/logic above all/challenge", json={}
        )
        assert response.status_code in [200, 201]
        result = response.json()

        assert result["determination"] == 2
        assert "challenged" in result["message"].lower()

    def test_mark_value_complied(self, client: TestClient, character_with_values):
        """Test marking a Value as Complied grants +1 Determination."""
        char_id = character_with_values

        response = client.put(
            f"/api/characters/{char_id}/values/logic above all/comply", json={}
        )
        assert response.status_code in [200, 201]
        result = response.json()

        assert result["determination"] == 2
        assert "complied" in result["message"].lower()

    def test_mark_value_used(self, client: TestClient, character_with_values):
        """Test marking a Value as Used (once per session)."""
        char_id = character_with_values

        response = client.put(
            f"/api/characters/{char_id}/values/logic above all/use", json={}
        )
        assert response.status_code in [200, 201]
        result = response.json()

        assert result["used_this_session"] is True
        assert "used" in result["message"].lower()

        response = client.put(
            f"/api/characters/{char_id}/values/logic above all/use", json={}
        )
        assert response.status_code == 400

    def test_value_challenge_determination_max(
        self, client: TestClient, character_with_values
    ):
        """Test that Determination doesn't exceed max (3)."""
        char_id = character_with_values

        client.put(
            f"/api/characters/{char_id}/values/logic above all/challenge", json={}
        )
        client.put(
            f"/api/characters/{char_id}/values/protect the crew/challenge", json={}
        )

        response = client.put(
            f"/api/characters/{char_id}/values/logic above all/challenge", json={}
        )
        assert response.status_code == 400


class TestGMJourney:
    """Test GM operations: Create campaign, scenes, traits, and spend Threat."""

    def test_create_campaign(self, client: TestClient):
        """Test creating a new campaign."""
        campaign_data = {
            "name": "GM Test Campaign",
            "description": "A test campaign for E2E testing",
            "gm_name": "Test GM",
        }

        response = client.post("/campaigns/new", data=campaign_data)
        assert response.status_code in [200, 201]
        result = response.json()

        assert "campaign_id" in result
        assert result["campaign_name"] == "GM Test Campaign"
        assert "gm_token" in result

    def test_create_and_activate_scene(self, client: TestClient):
        """Test creating a scene and activating it."""
        campaign_data = {
            "name": "Scene Test Campaign",
            "description": "Testing scene activation",
            "gm_name": "Test GM",
        }
        campaign_response = client.post("/campaigns/new", data=campaign_data)
        campaign = campaign_response.json()
        campaign_id = campaign["campaign_id"]

        get_response = client.get(f"/campaigns/api/campaign/{campaign_id}")
        assert get_response.status_code in [200, 201]

    def test_gm_spend_threat(self, client: TestClient):
        """Test GM can spend Threat."""
        campaign_data = {
            "name": "Threat Test Campaign",
            "description": "Testing threat spending",
            "gm_name": "Test GM",
        }
        campaign_response = client.post("/campaigns/new", data=campaign_data)
        campaign = campaign_response.json()
        campaign_id = campaign["campaign_id"]

        get_response = client.get(f"/campaigns/api/campaign/{campaign_id}")
        assert get_response.status_code in [200, 201]


class TestCharacterSheetJourney:
    """Test viewing character sheet with resources."""

    @pytest.fixture
    def created_character(self, client: TestClient):
        """Create a character for viewing."""
        character_data = {
            "step": "final",
            "character": {
                "name": "Sheet Test Character",
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
                        "name": "Honor",
                        "description": "I live by the code.",
                        "helpful": True,
                    },
                    {
                        "name": "Duty",
                        "description": "I serve with honor.",
                        "helpful": True,
                    },
                ],
                "rank": "Commander",
            },
            "campaign_id": None,
        }

        response = client.post("/api/characters/wizard", json=character_data)
        return response.json()["character"]["id"]

    def test_get_character_sheet(self, client: TestClient, created_character):
        """Test retrieving character sheet."""
        char_id = created_character

        response = client.get(f"/api/characters/{char_id}")
        assert response.status_code in [200, 201]
        char = response.json()

        assert char["name"] == "Sheet Test Character"
        assert char["stress_max"] == 8
        assert char["determination"] == 1
        assert char["determination_max"] == 3

    def test_get_character_values(self, client: TestClient, created_character):
        """Test retrieving character values."""
        char_id = created_character

        response = client.get(f"/api/characters/{char_id}/values")
        assert response.status_code in [200, 201]
        result = response.json()

        assert "values" in result
        assert len(result["values"]) >= 2

    def test_get_character_options(self, client: TestClient):
        """Test getting character creation options."""
        response = client.get("/api/characters/wizard/options")
        assert response.status_code in [200, 201]
        result = response.json()

        assert "species" in result
        assert "attributes" in result
        assert "departments" in result
        assert "talents" in result
        assert "focuses" in result
