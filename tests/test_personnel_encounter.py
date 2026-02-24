"""Tests for personnel encounter API endpoints."""

import json
import pytest
from tests.conftest import *  # noqa: F401, F403


class TestPersonnelEncounterAPI:
    """Test personnel encounter creation and status."""

    def test_create_personnel_encounter(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test creating a personnel encounter."""
        response = client.post(
            f"/api/personnel/{scene_personal.id}/create",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "encounter_id" in data

    def test_create_personnel_encounter_wrong_type(
        self, client, test_session, sample_campaign, scene
    ):
        """Test creating personnel encounter fails for non-personal scene."""
        response = client.post(
            f"/api/personnel/{scene.id}/create",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_get_personnel_status(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test getting personnel encounter status."""
        # Create encounter first
        client.post(f"/api/personnel/{scene_personal.id}/create")

        response = client.get(f"/api/personnel/{scene_personal.id}/status")
        assert response.status_code == 200
        data = response.get_json()
        assert "current_turn" in data
        assert "round" in data
        assert "momentum" in data
        assert "characters" in data

    def test_add_character_to_personnel(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test adding a character to personnel encounter."""
        # Create encounter first
        client.post(f"/api/personnel/{scene_personal.id}/create")

        response = client.post(
            f"/api/personnel/{scene_personal.id}/add-character",
            json={
                "name": "Test Character",
                "is_player": True,
                "stress_max": 5,
                "position": {"q": 0, "r": 0},
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["character_index"] == 0
        assert data["character"]["name"] == "Test Character"

    def test_get_personnel_actions(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test getting available personnel actions."""
        # Create encounter first
        client.post(f"/api/personnel/{scene_personal.id}/create")

        response = client.get(f"/api/personnel/{scene_personal.id}/action-availability")
        assert response.status_code == 200
        data = response.get_json()
        assert "minor_actions" in data
        assert "major_actions" in data
        assert "Personnel Attack" in data["major_actions"]
        assert "First Aid" in data["major_actions"]
        assert "Guard" in data["major_actions"]

    def test_self_targeting_prevention(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test that characters cannot target themselves."""
        # Create encounter and add two characters
        client.post(f"/api/personnel/{scene_personal.id}/create")
        client.post(
            f"/api/personnel/{scene_personal.id}/add-character",
            json={"name": "Attacker", "is_player": True, "stress_max": 5},
        )

        # Try to attack self - should fail
        response = client.post(
            f"/api/personnel/{scene_personal.id}/execute-action",
            json={
                "action": "Personnel Attack",
                "character_index": 0,
                "target_index": 0,  # Same as attacker!
                "attribute": "daring",
                "discipline": "security",
                "difficulty": 1,
                "severity": 2,
                "injury_type": "stun",
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Cannot target yourself" in data["error"]

    def test_invalid_character_index(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test that invalid character_index is rejected."""
        client.post(f"/api/personnel/{scene_personal.id}/create")
        client.post(
            f"/api/personnel/{scene_personal.id}/add-character",
            json={"name": "Character", "is_player": True, "stress_max": 5},
        )

        # Test negative index
        response = client.post(
            f"/api/personnel/{scene_personal.id}/execute-action",
            json={
                "action": "Guard",
                "character_index": -1,
            },
        )
        assert response.status_code == 400

        # Test out of bounds index
        response = client.post(
            f"/api/personnel/{scene_personal.id}/execute-action",
            json={
                "action": "Guard",
                "character_index": 999,
            },
        )
        assert response.status_code == 400

    def test_update_character_position(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test updating character position on map."""
        # Create encounter and add character
        client.post(f"/api/personnel/{scene_personal.id}/create")
        client.post(
            f"/api/personnel/{scene_personal.id}/add-character",
            json={"name": "Test", "is_player": True, "position": {"q": 0, "r": 0}},
        )

        response = client.post(
            f"/api/personnel/{scene_personal.id}/map/position",
            json={"character_index": 0, "position": {"q": 1, "r": -1}},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["position"] == {"q": 1, "r": -1}

    def test_next_turn(self, client, test_session, sample_campaign, scene_personal):
        """Test advancing to next turn."""
        # Create encounter first
        client.post(f"/api/personnel/{scene_personal.id}/create")

        response = client.post(f"/api/personnel/{scene_personal.id}/next-turn")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_delete_personnel_encounter(
        self, client, test_session, sample_campaign, scene_personal
    ):
        """Test deleting a personnel encounter."""
        # Create encounter first
        client.post(f"/api/personnel/{scene_personal.id}/create")

        response = client.delete(f"/api/personnel/{scene_personal.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True


class TestPersonnelSceneActivation:
    """Test personnel encounter activation from scenes."""

    def test_activate_personal_encounter_creates_record(
        self, client, test_session, sample_campaign, scene_personal, gm_session
    ):
        """Test activating a personal encounter scene creates personnel encounter."""
        # Set GM session
        client.set_cookie("sta_session_token", gm_session.session_token)

        # Activate scene
        response = client.put(
            f"/campaigns/api/scene/{scene_personal.id}/status",
            json={"status": "active"},
        )
        assert response.status_code == 200

        # Verify personnel encounter was created
        from sta.database import PersonnelEncounterRecord

        personnel = (
            test_session.query(PersonnelEncounterRecord)
            .filter_by(scene_id=scene_personal.id)
            .first()
        )
        assert personnel is not None
        assert personnel.momentum == 0
        assert personnel.round == 1
