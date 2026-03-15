"""Tests for scene activation endpoint (M3 Task 3.4)."""

import json
import uuid
import pytest
from sqlalchemy import select
from sta.database import (
    SceneRecord,
    CampaignRecord,
    StarshipRecord,
    EncounterRecord,
    PersonnelEncounterRecord,
    VTTCharacterRecord,
    CampaignPlayerRecord,
)
from sta.database.schema import SceneShipRecord, SceneParticipantRecord


class TestSceneActivationAPI:
    """Tests for POST /api/scenes/<id>/activate."""

    @pytest.mark.asyncio
    async def test_activate_starship_success(
        self, client, test_session, sample_campaign, sample_enemy_ship_data
    ):
        """Activating a starship scene creates EncounterRecord, reduces momentum, sets scene active."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        # Set initial momentum to 5
        campaign.momentum = 5
        await test_session.commit()

        # Create a draft starship scene
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Starship Encounter",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.flush()

        # Add player ship to scene_ships (campaign.active_ship_id)
        player_ship_id = campaign.active_ship_id
        test_session.add(
            SceneShipRecord(
                scene_id=scene.id, ship_id=player_ship_id, is_visible_to_players=False
            )
        )

        # Add an enemy ship
        enemy_ship = StarshipRecord(**sample_enemy_ship_data)
        test_session.add(enemy_ship)
        await test_session.flush()
        test_session.add(
            SceneShipRecord(
                scene_id=scene.id, ship_id=enemy_ship.id, is_visible_to_players=False
            )
        )
        await test_session.commit()

        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "active"
        assert "encounter_id" in data

        # Commit to expire session and see changes
        await test_session.commit()

        # Check scene status updated
        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene_id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "active"

        # Check encounter created
        encounter_id = data["encounter_id"]
        result = await test_session.execute(
            select(EncounterRecord).filter(EncounterRecord.id == encounter_id)
        )
        encounter = result.scalars().first()
        assert encounter is not None
        assert encounter.campaign_id == campaign.id
        assert encounter.player_ship_id == player_ship_id
        # Enemy ship IDs should be JSON array containing only the enemy ship
        enemy_ids = json.loads(encounter.enemy_ship_ids_json)
        assert enemy_ids == [enemy_ship.id]
        assert encounter.is_active is True

        # Check campaign momentum reduced by 1
        result = await test_session.execute(
            select(CampaignRecord).filter(CampaignRecord.id == campaign.id)
        )
        updated_campaign = result.scalars().first()
        assert updated_campaign.momentum == 4

    @pytest.mark.asyncio
    async def test_activate_starship_fails_if_campaign_no_active_ship(
        self, client, test_session, sample_campaign
    ):
        """Activation fails if campaign has no active ship."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.active_ship_id = None
        await test_session.commit()

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Starship Encounter",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 400
        data = response.json()
        assert "Campaign has no active ship assigned" in data["detail"]

    @pytest.mark.asyncio
    async def test_activate_starship_fails_if_no_ships_in_scene(
        self, client, test_session, sample_campaign
    ):
        """Activation fails if no ships added to scene."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        await test_session.commit()  # ensure active_ship exists

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Starship Encounter",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 400
        data = response.json()
        assert "must have at least one ship in scene" in data["detail"]

    @pytest.mark.asyncio
    async def test_activate_starship_fails_if_player_ship_not_in_scene(
        self, client, test_session, sample_campaign, sample_enemy_ship_data
    ):
        """Activation fails if campaign's active ship is not in scene_ships."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        player_ship_id = campaign.active_ship_id

        # Add only an enemy ship, not the player ship
        enemy_ship = StarshipRecord(**sample_enemy_ship_data)
        test_session.add(enemy_ship)
        await test_session.flush()

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Starship Encounter",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.flush()

        test_session.add(
            SceneShipRecord(
                scene_id=scene.id, ship_id=enemy_ship.id, is_visible_to_players=False
            )
        )
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 400
        data = response.json()
        assert "Player ship must be included in scene ships" in data["detail"]

    @pytest.mark.asyncio
    async def test_activate_personal_success(
        self, client, test_session, sample_campaign
    ):
        """Activating a personal scene creates PersonnelEncounterRecord with correct character states."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 3
        await test_session.commit()

        # Create a PC character assigned to a player
        pc_char = VTTCharacterRecord(
            campaign_id=campaign.id,
            name="PC Hero",
            character_type="main",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 10,
                    "fitness": 10,
                    "insight": 10,
                    "presence": 10,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 5,
                    "conn": 5,
                    "engineering": 5,
                    "medicine": 5,
                    "science": 5,
                    "security": 5,
                }
            ),
            talents_json=json.dumps([]),
            focuses_json=json.dumps([]),
            stress=4,
            stress_max=5,
            determination=2,
            determination_max=3,
        )
        test_session.add(pc_char)
        await test_session.flush()

        # Create an NPC character (no player)
        npc_char = VTTCharacterRecord(
            campaign_id=campaign.id,
            name="NPC Ally",
            character_type="npc",
            attributes_json=json.dumps(
                {
                    "control": 8,
                    "daring": 8,
                    "fitness": 8,
                    "insight": 8,
                    "presence": 8,
                    "reason": 8,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 3,
                    "science": 3,
                    "security": 3,
                }
            ),
            talents_json=json.dumps([]),
            focuses_json=json.dumps([]),
            stress=3,
            stress_max=5,
            determination=1,
            determination_max=3,
        )
        test_session.add(npc_char)
        await test_session.flush()

        # Create a draft personal scene
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Personal Encounter",
            scene_type="personal_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.flush()

        # Add participants: PC assigned to first player, NPC unassigned
        player = sample_campaign["players"][
            0
        ]  # GM is also a player; but we can assign any
        test_session.add(
            SceneParticipantRecord(
                scene_id=scene.id,
                character_id=pc_char.id,
                player_id=player.id,
                is_visible_to_players=False,
            )
        )
        test_session.add(
            SceneParticipantRecord(
                scene_id=scene.id,
                character_id=npc_char.id,
                player_id=None,
                is_visible_to_players=False,
            )
        )
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "active"
        assert "personnel_encounter_id" in data

        # Commit test session to see changes
        await test_session.commit()

        # Verify personnel encounter created
        pe_id = data["personnel_encounter_id"]
        result = await test_session.execute(
            select(PersonnelEncounterRecord).filter(
                PersonnelEncounterRecord.id == pe_id
            )
        )
        pe = result.scalars().first()
        assert pe is not None
        assert pe.scene_id == scene.id
        assert pe.is_active is True
        # Momentum should be campaign's momentum after reduction (3 -> 2)
        assert pe.momentum == 2
        assert pe.threat == campaign.threat  # unchanged

        # Verify character_states_json
        states = json.loads(pe.character_states_json)
        assert len(states) == 2
        # Find PC state
        pc_state = next(s for s in states if s["character_id"] == pc_char.id)
        assert pc_state["name"] == "PC Hero"
        assert pc_state["is_player"] is True
        assert pc_state["stress"] == 4
        assert pc_state["stress_max"] == 5
        assert pc_state["determination"] == 2
        assert pc_state["determination_max"] == 3
        assert pc_state["is_defeated"] is False
        assert pc_state["injuries"] == []
        assert pc_state["protection"] == 0
        # NPC state
        npc_state = next(s for s in states if s["character_id"] == npc_char.id)
        assert npc_state["name"] == "NPC Ally"
        assert npc_state["is_player"] is False

        # Verify campaign momentum reduced
        result = await test_session.execute(
            select(CampaignRecord).filter(CampaignRecord.id == campaign.id)
        )
        updated_campaign = result.scalars().first()
        assert updated_campaign.momentum == 2

    @pytest.mark.asyncio
    async def test_activate_personal_fails_if_no_participants(
        self, client, test_session, sample_campaign
    ):
        """Activation fails if personal scene has no participants."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Personal Encounter",
            scene_type="personal_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 400
        data = response.json()
        assert "must have at least one participant" in data["detail"]

    @pytest.mark.asyncio
    async def test_activate_narrative_success(
        self, client, test_session, sample_campaign
    ):
        """Activating a narrative scene just changes status to active; no encounter created."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 2
        await test_session.commit()

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Narrative Scene",
            scene_type="narrative",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "active"
        assert "encounter_id" not in data
        assert "personnel_encounter_id" not in data

        # Commit to expire session and see changes
        await test_session.commit()

        # Scene should be active, no encounter_id set
        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene_id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "active"
        assert updated_scene.encounter_id is None

        # Campaign momentum reduced
        result = await test_session.execute(
            select(CampaignRecord).filter(CampaignRecord.id == campaign.id)
        )
        updated_campaign = result.scalars().first()
        assert updated_campaign.momentum == 1

    @pytest.mark.asyncio
    async def test_activate_fails_if_not_draft(
        self, client, test_session, sample_campaign
    ):
        """Activation fails if scene is not in draft status."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Active Scene",
            scene_type="starship_encounter",
            status="active",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 400
        data = response.json()
        assert "must be in draft status" in data["detail"]

    @pytest.mark.asyncio
    async def test_activate_requires_gm_auth(
        self, client, test_session, sample_campaign
    ):
        """Activation requires GM authentication."""
        campaign = sample_campaign["campaign"]
        # No GM token set
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Starship Encounter",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        response = client.post(f"/scenes/{scene_id}/activate")
        assert response.status_code == 401
