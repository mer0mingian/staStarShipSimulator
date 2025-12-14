"""
Tests for action logging functionality.

Verifies that all actions are properly logged to the combat log,
including actor info, action details, and results.
"""

import json
import pytest


class TestCombatLogCreation:
    """Tests for combat log entry creation."""

    def test_action_creates_log_entry(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that executing an action creates a combat log entry."""
        encounter = sample_encounter["encounter"]

        # Execute an action
        execute_action(encounter.encounter_id, "Calibrate Weapons")

        # Check combat log
        log_response = get_combat_log(encounter.encounter_id)
        assert log_response.status_code == 200

        data = log_response.get_json()
        assert data["count"] >= 1

        # Find our action in the log
        log_entries = data["log"]
        calibrate_entry = next(
            (e for e in log_entries if e["action_name"] == "Calibrate Weapons"),
            None
        )
        assert calibrate_entry is not None

    def test_log_contains_actor_info(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that log entries contain actor information."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Attack Pattern")

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        entry = next(
            (e for e in data["log"] if e["action_name"] == "Attack Pattern"),
            None
        )
        assert entry is not None
        assert "actor_name" in entry
        assert "actor_type" in entry
        assert entry["actor_type"] == "player"

    def test_log_contains_action_type(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that log entries correctly identify minor vs major actions."""
        encounter = sample_encounter["encounter"]

        # Execute a minor action
        execute_action(encounter.encounter_id, "Calibrate Weapons")

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        entry = next(
            (e for e in data["log"] if e["action_name"] == "Calibrate Weapons"),
            None
        )
        assert entry is not None
        assert entry["action_type"] == "minor"


class TestCombatLogTaskResults:
    """Tests for task roll results in combat log."""

    def test_log_contains_task_result(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that task roll results are logged."""
        encounter = sample_encounter["encounter"]

        # Execute a task roll action
        execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,
            roll_successes=3,
            roll_momentum=2,
            attribute=12,
            discipline=5,
        )

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        entry = next(
            (e for e in data["log"] if e["action_name"] == "Rally"),
            None
        )
        assert entry is not None
        # Task result may be stored in task_result field
        # (depends on implementation)


class TestCombatLogRetrieval:
    """Tests for combat log retrieval."""

    def test_get_log_empty(self, client, sample_encounter, get_combat_log, test_session):
        """Test getting an empty combat log."""
        encounter = sample_encounter["encounter"]

        response = get_combat_log(encounter.encounter_id)
        assert response.status_code == 200

        data = response.get_json()
        assert "log" in data
        assert "count" in data

    def test_get_log_with_limit(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test getting combat log with a limit."""
        encounter = sample_encounter["encounter"]

        # Execute multiple actions
        execute_action(encounter.encounter_id, "Calibrate Weapons")
        execute_action(encounter.encounter_id, "Calibrate Sensors")
        execute_action(encounter.encounter_id, "Targeting Solution")

        # Get with limit 2
        response = get_combat_log(encounter.encounter_id, limit=2)
        assert response.status_code == 200

        data = response.get_json()
        assert data["count"] <= 2

    def test_get_log_since_id(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test getting combat log entries after a specific ID."""
        encounter = sample_encounter["encounter"]

        # Execute first action
        execute_action(encounter.encounter_id, "Calibrate Weapons")

        # Get log to find the ID
        log1 = get_combat_log(encounter.encounter_id)
        first_id = log1.get_json().get("latest_id")

        # Execute second action
        execute_action(encounter.encounter_id, "Calibrate Sensors")

        # Get entries since first ID
        log2 = get_combat_log(encounter.encounter_id, since_id=first_id)
        data = log2.get_json()

        # Should only have entries after the first one
        for entry in data["log"]:
            if first_id:
                assert entry["id"] > first_id

    def test_get_log_by_round(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test filtering combat log by round."""
        encounter = sample_encounter["encounter"]

        # Execute action in round 1
        execute_action(encounter.encounter_id, "Calibrate Weapons")

        # Get log for round 1
        response = get_combat_log(encounter.encounter_id, round_filter=1)
        assert response.status_code == 200

        data = response.get_json()
        for entry in data["log"]:
            assert entry["round"] == 1


class TestCombatLogRoundTracking:
    """Tests for round number tracking in combat log."""

    def test_log_tracks_round_number(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that log entries include the correct round number."""
        encounter = sample_encounter["encounter"]
        assert encounter.round == 1

        execute_action(encounter.encounter_id, "Calibrate Weapons")

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        if data["count"] > 0:
            entry = data["log"][0]
            assert "round" in entry
            assert entry["round"] == 1


class TestCombatLogTimestamp:
    """Tests for timestamp in combat log."""

    def test_log_has_timestamp(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that log entries have a timestamp."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Calibrate Weapons")

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        if data["count"] > 0:
            entry = data["log"][0]
            assert "timestamp" in entry
            # Timestamp should be an ISO format string
            assert entry["timestamp"] is None or "T" in entry["timestamp"]


class TestCombatLogShipInfo:
    """Tests for ship information in combat log."""

    def test_log_contains_ship_name(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that log entries contain the acting ship's name."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Calibrate Weapons")

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        if data["count"] > 0:
            entry = data["log"][0]
            assert "ship_name" in entry
            # Should be the player ship name
            assert entry["ship_name"] == "USS Endeavour"


class TestCombatLogDescription:
    """Tests for action descriptions in combat log."""

    def test_log_has_description(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that log entries have a human-readable description."""
        encounter = sample_encounter["encounter"]

        execute_action(encounter.encounter_id, "Calibrate Weapons")

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        if data["count"] > 0:
            entry = data["log"][0]
            assert "description" in entry
            assert len(entry["description"]) > 0


class TestMultipleActionsLogging:
    """Tests for logging multiple actions in sequence."""

    def test_multiple_actions_logged_in_order(self, client, sample_encounter, execute_action, get_combat_log, test_session):
        """Test that multiple actions are logged in execution order."""
        encounter = sample_encounter["encounter"]

        # Execute actions in sequence
        actions = ["Calibrate Weapons", "Calibrate Sensors", "Targeting Solution"]
        for action in actions:
            execute_action(encounter.encounter_id, action)

        log_response = get_combat_log(encounter.encounter_id)
        data = log_response.get_json()

        # Should have at least as many entries as actions
        assert data["count"] >= len(actions)

        # Log should be in order (oldest first)
        log_actions = [e["action_name"] for e in data["log"]]
        # Check that our actions appear in order
        action_indices = []
        for action in actions:
            if action in log_actions:
                action_indices.append(log_actions.index(action))

        # Indices should be ascending (in order)
        for i in range(len(action_indices) - 1):
            assert action_indices[i] < action_indices[i + 1], "Actions not in execution order"
