"""Tests for scene termination endpoint (M3 Task 3.4)."""

import json
import uuid
import pytest
from sqlalchemy import select
from sta.database import (
    SceneRecord,
    CampaignRecord,
    EncounterRecord,
    PersonnelEncounterRecord,
)


class TestSceneTerminationAPI:
    """Tests for POST /api/scenes/<id>/end."""

    async def _create_active_starship_scene(self, test_session, sample_campaign):
        """Helper to create an active starship scene with encounter."""
        campaign = sample_campaign["campaign"]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Starship Scene",
            scene_type="starship_encounter",
            status="active",
        )
        test_session.add(scene)
        await test_session.flush()

        encounter = EncounterRecord(
            encounter_id=str(uuid.uuid4()),
            name="Test Encounter",
            campaign_id=campaign.id,
            player_ship_id=campaign.active_ship_id,
            player_position="captain",
            enemy_ship_ids_json=json.dumps([]),
            is_active=True,
        )
        test_session.add(encounter)
        await test_session.flush()
        scene.encounter_id = encounter.id
        await test_session.commit()
        return scene, encounter

    async def _create_active_personal_scene(self, test_session, sample_campaign):
        """Helper to create an active personal scene with personnel encounter."""
        campaign = sample_campaign["campaign"]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Personal Scene",
            scene_type="personal_encounter",
            status="active",
        )
        test_session.add(scene)
        await test_session.flush()

        pe = PersonnelEncounterRecord(
            scene_id=scene.id,
            momentum=campaign.momentum,
            threat=campaign.threat,
            is_active=True,
        )
        test_session.add(pe)
        await test_session.commit()
        return scene, pe

    @pytest.mark.asyncio
    async def test_end_starship_reduces_momentum_and_deactivates(
        self, client, test_session, sample_campaign
    ):
        """Ending a starship scene reduces momentum by 1 (min 0) and deactivates encounter."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 3
        await test_session.commit()

        scene, encounter = self._create_active_starship_scene(
            test_session, sample_campaign
        )
        scene_id = scene.id
        encounter_id = encounter.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["momentum_remaining"] == 2
        assert "closing_options" in data

        # Commit test session to see changes
        await test_session.commit()

        # Verify scene completed
        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene_id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "completed"

        # Verify encounter deactivated
        result = await test_session.execute(
            select(EncounterRecord).filter(EncounterRecord.id == encounter_id)
        )
        updated_encounter = result.scalars().first()
        assert updated_encounter.is_active is False

        # Verify campaign momentum reduced
        result = await test_session.execute(
            select(CampaignRecord).filter(CampaignRecord.id == campaign.id)
        )
        updated_campaign = result.scalars().first()
        assert updated_campaign.momentum == 2

    @pytest.mark.asyncio
    async def test_end_personal_reduces_momentum_and_deactivates(
        self, client, test_session, sample_campaign
    ):
        """Ending a personal scene reduces momentum and deactivates personnel encounter."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 2
        await test_session.commit()

        scene, pe = self._create_active_personal_scene(test_session, sample_campaign)
        scene_id = scene.id
        pe_id = pe.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["momentum_remaining"] == 1

        # Commit test session to see changes
        await test_session.commit()

        # Verify personnel encounter deactivated
        result = await test_session.execute(
            select(PersonnelEncounterRecord).filter(
                PersonnelEncounterRecord.id == pe_id
            )
        )
        updated_pe = result.scalars().first()
        assert updated_pe.is_active is False

        # Verify scene completed
        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene_id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "completed"

    @pytest.mark.asyncio
    async def test_end_caps_momentum_at_6_before_reduction(
        self, client, test_session, sample_campaign
    ):
        """If campaign momentum > 6, cap at 6 before reducing."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 8
        await test_session.commit()

        scene, encounter = self._create_active_starship_scene(
            test_session, sample_campaign
        )
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 200
        data = response.json()
        # Expected: cap at 6 -> 6-1 = 5
        assert data["momentum_remaining"] == 5

    @pytest.mark.asyncio
    async def test_end_fails_if_not_active(self, client, test_session, sample_campaign):
        """Cannot end a scene that is not active."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Draft Scene",
            scene_type="narrative",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 400
        data = response.json()
        assert "must be active" in data["detail"]

    @pytest.mark.asyncio
    async def test_end_requires_gm_auth(self, client, test_session, sample_campaign):
        """End requires GM auth."""
        campaign = sample_campaign["campaign"]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Active Scene",
            scene_type="starship_encounter",
            status="active",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 401
