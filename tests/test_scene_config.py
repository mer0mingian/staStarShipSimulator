"""Tests for scene configuration endpoints (M3 Task 3.4)."""

import json
import pytest
from sta.database import SceneRecord


class TestSceneConfigAPI:
    """Tests for GET and PUT /api/scenes/<id>/config."""

    @pytest.mark.asyncio
    async def test_get_config_empty(self, client, test_session, sample_campaign):
        """GET returns empty dict when no config set."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Config Test Scene",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        response = client.get(f"/scenes/{scene_id}/config")
        assert response.status_code == 200
        data = response.json()
        assert data == {}

    @pytest.mark.asyncio
    async def test_put_config_valid(self, client, test_session, sample_campaign):
        """PUT with valid config updates scene's encounter_config_json."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Config Test Scene",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        config_data = {"npc_turn_mode": "all_npcs", "gm_spends_threat_to_start": False}
        response = client.put(f"/scenes/{scene_id}/config", json=config_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify via GET
        response = client.get(f"/scenes/{scene_id}/config")
        assert response.status_code == 200
        data = response.json()
        assert data == config_data

    @pytest.mark.asyncio
    async def test_put_config_unknown_key(self, client, test_session, sample_campaign):
        """PUT with unknown key returns error."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Config Test Scene",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        config_data = {"invalid_key": "value"}
        response = client.put(f"/scenes/{scene_id}/config", json=config_data)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid config keys" in data["detail"]

    @pytest.mark.asyncio
    async def test_put_config_invalid_npc_turn_mode(
        self, client, test_session, sample_campaign
    ):
        """PUT with invalid npc_turn_mode returns error."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Config Test Scene",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        config_data = {"npc_turn_mode": "invalid"}
        response = client.put(f"/scenes/{scene_id}/config", json=config_data)
        assert response.status_code == 400
        data = response.json()
        assert "Invalid npc_turn_mode" in data["detail"]

    @pytest.mark.asyncio
    async def test_put_config_gm_spends_threat_to_start_not_bool(
        self, client, test_session, sample_campaign
    ):
        """gm_spends_threat_to_start must be boolean."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Config Test Scene",
            scene_type="personal_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        client.cookies.set("sta_session_token", gm_token)
        config_data = {"gm_spends_threat_to_start": "yes"}  # not bool
        response = client.put(f"/scenes/{scene_id}/config", json=config_data)
        assert response.status_code == 400
        data = response.json()
        assert "must be a boolean" in data["detail"]

    @pytest.mark.asyncio
    async def test_config_requires_gm_auth(self, client, test_session, sample_campaign):
        """GET and PUT require GM auth."""
        campaign = sample_campaign["campaign"]
        # No GM token set
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Config Test Scene",
            scene_type="starship_encounter",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()
        scene_id = scene.id

        # GET without auth
        response = client.get(f"/scenes/{scene_id}/config")
        assert response.status_code == 401

        # PUT without auth
        response = client.put(
            f"/scenes/{scene_id}/config", json={"npc_turn_mode": "all_npcs"}
        )
        assert response.status_code == 401
