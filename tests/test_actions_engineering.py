"""
Tests for Engineering/Operations station actions.

Actions tested:
- Damage Control (major, task_roll)
- Regain Power (major, task_roll)
- Regenerate Shields (major, task_roll)
"""

import json
import pytest


class TestDamageControl:
    """Tests for Damage Control action."""

    def test_damage_control_success(self, client, sample_encounter, execute_action, test_session):
        """Test Damage Control with successful roll."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # Add a breach to the ship
        player_ship.breaches_json = json.dumps([{"system": "engines", "potency": 2}])
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Damage Control",
            roll_succeeded=True,
            roll_successes=3,
            roll_momentum=1,
            attribute=12,
            discipline=3,
            target_system="engines",
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_damage_control_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Damage Control with failed roll."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # Add a breach
        player_ship.breaches_json = json.dumps([{"system": "engines", "potency": 2}])
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Damage Control",
            roll_succeeded=False,
            roll_successes=1,
            roll_complications=0,
            attribute=12,
            discipline=3,
            target_system="engines",
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False

    def test_damage_control_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Damage Control is a major action."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # Add a breach
        player_ship.breaches_json = json.dumps([{"system": "engines", "potency": 1}])
        test_session.commit()

        execute_action(
            encounter.encounter_id,
            "Damage Control",
            roll_succeeded=True,
            roll_successes=3,
            attribute=12,
            discipline=3,
            target_system="engines",
        )

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"

    def test_damage_control_requires_target_system(self, client, sample_encounter, execute_action, test_session):
        """Test that Damage Control requires a target_system parameter."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Damage Control",
            roll_succeeded=True,
            roll_successes=3,
            attribute=12,
            discipline=3,
            # Missing target_system
        )

        # Should fail without target_system
        assert response.status_code == 400
        data = response.get_json()
        assert "target_system" in data.get("error", "").lower()


class TestRegainPower:
    """Tests for Regain Power action."""

    def test_regain_power_success(self, client, sample_encounter, execute_action, test_session):
        """Test Regain Power with successful roll."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # Deplete reserve power first
        player_ship.has_reserve_power = False
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Regain Power",
            roll_succeeded=True,
            roll_successes=2,
            roll_momentum=1,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_regain_power_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Regain Power with failed roll."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        player_ship.has_reserve_power = False
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Regain Power",
            roll_succeeded=False,
            roll_successes=0,
            roll_complications=0,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False

    def test_regain_power_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Regain Power is a major action."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        player_ship.has_reserve_power = False
        test_session.commit()

        execute_action(
            encounter.encounter_id,
            "Regain Power",
            roll_succeeded=True,
            roll_successes=2,
            attribute=10,
            discipline=3,
        )

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"


class TestRegenerateShields:
    """Tests for Regenerate Shields action."""

    def test_regenerate_shields_success(self, client, sample_encounter, execute_action, test_session):
        """Test Regenerate Shields with successful roll."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # Ensure reserve power is available and shields are raised but depleted
        player_ship.has_reserve_power = True
        player_ship.shields_raised = True
        player_ship.shields = 5  # Partially depleted
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Regenerate Shields",
            roll_succeeded=True,
            roll_successes=3,
            roll_momentum=1,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_regenerate_shields_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Regenerate Shields with failed roll."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        player_ship.has_reserve_power = True
        player_ship.shields_raised = True
        player_ship.shields = 5
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Regenerate Shields",
            roll_succeeded=False,
            roll_successes=1,
            roll_complications=0,
            attribute=10,
            discipline=3,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False

    def test_regenerate_shields_requires_reserve_power(self, client, sample_encounter, execute_action, test_session):
        """Test that Regenerate Shields requires reserve power."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # Deplete reserve power
        player_ship.has_reserve_power = False
        player_ship.shields_raised = True
        player_ship.shields = 5
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Regenerate Shields",
            roll_succeeded=True,
            roll_successes=3,
            attribute=10,
            discipline=3,
        )

        # Should fail due to no reserve power
        assert response.status_code == 400
        data = response.get_json()
        assert "power" in data.get("error", "").lower()

    def test_regenerate_shields_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Regenerate Shields is a major action."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        player_ship.has_reserve_power = True
        player_ship.shields_raised = True
        player_ship.shields = 5
        test_session.commit()

        execute_action(
            encounter.encounter_id,
            "Regenerate Shields",
            roll_succeeded=True,
            roll_successes=3,
            attribute=10,
            discipline=3,
        )

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"
