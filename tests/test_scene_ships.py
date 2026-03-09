"""Tests for scene ship management (M3 Task 3.3)."""

import json
import pytest
from sta.database import (
    get_session,
    SceneRecord,
    CampaignPlayerRecord,
    VTTShipRecord,
    CampaignShipRecord,
)
from sta.database.schema import SceneShipRecord


class TestSceneShipsAPI:
    """Tests for ship endpoints."""

    @pytest.fixture
    def setup_scene_with_ship(self, test_session, sample_campaign):
        """Create a scene and campaign ship."""
        campaign_id = sample_campaign["campaign"].campaign_id

        # Create a scene
        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Test Space Battle",
            scene_type="starship_encounter",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        # Create a ship and add to campaign_ships
        ship = VTTShipRecord(
            campaign_id=campaign_id,
            name="Frigate",
            ship_class="Frigate",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 10,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 10,
                    "structure": 10,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
            weapons_json=json.dumps([]),
            talents_json=json.dumps([]),
            traits_json=json.dumps([]),
            breaches_json=json.dumps([]),
            shields=10,
            shields_max=10,
            resistance=5,
        )
        test_session.add(ship)
        test_session.flush()

        # Link ship to campaign
        campaign_ship = CampaignShipRecord(campaign_id=campaign_id, ship_id=ship.id)
        test_session.add(campaign_ship)
        test_session.commit()

        gm = sample_campaign["players"][0]  # first player is GM

        return {
            "campaign": sample_campaign["campaign"],
            "gm": gm,
            "scene": scene,
            "ship": ship,
        }

    def test_get_ships_empty(self, client, setup_scene_with_ship):
        """GET ships returns empty list when no ships assigned."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        response = client.get(f"/scenes/{scene_id}/ships")
        assert response.status_code == 200
        result = response.get_json()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_add_ship(self, client, setup_scene_with_ship):
        """POST ships adds a ship to scene."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        ship_id = data["ship"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        payload = {
            "ship_id": ship_id,
            "is_visible_to_players": True,
        }
        response = client.post(f"/scenes/{scene_id}/ships", json=payload)
        assert response.status_code == 200
        assert response.get_json()["success"] is True

        # Verify via GET
        get_resp = client.get(f"/scenes/{scene_id}/ships")
        assert get_resp.status_code == 200
        ships = get_resp.get_json()
        assert len(ships) == 1
        s = ships[0]
        assert s["ship_id"] == ship_id
        assert s["name"] == "Frigate"
        assert s["is_visible_to_players"] is True

    def test_add_ship_requires_ship_id(self, client, setup_scene_with_ship):
        """POST ships requires ship_id."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        response = client.post(f"/scenes/{scene_id}/ships", json={})
        assert response.status_code == 400
        assert "ship_id required" in response.get_json()["error"]

    def test_add_ship_not_found(self, client, setup_scene_with_ship):
        """POST ships fails if ship does not exist."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        response = client.post(f"/scenes/{scene_id}/ships", json={"ship_id": 999})
        assert response.status_code == 404
        assert "Ship not found" in response.get_json()["error"]

    def test_add_ship_not_in_campaign(self, client, setup_scene_with_ship):
        """POST ships fails if ship not in campaign_ships."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        # Create a ship not linked to campaign
        other_ship = VTTShipRecord(
            campaign_id=data["campaign"].campaign_id,
            name="Orphan Ship",
            ship_class="Shuttle",
            scale=2,
            systems_json=json.dumps(
                {
                    "comms": 5,
                    "computers": 5,
                    "engines": 5,
                    "sensors": 5,
                    "structure": 5,
                    "weapons": 5,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 1,
                    "conn": 1,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 1,
                    "security": 1,
                }
            ),
            weapons_json=json.dumps([]),
            talents_json=json.dumps([]),
            traits_json=json.dumps([]),
            breaches_json=json.dumps([]),
            shields=0,
            shields_max=0,
            resistance=0,
        )
        test_session = get_session()
        test_session.add(other_ship)
        test_session.commit()
        orphan_ship_id = other_ship.id

        response = client.post(
            f"/scenes/{scene_id}/ships", json={"ship_id": orphan_ship_id}
        )
        assert response.status_code == 400
        assert "Ship not in campaign" in response.get_json()["error"]

    def test_add_ship_duplicate(self, client, setup_scene_with_ship):
        """POST ships fails if ship already in scene."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        ship_id = data["ship"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        # Add ship
        resp1 = client.post(f"/scenes/{scene_id}/ships", json={"ship_id": ship_id})
        assert resp1.status_code == 200

        # Try to add same ship again
        resp2 = client.post(f"/scenes/{scene_id}/ships", json={"ship_id": ship_id})
        assert resp2.status_code == 400
        assert "already in scene" in resp2.get_json()["error"].lower()

    def test_update_ship_visibility(self, client, setup_scene_with_ship):
        """PUT ship toggles visibility."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        ship_id = data["ship"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        # Add ship first
        resp = client.post(
            f"/scenes/{scene_id}/ships",
            json={"ship_id": ship_id, "is_visible_to_players": False},
        )
        assert resp.status_code == 200

        # Update visibility
        update_resp = client.put(
            f"/scenes/{scene_id}/ships/{ship_id}", json={"is_visible_to_players": True}
        )
        assert update_resp.status_code == 200
        assert update_resp.get_json()["success"] is True

        # Verify via GET
        get_resp = client.get(f"/scenes/{scene_id}/ships")
        ships = get_resp.get_json()
        assert ships[0]["is_visible_to_players"] is True

    def test_update_ship_not_found(self, client, setup_scene_with_ship):
        """PUT ship fails if not in scene."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        ship_id = data["ship"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        response = client.put(
            f"/scenes/{scene_id}/ships/{ship_id}", json={"is_visible_to_players": True}
        )
        assert response.status_code == 404
        assert "Ship not found in scene" in response.get_json()["error"]

    def test_delete_ship(self, client, setup_scene_with_ship):
        """DELETE ship removes it from scene."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        ship_id = data["ship"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        # Add ship
        resp = client.post(f"/scenes/{scene_id}/ships", json={"ship_id": ship_id})
        assert resp.status_code == 200

        # Delete
        del_resp = client.delete(f"/scenes/{scene_id}/ships/{ship_id}")
        assert del_resp.status_code == 200
        assert del_resp.get_json()["success"] is True

        # Verify removed
        get_resp = client.get(f"/scenes/{scene_id}/ships")
        assert len(get_resp.get_json()) == 0

    def test_delete_ship_not_found(self, client, setup_scene_with_ship):
        """DELETE ship fails if not in scene."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        ship_id = data["ship"].id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        response = client.delete(f"/scenes/{scene_id}/ships/{ship_id}")
        assert response.status_code == 404
        assert "Ship not found in scene" in response.get_json()["error"]

    def test_authentication_required(self, client, setup_scene_with_ship):
        """All ship endpoints require GM auth."""
        data = setup_scene_with_ship
        scene_id = data["scene"].id
        ship_id = data["ship"].id

        # Not logged in
        response = client.get(f"/scenes/{scene_id}/ships")
        assert response.status_code == 401

        response = client.post(f"/scenes/{scene_id}/ships", json={"ship_id": ship_id})
        assert response.status_code == 401

        # Add as GM first for update/delete tests
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)
        client.post(f"/scenes/{scene_id}/ships", json={"ship_id": ship_id})
        client.delete_cookie("sta_session_token")

        response = client.put(
            f"/scenes/{scene_id}/ships/{ship_id}", json={"is_visible_to_players": True}
        )
        assert response.status_code == 401

        response = client.delete(f"/scenes/{scene_id}/ships/{ship_id}")
        assert response.status_code == 401

    def test_scene_not_found(self, client, setup_scene_with_ship):
        """Ship endpoints return 404 for non-existent scene."""
        gm_token = setup_scene_with_ship["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        response = client.get("/scenes/999/ships")
        assert response.status_code == 404

        response = client.post("/scenes/999/ships", json={"ship_id": 1})
        assert response.status_code == 404

        response = client.put("/scenes/999/ships/1", json={})
        assert response.status_code == 404

        response = client.delete("/scenes/999/ships/1")
        assert response.status_code == 404


class TestAvailableShipsHelper:
    """Tests for /api/campaigns/<id>/ships/available endpoint."""

    @pytest.fixture
    def setup_campaign_ships(self, test_session, sample_campaign):
        """Create multiple ships in campaign."""
        campaign_id = sample_campaign["campaign"].id

        ship1 = VTTShipRecord(
            campaign_id=campaign_id,
            name="Destroyer",
            ship_class="Destroyer",
            scale=3,
            systems_json=json.dumps(
                {
                    "comms": 8,
                    "computers": 8,
                    "engines": 8,
                    "sensors": 8,
                    "structure": 8,
                    "weapons": 8,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 2,
                    "conn": 2,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 2,
                    "security": 2,
                }
            ),
            weapons_json=json.dumps([]),
            talents_json=json.dumps([]),
            traits_json=json.dumps([]),
            breaches_json=json.dumps([]),
            shields=8,
            shields_max=8,
            resistance=4,
        )
        test_session.add(ship1)
        test_session.flush()

        ship2 = VTTShipRecord(
            campaign_id=campaign_id,
            name="Cruiser",
            ship_class="Cruiser",
            scale=5,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 9,
                    "engines": 9,
                    "sensors": 9,
                    "structure": 9,
                    "weapons": 9,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
            weapons_json=json.dumps([]),
            talents_json=json.dumps([]),
            traits_json=json.dumps([]),
            breaches_json=json.dumps([]),
            shields=12,
            shields_max=12,
            resistance=6,
        )
        test_session.add(ship2)
        test_session.flush()

        # Add to campaign_ships
        cs1 = CampaignShipRecord(campaign_id=campaign_id, ship_id=ship1.id)
        cs2 = CampaignShipRecord(campaign_id=campaign_id, ship_id=ship2.id)
        test_session.add_all([cs1, cs2])

        test_session.commit()

        gm = sample_campaign["players"][0]

        return {
            "campaign": sample_campaign["campaign"],
            "gm": gm,
            "ship1": ship1,
            "ship2": ship2,
        }

    def test_available_ships_requires_auth(self, client, setup_campaign_ships):
        """Unauthenticated cannot access available ships."""
        data = setup_campaign_ships
        campaign_id = data["campaign"].campaign_id

        response = client.get(f"/campaigns/{campaign_id}/ships/available")
        assert response.status_code == 401

    def test_available_ships_returns_list(self, client, setup_campaign_ships):
        """GM gets list of ships in campaign."""
        data = setup_campaign_ships
        campaign_id = data["campaign"].campaign_id
        gm_token = data["gm"].session_token
        client.set_cookie("sta_session_token", gm_token)

        response = client.get(f"/campaigns/{campaign_id}/ships/available")
        assert response.status_code == 200
        ships = response.get_json()
        assert len(ships) == 2
        names = {s["name"] for s in ships}
        assert "Destroyer" in names
        assert "Cruiser" in names
        # Ensure fields
        for s in ships:
            assert "id" in s
            assert "name" in s
