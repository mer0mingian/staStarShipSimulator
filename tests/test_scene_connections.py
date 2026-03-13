"""Tests for scene connection management (M3 Task 3.2)."""

import json
import pytest
from sta.database import SceneRecord


class TestSceneConnectionsAPI:
    """Test scene connections API endpoints."""

    @pytest.fixture
    async def setup_scene_with_data(self, test_session, sample_campaign):
        """Create a scene with data for testing."""
        campaign = sample_campaign["campaign"]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        await test_session.commit()  # Commit to make scene visible to other sessions
        await test_session.flush()

        gm_player = None
        for player in sample_campaign["players"]:
            if player.is_gm:
                gm_player = player
                break

        return {
            "session": test_session,
            "scene": scene,
            "scene_id": scene.id,
            "campaign": campaign,
            "campaign_id": campaign.campaign_id,
            "gm_player": gm_player,
        }

    @pytest.mark.asyncio
    async def test_get_connections_empty(self, client, setup_scene_with_data):
        """GET connections returns empty arrays when no connections exist."""
        scene_id = setup_scene_with_data["scene_id"]
        gm_token = setup_scene_with_data["gm_player"].session_token
        client.cookies.set("sta_session_token", gm_token)

        response = client.get(f"/scenes/{scene_id}/connections")

        assert response.status_code == 200
        data = response.json()
        assert data["previous_scene_ids"] == []
        assert data["next_scene_ids"] == []

    @pytest.mark.asyncio
    async def test_get_connections_with_data(self, client, setup_scene_with_data):
        """GET connections returns existing connections."""
        session = setup_scene_with_data["session"]
        scene = setup_scene_with_data["scene"]
        campaign = setup_scene_with_data["campaign"]
        scene_id = setup_scene_with_data["scene_id"]
        gm_token = setup_scene_with_data["gm_player"].session_token
        client.cookies.set("sta_session_token", gm_token)

        prev_scene = SceneRecord(
            campaign_id=campaign.id, name="Previous Scene", status="completed"
        )
        session.add(prev_scene)
        session.flush()

        next_scene = SceneRecord(
            campaign_id=campaign.id, name="Next Scene", status="draft"
        )
        session.add(next_scene)
        session.flush()

        scene.previous_scene_ids_json = json.dumps([prev_scene.id])
        scene.next_scene_ids_json = json.dumps([next_scene.id])
        session.commit()

        response = client.get(f"/scenes/{scene_id}/connections")

        assert response.status_code == 200
        data = response.json()
        assert prev_scene.id in data["previous_scene_ids"]
        assert next_scene.id in data["next_scene_ids"]

    @pytest.mark.asyncio
    async def test_get_connections_nonexistent_scene(self, client):
        """GET connections returns 404 for nonexistent scene."""
        response = client.get("/scenes/99999/connections")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_connections_add_next(self, client, setup_scene_with_data):
        """PUT connections can add a next scene connection."""
        session = setup_scene_with_data["session"]
        scene = setup_scene_with_data["scene"]
        campaign = setup_scene_with_data["campaign"]
        scene_id = setup_scene_with_data["scene_id"]
        gm_token = setup_scene_with_data["gm_player"].session_token
        client.cookies.set("sta_session_token", gm_token)

        next_scene = SceneRecord(
            campaign_id=campaign.id, name="Next Scene", status="draft"
        )
        session.add(next_scene)
        session.flush()

        response = client.put(
            f"/scenes/{scene_id}/connections",
            json={"next_scene_ids": [next_scene.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert next_scene.id in data["next_scene_ids"]

        session.expire(scene)
        scene = session.query(SceneRecord).filter_by(id=scene.id).first()
        assert next_scene.id in json.loads(scene.next_scene_ids_json)

    @pytest.mark.asyncio
    async def test_update_connections_add_previous(self, client, setup_scene_with_data):
        """PUT connections can add a previous scene connection."""
        session = setup_scene_with_data["session"]
        scene = setup_scene_with_data["scene"]
        campaign = setup_scene_with_data["campaign"]
        scene_id = setup_scene_with_data["scene_id"]
        gm_token = setup_scene_with_data["gm_player"].session_token
        client.cookies.set("sta_session_token", gm_token)

        prev_scene = SceneRecord(
            campaign_id=campaign.id, name="Previous Scene", status="completed"
        )
        session.add(prev_scene)
        session.flush()

        response = client.put(
            f"/scenes/{scene_id}/connections",
            json={"previous_scene_ids": [prev_scene.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert prev_scene.id in data["previous_scene_ids"]

    @pytest.mark.asyncio
    async def test_update_connections_remove(self, client, setup_scene_with_data):
        """PUT connections can remove connections by passing empty arrays."""
        session = setup_scene_with_data["session"]
        scene = setup_scene_with_data["scene"]
        campaign = setup_scene_with_data["campaign"]
        scene_id = setup_scene_with_data["scene_id"]
        gm_token = setup_scene_with_data["gm_player"].session_token
        client.cookies.set("sta_session_token", gm_token)

        next_scene = SceneRecord(
            campaign_id=campaign.id, name="Next Scene", status="draft"
        )
        session.add(next_scene)
        session.flush()

        scene.next_scene_ids_json = json.dumps([next_scene.id])
        session.commit()

        response = client.put(
            f"/scenes/{scene_id}/connections",
            json={"next_scene_ids": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["next_scene_ids"] == []

    @pytest.mark.asyncio
    async def test_update_connections_nonexistent_scene(self, client):
        """PUT connections returns 404 for nonexistent scene."""
        response = client.put("/scenes/99999/connections", json={"next_scene_ids": [1]})

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_connections_invalid_scene_id(self, client, setup_scene_with_data):
        """PUT connections ignores invalid scene IDs in the arrays."""
        scene_id = setup_scene_with_data["scene_id"]
        gm_token = setup_scene_with_data["gm_player"].session_token
        client.cookies.set("sta_session_token", gm_token)

        response = client.put(
            f"/scenes/{scene_id}/connections",
            json={"next_scene_ids": [99999, 88888]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["next_scene_ids"] == []

    @pytest.mark.asyncio
    async def test_connections_without_gm_token(self, client, setup_scene_with_data):
        """Connections endpoints return error without valid GM session token."""
        scene_id = setup_scene_with_data["scene_id"]

        response = client.get(f"/scenes/{scene_id}/connections")
        assert response.status_code in (401, 404)

        response = client.put(
            f"/scenes/{scene_id}/connections", json={"next_scene_ids": []}
        )
        assert response.status_code in (401, 404)