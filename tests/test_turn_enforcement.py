"""
Tests for turn enforcement in STA Starship Simulator.

These tests verify that the turn order system properly REJECTS invalid actions:
- Players who have already acted cannot act again
- Multiplayer: players must have claimed the turn
- Single player in multiplayer cannot take multiple turns
- GM cannot take consecutive turns when players are available
"""

import json
import pytest


class TestPlayerAlreadyActed:
    """Tests that players who have already acted are blocked from acting again."""

    def test_reject_action_after_major_action(
        self, client, multiplayer_encounter, claim_turn, execute_action, test_session
    ):
        """Test that a player cannot execute another action after completing a major action."""
        from sta.database.schema import EncounterRecord

        encounter = multiplayer_encounter["encounter"]
        encounter_id = encounter.encounter_id
        player = multiplayer_encounter["players"][1]  # Non-GM player

        # Player claims turn and executes a major action
        claim_response = claim_turn(encounter_id, player.id)
        assert claim_response.status_code == 200

        # Execute a major action (Attack Pattern)
        action_response = execute_action(
            encounter_id,
            "Attack Pattern",
            player_id=player.id,
        )
        assert action_response.status_code == 200

        # Refresh encounter from DB (API may have modified it)
        test_session.expire_all()
        encounter = test_session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()

        # Now it should be enemy turn, switch back to player
        encounter.current_turn = "player"
        encounter.current_player_id = None
        test_session.commit()

        # Try to execute another action with the same player
        second_action_response = execute_action(
            encounter_id,
            "Calibrate Weapons",
            player_id=player.id,
        )

        # Should be rejected
        assert second_action_response.status_code == 403
        data = second_action_response.get_json()
        assert "already acted" in data["error"].lower()

    def test_reject_claim_after_acted(
        self, client, multiplayer_encounter, claim_turn, execute_action, test_session
    ):
        """Test that a player who has acted cannot claim the turn again."""
        encounter = multiplayer_encounter["encounter"]
        player = multiplayer_encounter["players"][1]

        # Mark player as already acted
        players_turns_used = {str(player.id): {"acted": True, "acted_at": "2025-01-01T00:00:00"}}
        encounter.players_turns_used_json = json.dumps(players_turns_used)
        test_session.commit()

        # Try to claim turn
        response = claim_turn(encounter.encounter_id, player.id)

        assert response.status_code == 400
        data = response.get_json()
        assert "already acted" in data["error"].lower()


class TestSinglePlayerMultiplayer:
    """Tests for the edge case of a single player in multiplayer mode."""

    def test_single_player_one_turn_per_round(
        self, client, test_session, sample_campaign, sample_enemy_ship_data
    ):
        """Test that a single player in multiplayer mode can only take one turn per round."""
        from sta.database.schema import (
            EncounterRecord,
            StarshipRecord,
            CampaignPlayerRecord,
        )

        campaign = sample_campaign["campaign"]
        player_ship = sample_campaign["player_ship"]

        # Remove all but one non-GM player
        players = sample_campaign["players"]
        gm = players[0]
        single_player = players[1]

        # Deactivate other players
        for p in players[2:]:
            p.is_active = False
        test_session.commit()

        # Create enemy ship
        enemy_ship = StarshipRecord(**sample_enemy_ship_data)
        test_session.add(enemy_ship)
        test_session.flush()

        # Create encounter with single active player
        encounter = EncounterRecord(
            encounter_id="single-player-test",
            name="Single Player Test",
            description="Test with single player",
            campaign_id=campaign.id,
            player_ship_id=player_ship.id,
            player_character_id=None,
            player_position="captain",
            enemy_ship_ids_json=json.dumps([enemy_ship.id]),
            momentum=2,
            threat=3,
            round=1,
            current_turn="player",
            is_active=True,
            ships_turns_used_json=json.dumps({}),
            player_turns_used=0,
            player_turns_total=1,  # Only 1 player
            players_turns_used_json=json.dumps({}),
            current_player_id=None,
            turn_claimed_at=None,
            active_effects_json=json.dumps([]),
            tactical_map_json=json.dumps({"radius": 3, "tiles": []}),
            ship_positions_json=json.dumps({
                "player": {"q": 0, "r": 0},
                "enemy_0": {"q": 1, "r": 0},
            }),
        )
        test_session.add(encounter)
        test_session.commit()

        encounter_id = encounter.encounter_id

        # Claim and execute first action
        claim_response = client.post(
            f"/api/encounter/{encounter_id}/claim-turn",
            json={"player_id": single_player.id},
            content_type="application/json",
        )
        assert claim_response.status_code == 200

        action_response = client.post(
            f"/api/encounter/{encounter_id}/execute-action",
            json={
                "action_name": "Attack Pattern",
                "player_id": single_player.id,
            },
            content_type="application/json",
        )
        assert action_response.status_code == 200

        # Refresh encounter from DB (API may have modified it)
        test_session.expire_all()
        encounter = test_session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()

        # Now try to act again - should fail
        # Reset turn to player for the test
        encounter.current_turn = "player"
        encounter.current_player_id = None
        test_session.commit()

        second_action = client.post(
            f"/api/encounter/{encounter_id}/execute-action",
            json={
                "action_name": "Calibrate Weapons",
                "player_id": single_player.id,
            },
            content_type="application/json",
        )

        assert second_action.status_code == 403
        data = second_action.get_json()
        assert "already acted" in data["error"].lower()


