"""Tests for 4-state scene lifecycle (draft → ready → active → completed)."""

import json
import pytest
from sqlalchemy import select
from sta.database import (
    SceneRecord,
    CampaignRecord,
    EncounterRecord,
    PersonnelEncounterRecord,
)
from sta.database.schema import SceneShipRecord, SceneParticipantRecord


@pytest.mark.scene_lifecycle
class TestDraftToReady:
    """Tests for POST /api/scenes/{id}/transition-to-ready."""

    @pytest.mark.asyncio
    async def test_transition_to_ready_success(
        self, client, test_session, sample_campaign
    ):
        """Successfully transition from draft to ready with all requirements."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            scene_type="narrative",
            status="draft",
            gm_short_description="A test scene description",
            player_character_list=json.dumps([{"id": 1, "name": "PC Hero"}]),
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/transition-to-ready")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "ready"

        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene_id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "ready"

    @pytest.mark.asyncio
    async def test_transition_to_ready_requires_title(
        self, client, test_session, sample_campaign
    ):
        """Transition fails without a valid title (name)."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="New Scene",
            scene_type="narrative",
            status="draft",
            gm_short_description="A test scene description",
            player_character_list=json.dumps([{"id": 1, "name": "PC Hero"}]),
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/transition-to-ready")
        assert response.status_code == 400
        data = response.json()
        assert "name (title)" in data["detail"]

    @pytest.mark.asyncio
    async def test_transition_to_ready_requires_description(
        self, client, test_session, sample_campaign
    ):
        """Transition fails without gm_short_description."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            scene_type="narrative",
            status="draft",
            gm_short_description=None,
            player_character_list=json.dumps([{"id": 1, "name": "PC Hero"}]),
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/transition-to-ready")
        assert response.status_code == 400
        data = response.json()
        assert "GM short description" in data["detail"]

    @pytest.mark.asyncio
    async def test_transition_to_ready_requires_player_characters(
        self, client, test_session, sample_campaign
    ):
        """Transition fails without player_character_list."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            scene_type="narrative",
            status="draft",
            gm_short_description="A test scene description",
            player_character_list=None,
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/transition-to-ready")
        assert response.status_code == 400
        data = response.json()
        assert "player character" in data["detail"]

    @pytest.mark.asyncio
    async def test_transition_to_ready_from_ready_fails(
        self, client, test_session, sample_campaign
    ):
        """Cannot transition a scene that's already ready."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            scene_type="narrative",
            status="ready",
            gm_short_description="A test scene description",
            player_character_list=json.dumps([{"id": 1, "name": "PC Hero"}]),
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/transition-to-ready")
        assert response.status_code == 400
        data = response.json()
        assert "draft" in data["detail"]


@pytest.mark.scene_lifecycle
class TestReadyToActive:
    """Tests for POST /api/scenes/{id}/activate."""

    @pytest.mark.asyncio
    async def test_activate_from_ready_success(
        self, client, test_session, sample_campaign
    ):
        """Successfully activate a ready scene."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            scene_type="narrative",
            status="ready",
            gm_short_description="A test scene description",
            player_character_list=json.dumps([{"id": 1, "name": "PC Hero"}]),
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

    @pytest.mark.asyncio
    async def test_activate_from_draft_allowed(
        self, client, test_session, sample_campaign
    ):
        """Can activate a draft scene directly (also allowed per implementation)."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
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

    @pytest.mark.asyncio
    async def test_multiple_active_scenes(self, client, test_session, sample_campaign):
        """Multiple scenes can be active simultaneously (split-party support)."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 5
        await test_session.commit()

        scene1 = SceneRecord(
            campaign_id=campaign.id,
            name="Scene 1",
            scene_type="narrative",
            status="ready",
            gm_short_description="First scene",
            player_character_list=json.dumps([{"id": 1, "name": "PC1"}]),
        )
        scene2 = SceneRecord(
            campaign_id=campaign.id,
            name="Scene 2",
            scene_type="narrative",
            status="ready",
            gm_short_description="Second scene",
            player_character_list=json.dumps([{"id": 2, "name": "PC2"}]),
        )
        test_session.add(scene1)
        test_session.add(scene2)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)

        response1 = client.post(f"/scenes/{scene1.id}/activate")
        assert response1.status_code == 200

        response2 = client.post(f"/scenes/{scene2.id}/activate")
        assert response2.status_code == 200

        await test_session.commit()

        result1 = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene1.id)
        )
        result2 = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene2.id)
        )
        assert result1.scalars().first().status == "active"
        assert result2.scalars().first().status == "active"


@pytest.mark.scene_lifecycle
class TestActiveToCompleted:
    """Tests for POST /api/scenes/{id}/end."""

    @pytest.mark.asyncio
    async def test_complete_scene_success(self, client, test_session, sample_campaign):
        """Successfully complete an active scene."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 3
        await test_session.commit()

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene_id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "completed"

    @pytest.mark.asyncio
    async def test_complete_terminates_connections(
        self, client, test_session, sample_campaign
    ):
        """Completing a scene should set status to completed."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene1 = SceneRecord(
            campaign_id=campaign.id,
            name="Active Scene",
            scene_type="narrative",
            status="active",
            next_scene_ids_json=json.dumps([1, 2]),
        )
        scene2 = SceneRecord(
            campaign_id=campaign.id,
            name="Next Scene 1",
            scene_type="narrative",
            status="draft",
        )
        scene3 = SceneRecord(
            campaign_id=campaign.id,
            name="Next Scene 2",
            scene_type="narrative",
            status="draft",
        )
        test_session.add(scene1)
        test_session.add(scene2)
        test_session.add(scene3)
        await test_session.flush()

        scene1.next_scene_ids_json = json.dumps([scene2.id, scene3.id])
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene1.id}/end")
        assert response.status_code == 200

        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene1.id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "completed"


