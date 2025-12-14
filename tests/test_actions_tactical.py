"""
Tests for Tactical/Security station actions.

Actions tested:
- Calibrate Weapons (minor, buff)
- Targeting Solution (minor, buff)
- Raise/Lower Shields (minor, toggle)
- Arm/Disarm Weapons (minor, toggle)
- Modulate Shields (major, task_roll)
"""

import json
import pytest


class TestCalibrateWeapons:
    """Tests for Calibrate Weapons action."""

    def test_calibrate_weapons_creates_effect(self, client, sample_encounter, execute_action, test_session):
        """Test that Calibrate Weapons creates a damage bonus effect."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Calibrate Weapons")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "effect_created" in data or "Calibrate Weapons" in data.get("message", "")

    def test_calibrate_weapons_is_minor(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Calibrate Weapons is a minor action (doesn't end turn)."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Calibrate Weapons")

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "player"


class TestTargetingSolution:
    """Tests for Targeting Solution action."""

    def test_targeting_solution_creates_effect(self, client, sample_encounter, execute_action, test_session):
        """Test that Targeting Solution creates an effect."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Targeting Solution")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_targeting_solution_is_minor(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Targeting Solution is a minor action."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Targeting Solution")

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "player"


class TestShieldToggle:
    """Tests for Raise/Lower Shields toggle actions."""

    def test_raise_shields(self, client, sample_encounter, execute_action, test_session):
        """Test raising shields."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # First lower shields
        player_ship.shields_raised = False
        test_session.commit()

        response = execute_action(encounter.encounter_id, "Raise Shields")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_lower_shields(self, client, sample_encounter, execute_action, test_session):
        """Test lowering shields."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Lower Shields")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_shield_toggle_is_minor(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that shield toggling is a minor action."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Lower Shields")

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "player"


class TestWeaponToggle:
    """Tests for Arm/Disarm Weapons toggle actions."""

    def test_arm_weapons(self, client, sample_encounter, execute_action, test_session):
        """Test arming weapons."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # First disarm
        player_ship.weapons_armed = False
        test_session.commit()

        response = execute_action(encounter.encounter_id, "Arm Weapons")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_disarm_weapons(self, client, sample_encounter, execute_action, test_session):
        """Test disarming weapons."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Disarm Weapons")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_weapon_toggle_is_minor(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that weapon toggling is a minor action."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Disarm Weapons")

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "player"


class TestModulateShields:
    """Tests for Modulate Shields action (task roll)."""

    def test_modulate_shields_success(self, client, sample_encounter, execute_action, test_session):
        """Test Modulate Shields with successful roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Modulate Shields",
            roll_succeeded=True,
            roll_successes=2,
            roll_momentum=1,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_modulate_shields_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Modulate Shields with failed roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Modulate Shields",
            roll_succeeded=False,
            roll_successes=0,
            roll_complications=0,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False
        assert "failed" in data["message"].lower()

    def test_modulate_shields_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Modulate Shields is a major action."""
        encounter = sample_encounter["encounter"]

        execute_action(
            encounter.encounter_id,
            "Modulate Shields",
            roll_succeeded=True,
            roll_successes=2,
            attribute=10,
            discipline=3,
        )

        status = get_encounter_status(encounter.encounter_id)
        # Should have switched to enemy turn
        assert status.get_json()["current_turn"] == "enemy"