class TestMultipleMinorActions:
    """Tests that minor actions don't allow infinite turns."""

    def test_minor_actions_dont_mark_acted(
        self, client, multiplayer_encounter, claim_turn, execute_action, get_encounter_status, test_session
    ):
        """Test that minor actions don't mark the player as acted, allowing major action after."""
        encounter = multiplayer_encounter["encounter"]
        player = multiplayer_encounter["players"][1]

        # Claim turn
        claim_turn(encounter.encounter_id, player.id)

        # Execute a minor action
        minor_response = execute_action(
            encounter.encounter_id,
            "Calibrate Weapons",
            player_id=player.id,
        )
        assert minor_response.status_code == 200

        # Should still be player's turn
        status = get_encounter_status(encounter.encounter_id)
        assert status.get_json()["current_turn"] == "player"

        # Player should be able to execute a major action now
        major_response = execute_action(
            encounter.encounter_id,
            "Attack Pattern",
            player_id=player.id,
        )
        assert major_response.status_code == 200

        # Now player should be marked as acted and turn should switch
        status2 = get_encounter_status(encounter.encounter_id)
        assert status2.get_json()["current_turn"] == "enemy"

    def test_cannot_do_two_minor_actions(
        self, client, multiplayer_encounter, claim_turn, execute_action, test_session
    ):
        """Test that a player cannot execute two minor actions in one turn."""
        encounter = multiplayer_encounter["encounter"]
        player = multiplayer_encounter["players"][1]

        # Claim turn
        claim_turn(encounter.encounter_id, player.id)

        # Execute first minor action (Calibrate Weapons)
        first_minor = execute_action(
            encounter.encounter_id,
            "Calibrate Weapons",
            player_id=player.id,
        )
        assert first_minor.status_code == 200

        # Try to execute second minor action (Raise Shields) - should fail
        second_minor = execute_action(
            encounter.encounter_id,
            "Raise Shields",
            player_id=player.id,
        )
        assert second_minor.status_code == 403
        data = second_minor.get_json()
        assert "minor action" in data["error"].lower()


class TestFireWeaponEnforcement:
    """Tests for fire weapon action turn enforcement."""

    def test_fire_weapon_respects_acted_flag(
        self, client, multiplayer_encounter, claim_turn, test_session
    ):
        """Test that fire weapon action checks if player has already acted."""
        encounter = multiplayer_encounter["encounter"]
        player = multiplayer_encounter["players"][1]

        # Mark player as already acted
        players_turns_used = {str(player.id): {"acted": True, "acted_at": "2025-01-01T00:00:00"}}
        encounter.players_turns_used_json = json.dumps(players_turns_used)
        test_session.commit()

        # Try to fire weapon
        response = client.post(
            "/api/fire",
            json={
                "encounter_id": encounter.encounter_id,
                "weapon_index": 0,
                "target_index": 0,
                "attribute": 10,
                "discipline": 4,
                "difficulty": 2,
                "focus": False,
                "bonus_dice": 0,
                "player_id": player.id,
            },
            content_type="application/json",
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "already acted" in data["error"].lower()


class TestRamActionEnforcement:
    """Tests for ram action turn enforcement."""

    def test_ram_respects_acted_flag(
        self, client, multiplayer_encounter, test_session
    ):
        """Test that ram action checks if player has already acted."""
        encounter = multiplayer_encounter["encounter"]
        player = multiplayer_encounter["players"][1]

        # Mark player as already acted
        players_turns_used = {str(player.id): {"acted": True, "acted_at": "2025-01-01T00:00:00"}}
        encounter.players_turns_used_json = json.dumps(players_turns_used)
        test_session.commit()

        # Try to ram
        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/ram",
            json={
                "target_index": 0,
                "attribute": 10,
                "discipline": 4,
                "difficulty": 2,
                "focus": False,
                "bonus_dice": 0,
                "player_id": player.id,
            },
            content_type="application/json",
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "already acted" in data["error"].lower()


class TestRoundReset:
    """Tests that player acted flags reset when round advances."""

    def test_acted_flags_reset_on_round_advance(
        self, client, multiplayer_encounter, next_turn, test_session
    ):
        """Test that players can act again after round advances."""
        encounter = multiplayer_encounter["encounter"]
        enemy_ship = multiplayer_encounter["enemy_ship"]
        players = [p for p in multiplayer_encounter["players"] if not p.is_gm]

        # Mark all players as acted
        players_turns_used = {}
        for p in players:
            players_turns_used[str(p.id)] = {"acted": True, "acted_at": "2025-01-01T00:00:00"}
        encounter.players_turns_used_json = json.dumps(players_turns_used)

        # Mark all enemy turns as used too
        ships_turns_used = {str(enemy_ship.id): enemy_ship.scale}
        encounter.ships_turns_used_json = json.dumps(ships_turns_used)

        test_session.commit()

        initial_round = encounter.round

        # Advance turn - should advance the round
        response = next_turn(encounter.encounter_id)
        assert response.status_code == 200
        data = response.get_json()

        # Verify round advanced
        assert data["round"] == initial_round + 1

        # Verify players can act again (acted flags reset)
        # Refresh encounter from db
        test_session.refresh(encounter)
        new_players_turns = json.loads(encounter.players_turns_used_json or "{}")

        # Should be empty or all acted=False
        for p in players:
            player_data = new_players_turns.get(str(p.id), {})
            assert player_data.get("acted", False) is False
