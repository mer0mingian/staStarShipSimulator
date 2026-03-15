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


@pytest.mark.action_tactical
class TestCalibrateWeapons:
    """Tests for Calibrate Weapons action."""

    @pytest.mark.asyncio
    async def test_calibrate_weapons_creates_effect(
        self, client, sample_encounter, execute_action, test_session
    ):
        """Test that Calibrate Weapons creates a damage bonus effect."""
        encounter = sample_encounter["encounter"]

        response = execute_action(encounter.encounter_id, "Calibrate Weapons")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "effect_created" in data or "Calibrate Weapons" in data.get(
            "message", ""
        )


@pytest.mark.action_tactical
class TestModulateShields:
    """Tests for Modulate Shields action (task roll)."""

    @pytest.mark.asyncio
    async def test_modulate_shields_success(
        self, client, sample_encounter, execute_action, test_session
    ):
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

        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_modulate_shields_failure(
        self, client, sample_encounter, execute_action, test_session
    ):
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

        data = response.json()
        assert data["success"] is False
        assert "failed" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_modulate_shields_is_major(
        self,
        client,
        sample_encounter,
        execute_action,
        get_encounter_status,
        test_session,
    ):
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
        assert status.json()["current_turn"] == "enemy"
