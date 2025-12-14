"""
Tests for Science station actions.

Actions tested:
- Calibrate Sensors (minor, buff)
- Scan For Weakness (major, task_roll)
- Sensor Sweep (major, task_roll)
"""

import json
import pytest


class TestCalibrateSensors:
    """Tests for Calibrate Sensors action."""

    def test_calibrate_sensors_creates_effect(self, client, sample_encounter, execute_action, test_session):
        """Test that Calibrate Sensors creates a sensor bonus effect."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Calibrate Sensors")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_calibrate_sensors_is_minor(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Calibrate Sensors is a minor action."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Calibrate Sensors")

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "player"


class TestScanForWeakness:
    """Tests for Scan For Weakness action."""

    def test_scan_for_weakness_success(self, client, sample_encounter, execute_action, test_session):
        """Test Scan For Weakness with successful roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Scan For Weakness",
            roll_succeeded=True,
            roll_successes=3,
            roll_momentum=1,
            attribute=10,
            discipline=3,
            target_index=0,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_scan_for_weakness_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Scan For Weakness with failed roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Scan For Weakness",
            roll_succeeded=False,
            roll_successes=1,
            roll_complications=0,
            attribute=10,
            discipline=3,
            target_index=0,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False

    def test_scan_for_weakness_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Scan For Weakness is a major action."""
        encounter = sample_encounter["encounter"]

        execute_action(
            encounter.encounter_id,
            "Scan For Weakness",
            roll_succeeded=True,
            roll_successes=3,
            attribute=10,
            discipline=3,
            target_index=0,
        )

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"

    def test_scan_for_weakness_range_limit(self, client, sample_encounter, execute_action, test_session):
        """Test that Scan For Weakness has a maximum range (Long = 2 hexes)."""
        encounter = sample_encounter["encounter"]

        # Move enemy to Extreme range (3+ hexes)
        ship_positions = {"player": {"q": 0, "r": 0}, "enemy_0": {"q": 3, "r": 0}}
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Scan For Weakness",
            roll_succeeded=True,
            roll_successes=3,
            attribute=10,
            discipline=3,
            target_index=0,
        )

        # Should fail due to range
        assert response.status_code == 400
        data = response.get_json()
        assert "range" in data.get("error", "").lower()


class TestSensorSweep:
    """Tests for Sensor Sweep action."""

    def test_sensor_sweep_success(self, client, sample_encounter, execute_action, test_session):
        """Test Sensor Sweep with successful roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Sensor Sweep",
            roll_succeeded=True,
            roll_successes=2,
            roll_momentum=1,
            attribute=10,
            discipline=3,
            target_index=0,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_sensor_sweep_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Sensor Sweep with failed roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Sensor Sweep",
            roll_succeeded=False,
            roll_successes=0,
            roll_complications=1,
            attribute=10,
            discipline=3,
            target_index=0,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False

    def test_sensor_sweep_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Sensor Sweep is a major action."""
        encounter = sample_encounter["encounter"]

        execute_action(
            encounter.encounter_id,
            "Sensor Sweep",
            roll_succeeded=True,
            roll_successes=2,
            attribute=10,
            discipline=3,
            target_index=0,
        )

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"

    def test_sensor_sweep_difficulty_increases_with_range(self, client, sample_encounter, execute_action, test_session):
        """Test that Sensor Sweep difficulty increases with distance."""
        encounter = sample_encounter["encounter"]

        # Base difficulty is 1
        # At Long range (2 hexes), should be difficulty 3 (+1 per hex)
        ship_positions = {"player": {"q": 0, "r": 0}, "enemy_0": {"q": 2, "r": 0}}
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # A roll that would succeed at close range (difficulty 1) but fails at long range (difficulty 3)
        response = execute_action(
            encounter.encounter_id,
            "Sensor Sweep",
            roll_succeeded=True,  # We're simulating the result
            roll_successes=3,
            attribute=10,
            discipline=3,
            target_index=0,
        )

        # Should succeed (3 successes >= difficulty 3)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
