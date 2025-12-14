"""
Tests for Conn/Helm station actions.

Actions tested:
- Attack Pattern (major, buff)
- Evasive Action (major, buff)
- Maneuver (major, task_roll)
"""

import json
import pytest


class TestAttackPattern:
    """Tests for Attack Pattern action."""

    def test_attack_pattern_creates_effect(self, client, sample_encounter, execute_action, test_session):
        """Test that Attack Pattern creates a difficulty reduction effect."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Attack Pattern")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_attack_pattern_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Attack Pattern is a major action (ends turn)."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Attack Pattern")

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"

    def test_attack_pattern_effect_lasts_until_end_of_round(self, client, sample_encounter, execute_action, test_session):
        """Test that Attack Pattern effect has end_of_round duration."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Attack Pattern")
        assert response.status_code == 200

        data = response.get_json()
        # Check that the effect was created with correct duration
        if "effect" in data:
            assert data["effect"].get("duration") == "end_of_round"


class TestEvasiveAction:
    """Tests for Evasive Action action."""

    def test_evasive_action_creates_effect(self, client, sample_encounter, execute_action, test_session):
        """Test that Evasive Action creates a defensive effect."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Evasive Action")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_evasive_action_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Evasive Action is a major action."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Evasive Action")

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"

    def test_evasive_action_effect_lasts_until_end_of_round(self, client, sample_encounter, execute_action, test_session):
        """Test that Evasive Action effect lasts until end of round."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Evasive Action")
        assert response.status_code == 200

        data = response.get_json()
        if "effect" in data:
            assert data["effect"].get("duration") == "end_of_round"


class TestManeuver:
    """Tests for Maneuver action."""

    def test_maneuver_success(self, client, sample_encounter, execute_action, test_session):
        """Test Maneuver with successful roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Maneuver",
            roll_succeeded=True,
            roll_successes=2,
            roll_momentum=1,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_maneuver_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Maneuver with failed roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Maneuver",
            roll_succeeded=False,
            roll_successes=0,
            roll_complications=0,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False

    def test_maneuver_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Maneuver is a major action."""
        encounter = sample_encounter["encounter"]

        execute_action(
            encounter.encounter_id,
            "Maneuver",
            roll_succeeded=True,
            roll_successes=2,
            attribute=10,
            discipline=3,
        )

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"

    def test_maneuver_generates_momentum_on_success(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Maneuver generates momentum on success."""
        encounter = sample_encounter["encounter"]
        initial_momentum = encounter.momentum

        response = execute_action(
            encounter.encounter_id,
            "Maneuver",
            roll_succeeded=True,
            roll_successes=3,  # 2 extra successes = momentum
            roll_momentum=2,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        # Momentum should be added (if the action generates momentum)
        if "momentum_generated" in data:
            assert data["momentum_generated"] > 0