@pytest.mark.scene_lifecycle
class TestReactivation:
    """Tests for POST /api/scenes/{id}/reactivate and /api/scenes/{id}/copy."""

    @pytest.mark.asyncio
    async def test_reactivate_completed_scene(
        self, client, test_session, sample_campaign
    ):
        """Successfully reactivate a completed scene (completed → ready → active)."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Completed Scene",
            scene_type="narrative",
            status="completed",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/reactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "active"

        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene_id)
        )
        updated_scene = result.scalars().first()
        assert updated_scene.status == "active"

    @pytest.mark.asyncio
    async def test_reactivate_non_completed_fails(
        self, client, test_session, sample_campaign
    ):
        """Cannot reactivate a scene that's not completed."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Ready Scene",
            scene_type="narrative",
            status="ready",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/reactivate")
        assert response.status_code == 400
        data = response.json()
        assert "completed" in data["detail"]

    @pytest.mark.asyncio
    async def test_copy_scene_as_new(self, client, test_session, sample_campaign):
        """Successfully copy a completed scene as a new ready scene."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Original Scene",
            scene_type="narrative",
            status="completed",
            gm_short_description="Original description",
            player_character_list=json.dumps([{"id": 1, "name": "PC Hero"}]),
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/copy")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "ready"
        assert "Copy" in data["name"]

        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == data["scene_id"])
        )
        new_scene = result.scalars().first()
        assert new_scene.status == "ready"
        assert new_scene.name == "Original Scene (Copy)"

    @pytest.mark.asyncio
    async def test_copy_non_completed_fails(
        self, client, test_session, sample_campaign
    ):
        """Cannot copy a scene that's not completed."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Active Scene",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/copy")
        assert response.status_code == 400
        data = response.json()
        assert "completed" in data["detail"]


@pytest.mark.scene_lifecycle
class TestTransitionDialogue:
    """Tests for GET /campaigns/api/campaign/{id}/scenes/transition-options."""

    @pytest.mark.asyncio
    async def test_get_transition_options(self, client, test_session, sample_campaign):
        """Returns connected scenes (draft) and ready scenes."""
        campaign = sample_campaign["campaign"]
        campaign_id = campaign.campaign_id
        gm_token = sample_campaign["players"][0].session_token

        draft_scene = SceneRecord(
            campaign_id=campaign.id,
            name="Draft Scene",
            scene_type="narrative",
            status="draft",
        )
        ready_scene = SceneRecord(
            campaign_id=campaign.id,
            name="Ready Scene",
            scene_type="narrative",
            status="ready",
            gm_short_description="Ready description",
        )
        test_session.add(draft_scene)
        test_session.add(ready_scene)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.get(
            f"/campaigns/api/campaign/{campaign_id}/scenes/transition-options"
        )
        assert response.status_code == 200
        data = response.json()
        assert "connected_scenes" in data
        assert "ready_scenes" in data
        assert "can_create_new" in data

    @pytest.mark.asyncio
    async def test_connected_scenes_are_draft(
        self, client, test_session, sample_campaign
    ):
        """Connected scenes should be those in draft status."""
        campaign = sample_campaign["campaign"]
        campaign_id = campaign.campaign_id
        gm_token = sample_campaign["players"][0].session_token

        draft_scene = SceneRecord(
            campaign_id=campaign.id,
            name="Draft Scene",
            scene_type="narrative",
            status="draft",
        )
        test_session.add(draft_scene)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.get(
            f"/campaigns/api/campaign/{campaign_id}/scenes/transition-options"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["connected_scenes"]) == 1
        assert data["connected_scenes"][0]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_ready_scenes_in_transition_options(
        self, client, test_session, sample_campaign
    ):
        """Ready scenes should be returned in transition options."""
        campaign = sample_campaign["campaign"]
        campaign_id = campaign.campaign_id
        gm_token = sample_campaign["players"][0].session_token

        ready_scene = SceneRecord(
            campaign_id=campaign.id,
            name="Ready Scene",
            scene_type="narrative",
            status="ready",
            gm_short_description="Ready description",
        )
        test_session.add(ready_scene)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.get(
            f"/campaigns/api/campaign/{campaign_id}/scenes/transition-options"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["ready_scenes"]) == 1
        assert data["ready_scenes"][0]["gm_short_description"] == "Ready description"

    @pytest.mark.asyncio
    async def test_transition_options_requires_gm_auth(
        self, client, test_session, sample_campaign
    ):
        """Transition options endpoint requires GM authentication."""
        campaign = sample_campaign["campaign"]
        campaign_id = campaign.campaign_id

        response = client.get(
            f"/campaigns/api/campaign/{campaign_id}/scenes/transition-options"
        )
        assert response.status_code == 401
