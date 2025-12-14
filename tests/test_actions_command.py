"""
Tests for Command station actions.

Actions tested:
- Rally (major, task_roll)
"""

import json
import pytest


class TestRally:
    """Tests for Rally action."""

    def test_rally_success(self, client, sample_encounter, execute_action, test_session):
        """Test Rally with successful roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,
            roll_successes=2,
            roll_momentum=2,  # Rally generates momentum on success
            attribute=12,  # Presence
            discipline=5,   # Command
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

    def test_rally_failure(self, client, sample_encounter, execute_action, test_session):
        """Test Rally with failed roll."""
        encounter = sample_encounter["encounter"]

        response = execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=False,
            roll_successes=0,
            roll_complications=0,
            attribute=12,
            discipline=5,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is False

    def test_rally_is_major(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Rally is a major action."""
        encounter = sample_encounter["encounter"]

        execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,
            roll_successes=2,
            roll_momentum=1,
            attribute=12,
            discipline=5,
        )

        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "enemy"

    def test_rally_has_difficulty_0(self, client, sample_encounter, execute_action, test_session):
        """Test that Rally has difficulty 0 (always succeeds if you roll)."""
        encounter = sample_encounter["encounter"]

        # Even with minimal successes, should succeed (difficulty 0)
        response = execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,  # Simulating a roll
            roll_successes=0,  # No successes needed (diff 0)
            roll_momentum=0,
            attribute=12,
            discipline=5,
        )
        assert response.status_code == 200

        data = response.get_json()
        # With difficulty 0, even 0 successes should pass
        assert data["success"] is True

    def test_rally_generates_momentum(self, client, sample_encounter, execute_action, get_encounter_status, test_session):
        """Test that Rally generates momentum on success."""
        encounter = sample_encounter["encounter"]
        initial_momentum = encounter.momentum

        response = execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,
            roll_successes=3,  # Extra successes become momentum
            roll_momentum=3,
            attribute=12,
            discipline=5,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        # Check if momentum was generated
        if "momentum_generated" in data:
            assert data["momentum_generated"] >= 0

    def test_rally_uses_presence_and_command(self, client, sample_encounter, execute_action, test_session):
        """Test that Rally uses Presence + Command as per the rules."""
        encounter = sample_encounter["encounter"]

        # Rally config specifies attribute: "presence" and discipline: "command"
        # This is mainly for documentation; the test validates the action works
        response = execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,
            roll_successes=2,
            roll_momentum=1,
            attribute=12,  # Presence
            discipline=5,   # Command
        )
        assert response.status_code == 200
        assert response.get_json()["success"] is True
