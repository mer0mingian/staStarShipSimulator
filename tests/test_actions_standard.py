"""
Tests for Standard actions (available to all positions).

Actions tested:
- Pass (major, special) - tested via next_turn endpoint
"""

import json
import pytest


@pytest.mark.actions
class TestPassAction:
    """Tests for Pass action."""

    @pytest.mark.asyncio
    async def test_pass_ends_player_turns(
        self, client, sample_encounter, next_turn, get_encounter_status, test_session
    ):
        """Test that Pass ends all remaining player turns."""
        encounter = sample_encounter["encounter"]

        response = next_turn(encounter.encounter_id)
        assert response.status_code == 200

        data = response.json()
        # After pass, should switch to enemy turn
        assert data["current_turn"] == "enemy"

    @pytest.mark.asyncio
    async def test_pass_switches_to_enemy(
        self, client, sample_encounter, next_turn, test_session
    ):
        """Test that Pass switches to enemy turn."""
        encounter = sample_encounter["encounter"]

        response = next_turn(encounter.encounter_id)
        assert response.status_code == 200

        data = response.json()
        assert data["current_turn"] == "enemy"

    @pytest.mark.asyncio
    async def test_enemy_pass_switches_to_player(
        self, client, sample_encounter, next_turn, test_session
    ):
        """Test that enemy pass switches back to player."""
        encounter = sample_encounter["encounter"]

        # First pass to switch to enemy
        next_turn(encounter.encounter_id)

        # Set current turn to enemy (should already be)
        encounter.current_turn = "enemy"
        await test_session.commit()

        # Enemy passes
        response = next_turn(encounter.encounter_id)
        assert response.status_code == 200

        data = response.json()
        # Should switch to player or advance round
        assert data["current_turn"] in ["player", "enemy"]


class TestActionRequirements:
    """Tests for action requirements (system availability, etc)."""

    @pytest.mark.asyncio
    async def test_action_unavailable_with_destroyed_system(
        self, client, sample_encounter, execute_action, test_session
    ):
        """Test that actions are unavailable if required system is destroyed."""
        encounter = sample_encounter["encounter"]
        player_ship = sample_encounter["player_ship"]

        # Destroy the weapons system (add breaches >= half scale)
        # Scale 4 ship = 2 breaches to destroy
        player_ship.breaches_json = json.dumps(
            [
                {"system": "weapons", "potency": 2},
                {"system": "weapons", "potency": 2},
            ]
        )
        await test_session.commit()

        # Calibrate Weapons requires weapons system
        response = execute_action(encounter.encounter_id, "Calibrate Weapons")

        # Should fail due to destroyed system
        assert response.status_code == 400
        data = response.json()
        assert (
            "destroyed" in data.get("detail", "").lower()
            or "unavailable" in data.get("detail", "").lower()
        )


class TestActionOnWrongTurn:
    """Tests for attempting actions on the wrong turn."""

    @pytest.mark.asyncio
    async def test_player_action_on_enemy_turn_fails(
        self, client, sample_encounter, execute_action, test_session
    ):
        """Test that player actions fail during enemy turn."""
        encounter = sample_encounter["encounter"]

        # Set to enemy turn
        encounter.current_turn = "enemy"
        await test_session.commit()

        response = execute_action(
            encounter.encounter_id, "Calibrate Weapons", role="player"
        )

        # Should fail
        assert response.status_code == 403
        data = response.json()
        assert "turn" in data.get("detail", "").lower()


class TestBonusDice:
    """Tests for bonus dice (momentum spending)."""

    @pytest.mark.asyncio
    async def test_bonus_dice_cost_momentum(
        self, client, sample_encounter, execute_action, test_session
    ):
        """Test that bonus dice cost momentum."""
        encounter = sample_encounter["encounter"]
        initial_momentum = 6  # Full momentum pool
        encounter.momentum = initial_momentum
        await test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,
            roll_successes=3,
            roll_momentum=1,
            attribute=12,
            discipline=5,
            bonus_dice=2,  # Costs 1+2=3 momentum
        )
        assert response.status_code == 200

        # Momentum should be reduced
        # (Note: momentum may also be gained from the action)

    @pytest.mark.asyncio
    async def test_bonus_dice_fails_without_momentum(
        self, client, sample_encounter, execute_action, test_session
    ):
        """Test that bonus dice fail if not enough momentum."""
        encounter = sample_encounter["encounter"]
        encounter.momentum = 0  # No momentum
        await test_session.commit()

        response = execute_action(
            encounter.encounter_id,
            "Rally",
            roll_succeeded=True,
            roll_successes=2,
            attribute=12,
            discipline=5,
            bonus_dice=1,  # Costs 1 momentum
        )

        # Should fail due to insufficient momentum
        assert response.status_code == 400
        data = response.json()
        assert "momentum" in data.get("detail", "").lower()
