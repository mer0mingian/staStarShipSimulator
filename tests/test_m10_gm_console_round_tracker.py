"""Tests for M10.7 - GM Console and M10.8 - Dynamic Round Tracker."""

import json
import pytest
from sqlalchemy import select
from sta.database.schema import EncounterRecord, CombatLogRecord


@pytest.mark.m10_gm_console
class TestThreatSpending:
    """Tests for GM Threat spending mechanics (M10.7)."""

    @pytest.mark.asyncio
    async def test_spend_trait_level_1(self, client, sample_encounter, test_session):
        """Test spending 1 Threat for Trait level 1."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "trait_1", "description": "Apply Dark Environment"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["threat_spent"] == 1
        assert data["threat_remaining"] == 4
        assert data["spend_name"] == "Apply Trait (Level 1)"

    @pytest.mark.asyncio
    async def test_spend_trait_level_2(self, client, sample_encounter, test_session):
        """Test spending 2 Threat for Trait level 2."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "trait_2"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["threat_spent"] == 2
        assert data["threat_remaining"] == 3

    @pytest.mark.asyncio
    async def test_spend_trait_level_3(self, client, sample_encounter, test_session):
        """Test spending 3 Threat for Trait level 3."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 10
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "trait_3"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["threat_spent"] == 3
        assert data["threat_remaining"] == 7

    @pytest.mark.asyncio
    async def test_spend_reinforcement_minor(
        self, client, sample_encounter, test_session
    ):
        """Test spending 1 Threat to add Minor NPC reinforcement."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "reinforcement_minor"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spend_name"] == "Reinforce: Minor NPC"
        assert data["threat_spent"] == 1

    @pytest.mark.asyncio
    async def test_spend_reinforcement_notable(
        self, client, sample_encounter, test_session
    ):
        """Test spending 2 Threat to add Notable NPC reinforcement."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "reinforcement_notable"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spend_name"] == "Reinforce: Notable NPC"
        assert data["threat_spent"] == 2

    @pytest.mark.asyncio
    async def test_spend_hazard(self, client, sample_encounter, test_session):
        """Test spending 2 Threat to introduce a hazard."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "hazard", "description": "Introduce plasma fire"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spend_name"] == "Introduce Hazard"
        assert data["threat_spent"] == 2

    @pytest.mark.asyncio
    async def test_spend_reversal(self, client, sample_encounter, test_session):
        """Test spending 2 Threat for Reversal."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "reversal"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spend_name"] == "Reversal"

    @pytest.mark.asyncio
    async def test_spend_npc_complication(self, client, sample_encounter, test_session):
        """Test spending 2 Threat to handle NPC complication."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "npc_complication"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spend_name"] == "NPC Complication"

    @pytest.mark.asyncio
    async def test_spend_extended_task(self, client, sample_encounter, test_session):
        """Test spending 1 Threat for extended task progress."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "extended_task"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spend_name"] == "Extended Task Progress"
        assert data["threat_spent"] == 1

    @pytest.mark.asyncio
    async def test_spend_insufficient_threat(
        self, client, sample_encounter, test_session
    ):
        """Test that spending more Threat than available fails."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 1
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "hazard"},
        )

        assert response.status_code == 400
        assert "Not enough Threat" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_spend_invalid_type(self, client, sample_encounter):
        """Test that invalid spend_type is rejected."""
        response = client.post(
            f"/api/encounter/{sample_encounter['encounter'].encounter_id}/threat/spend",
            json={"spend_type": "invalid_type"},
        )

        assert response.status_code == 400
        assert "Invalid spend_type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_threat_spend_creates_log(
        self, client, sample_encounter, test_session
    ):
        """Test that Threat spend creates a combat log entry."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 5
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "trait_1", "description": "Dark Environment"},
        )

        assert response.status_code == 200
        log_entry_id = response.json()["log_entry_id"]

        test_session.expire_all()
        result = await test_session.execute(
            select(CombatLogRecord).filter(CombatLogRecord.id == log_entry_id)
        )
        log = result.scalars().first()

        assert log is not None
        assert log.action_type == "gm_threat_spend"
        assert log.threat_spent == 1
        assert log.actor_type == "gm"


@pytest.mark.m10_gm_console
class TestClaimMomentum:
    """Tests for Claim Momentum mechanic (M10.7)."""

    @pytest.mark.asyncio
    async def test_claim_momentum_basic(self, client, sample_encounter, test_session):
        """Test converting 2 Momentum to 1 Threat."""
        encounter = sample_encounter["encounter"]
        encounter.momentum = 4
        encounter.threat = 0
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/claim-momentum",
            json={"amount": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["momentum_spent"] == 2
        assert data["threat_gained"] == 1
        assert data["momentum_remaining"] == 2
        assert data["threat_remaining"] == 1

    @pytest.mark.asyncio
    async def test_claim_momentum_multiple(
        self, client, sample_encounter, test_session
    ):
        """Test converting 4 Momentum to 2 Threat."""
        encounter = sample_encounter["encounter"]
        encounter.momentum = 6
        encounter.threat = 0
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/claim-momentum",
            json={"amount": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["momentum_spent"] == 4
        assert data["threat_gained"] == 2

    @pytest.mark.asyncio
    async def test_claim_momentum_insufficient(
        self, client, sample_encounter, test_session
    ):
        """Test that claiming Momentum without enough Momentum fails."""
        encounter = sample_encounter["encounter"]
        encounter.momentum = 1
        encounter.threat = 0
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/claim-momentum",
            json={"amount": 1},
        )

        assert response.status_code == 400
        assert "Not enough Momentum" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_claim_momentum_threat_cap(
        self, client, sample_encounter, test_session
    ):
        """Test that Threat is capped at 24."""
        encounter = sample_encounter["encounter"]
        encounter.momentum = 100
        encounter.threat = 23
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/claim-momentum",
            json={"amount": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["threat_remaining"] == 24


@pytest.mark.m10_gm_console
class TestPlayerResourceFeedback:
    """Tests for Player Resource Feedback (M10.7)."""

    @pytest.mark.asyncio
    async def test_get_player_resources_basic(
        self, client, sample_encounter, test_session
    ):
        """Test getting player resources returns threat and momentum."""
        encounter = sample_encounter["encounter"]
        encounter.threat = 10
        encounter.momentum = 3
        await test_session.commit()
        await test_session.flush()

        response = client.get(
            f"/api/encounter/{encounter.encounter_id}/player-resources"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["threat"] == 10
        assert data["threat_max"] == 24
        assert data["momentum"] == 3
        assert data["momentum_max"] == 6

    @pytest.mark.asyncio
    async def test_log_determination_spend(
        self, client, sample_encounter, test_session
    ):
        """Test logging a Determination spend."""
        encounter = sample_encounter["encounter"]
        character = sample_encounter["character"]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/log-determination",
            json={
                "character_id": character.id,
                "spend_type": "moment_of_inspiration",
                "description": "Re-roll failed attack",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["spend_type"] == "moment_of_inspiration"

        log_entry_id = data["log_entry_id"]
        test_session.expire_all()
        result = await test_session.execute(
            select(CombatLogRecord).filter(CombatLogRecord.id == log_entry_id)
        )
        log = result.scalars().first()
        assert log.action_type == "determination_spend"
        assert log.actor_type == "player"

    @pytest.mark.asyncio
    async def test_log_perfect_opportunity_spend(self, client, sample_encounter):
        """Test logging Perfect Opportunity spend."""
        encounter = sample_encounter["encounter"]
        character = sample_encounter["character"]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/log-determination",
            json={
                "character_id": character.id,
                "spend_type": "perfect_opportunity",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spend_type"] == "perfect_opportunity"

    @pytest.mark.asyncio
    async def test_log_value_interaction_challenged(self, client, sample_encounter):
        """Test logging Value Challenged interaction."""
        encounter = sample_encounter["encounter"]
        character = sample_encounter["character"]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/log-value-interaction",
            json={
                "character_id": character.id,
                "character_name": character.name,
                "value_name": "Integrity Above All",
                "interaction_type": "challenged",
                "description": "Must lie to protect crew",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["interaction_type"] == "challenged"
        assert data["value_name"] == "Integrity Above All"

    @pytest.mark.asyncio
    async def test_log_value_interaction_complied(self, client, sample_encounter):
        """Test logging Value Complied interaction."""
        encounter = sample_encounter["encounter"]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/log-value-interaction",
            json={
                "character_id": 1,
                "character_name": "Test Captain",
                "value_name": "Seek Knowledge",
                "interaction_type": "complied",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["interaction_type"] == "complied"

    @pytest.mark.asyncio
    async def test_log_value_interaction_used(self, client, sample_encounter):
        """Test logging Value Used interaction."""
        encounter = sample_encounter["encounter"]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/log-value-interaction",
            json={
                "character_id": 1,
                "character_name": "Test Captain",
                "value_name": "Loyalty to Crew",
                "interaction_type": "used",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["interaction_type"] == "used"

    @pytest.mark.asyncio
    async def test_log_value_interaction_invalid_type(self, client, sample_encounter):
        """Test that invalid interaction_type is rejected."""
        response = client.post(
            f"/api/encounter/{sample_encounter['encounter'].encounter_id}/log-value-interaction",
            json={
                "character_id": 1,
                "interaction_type": "invalid",
            },
        )

        assert response.status_code == 400
        assert "interaction_type" in response.json()["detail"]


@pytest.mark.m10_round_tracker
class TestDynamicRoundTracker:
    """Tests for Dynamic Round Tracker (M10.8)."""

    @pytest.mark.asyncio
    async def test_start_new_round(self, client, sample_encounter, test_session):
        """Test starting a new round resets action status."""
        encounter = sample_encounter["encounter"]
        encounter_id = encounter.encounter_id
        encounter.round = 2
        encounter.players_turns_used_json = json.dumps({"1": {"acted": True}})
        await test_session.commit()
        await test_session.flush()

        response = client.post(f"/api/encounter/{encounter_id}/round/start")

        assert response.status_code == 200
        data = response.json()
        assert data["old_round"] == 2
        assert data["new_round"] == 3
        assert data["all_participants_ready"] is True
        assert data["current_turn"] == "player"

        test_session.expire_all()
        result = await test_session.execute(
            select(EncounterRecord).filter(EncounterRecord.encounter_id == encounter_id)
        )
        refreshed = result.scalars().first()
        assert refreshed.round == 3
        assert refreshed.players_turns_used_json == "{}"

    @pytest.mark.asyncio
    async def test_start_new_round_creates_log(self, client, sample_encounter):
        """Test that starting new round creates a combat log entry."""
        encounter = sample_encounter["encounter"]

        response = client.post(f"/api/encounter/{encounter.encounter_id}/round/start")

        assert response.status_code == 200


@pytest.mark.m10_round_tracker
class TestParticipantActionStatus:
    """Tests for Participant Action Status toggle (M10.8)."""

    @pytest.mark.asyncio
    async def test_toggle_player_action_taken(
        self, client, sample_encounter, sample_campaign
    ):
        """Test toggling a player's action status to Action Taken."""
        encounter = sample_encounter["encounter"]
        players = sample_campaign["players"]
        player = [p for p in players if not p.is_gm][0]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/participant/{player.id}/action-status",
            json={"participant_type": "player", "action_taken": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action_taken"] is True
        assert data["participant_id"] == player.id
        assert data["participant_type"] == "player"

    @pytest.mark.asyncio
    async def test_toggle_player_action_ready(
        self, client, sample_encounter, sample_campaign
    ):
        """Test toggling a player's action status back to Ready."""
        encounter = sample_encounter["encounter"]
        players = sample_campaign["players"]
        player = [p for p in players if not p.is_gm][0]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/participant/{player.id}/action-status",
            json={"participant_type": "player", "action_taken": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action_taken"] is False

    @pytest.mark.asyncio
    async def test_toggle_enemy_ship_action(self, client, sample_encounter):
        """Test toggling an enemy ship's action status."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/participant/{enemy_ship.id}/action-status",
            json={"participant_type": "enemy_ship", "action_taken": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["participant_type"] == "enemy_ship"
        assert data["action_taken"] is True

    @pytest.mark.asyncio
    async def test_player_ship_action_switches_turn(
        self, client, sample_encounter, test_session
    ):
        """Test that marking player ship as acted switches turn to enemy."""
        encounter = sample_encounter["encounter"]
        encounter.current_turn = "player"
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/participant/player_ship/action-status",
            json={"participant_type": "player_ship", "action_taken": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_turn"] == "enemy"


@pytest.mark.m10_round_tracker
class TestRoundStatus:
    """Tests for Round Status endpoint (M10.8)."""

    @pytest.mark.asyncio
    async def test_get_round_status_basic(self, client, sample_encounter, test_session):
        """Test getting basic round status."""
        encounter = sample_encounter["encounter"]
        encounter.round = 3
        encounter.threat = 15
        encounter.momentum = 4
        await test_session.commit()
        await test_session.flush()

        response = client.get(f"/api/encounter/{encounter.encounter_id}/round-status")

        assert response.status_code == 200
        data = response.json()
        assert data["round"] == 3
        assert data["threat"] == 15
        assert data["momentum"] == 4
        assert "summary" in data
        assert "players" in data
        assert "enemy_ships" in data

    @pytest.mark.asyncio
    async def test_round_status_shows_acted_players(
        self, client, sample_encounter, sample_campaign, test_session
    ):
        """Test that round status shows which players have acted."""
        encounter = sample_encounter["encounter"]
        players = sample_campaign["players"]
        player = [p for p in players if not p.is_gm][0]

        encounter.players_turns_used_json = json.dumps(
            {str(player.id): {"acted": True}}
        )
        await test_session.commit()
        await test_session.flush()

        response = client.get(f"/api/encounter/{encounter.encounter_id}/round-status")

        assert response.status_code == 200
        data = response.json()

        players_info = data.get("players", [])
        if players_info:
            acted_player = next(
                (p for p in players_info if p.get("name") == player.player_name), None
            )
            if acted_player:
                assert acted_player["has_acted"] is True
                assert acted_player["status"] == "Action Taken"

    @pytest.mark.asyncio
    async def test_round_status_summary_all_done(
        self, client, sample_encounter, sample_campaign, test_session
    ):
        """Test round status summary when all participants have acted."""
        encounter = sample_encounter["encounter"]

        players = sample_campaign["players"]
        players_turns = {}
        for p in players:
            if not p.is_gm:
                players_turns[str(p.id)] = {"acted": True}

        encounter.players_turns_used_json = json.dumps(players_turns)
        await test_session.commit()
        await test_session.flush()

        response = client.get(f"/api/encounter/{encounter.encounter_id}/round-status")

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["players_acted"] == data["summary"]["players_total"]
        assert data["summary"]["all_players_done"] is True


@pytest.mark.round_integration
class TestThreatAndRoundIntegration:
    """Integration tests for Threat and Round Tracker working together."""

    @pytest.mark.asyncio
    async def test_full_encounter_flow(
        self, client, sample_encounter, sample_campaign, test_session
    ):
        """Test a full encounter flow: spend threat, log actions, advance rounds."""
        encounter = sample_encounter["encounter"]
        players = sample_campaign["players"]
        player = [p for p in players if not p.is_gm][0]

        encounter.threat = 10
        encounter.momentum = 3
        encounter.round = 1
        await test_session.commit()
        await test_session.flush()

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/threat/spend",
            json={"spend_type": "hazard", "description": "Asteroid field"},
        )
        assert response.status_code == 200

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/claim-momentum",
            json={"amount": 1},
        )
        assert response.status_code == 200

        response = client.post(
            f"/api/encounter/{encounter.encounter_id}/participant/{player.id}/action-status",
            json={"participant_type": "player", "action_taken": True},
        )
        assert response.status_code == 200

        response = client.get(
            f"/api/encounter/{encounter.encounter_id}/player-resources"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["threat"] == 9
        assert data["momentum"] == 1

        response = client.get(f"/api/encounter/{encounter.encounter_id}/round-status")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["players_acted"] >= 1

        response = client.post(f"/api/encounter/{encounter.encounter_id}/round/start")
        assert response.status_code == 200
        data = response.json()
        assert data["new_round"] == 2

        response = client.get(f"/api/encounter/{encounter.encounter_id}/round-status")
        assert response.status_code == 200
        data = response.json()
        assert data["round"] == 2
