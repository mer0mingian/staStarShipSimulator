"""Tests for scene management (Milestone 1)."""

import json
import pytest
from sta.database.schema import SceneRecord


class TestSceneRecord:
    """Tests for SceneRecord model."""

    def test_scene_record_creation(self, test_session, sample_campaign):
        """SceneRecord should be creatable with campaign_id."""
        campaign_id = sample_campaign["campaign"].id
        scene = SceneRecord(campaign_id=campaign_id, name="Test Scene")
        test_session.add(scene)
        test_session.flush()
        assert scene.id is not None
        assert scene.stardate is None
        assert scene.scene_picture_url is None
        assert scene.scene_type == "narrative"
        assert scene.status == "draft"

    def test_scene_traits_json_serialization(self, test_session, sample_campaign):
        """Scene traits should serialize to/from JSON."""
        campaign_id = sample_campaign["campaign"].id
        scene = SceneRecord(
            campaign_id=campaign_id, scene_traits_json='["Dark", "Dangerous"]'
        )
        test_session.add(scene)
        test_session.flush()
        traits = json.loads(scene.scene_traits_json)
        assert traits == ["Dark", "Dangerous"]

    def test_scene_challenges_json_structure(self, test_session, sample_campaign):
        """Challenges should support name, progress, resistance."""
        campaign_id = sample_campaign["campaign"].id
        challenges = [{"name": "Repair Warp Core", "progress": 2, "resistance": 5}]
        scene = SceneRecord(
            campaign_id=campaign_id, challenges_json=json.dumps(challenges)
        )
        test_session.add(scene)
        test_session.flush()
        loaded = json.loads(scene.challenges_json)
        assert loaded[0]["name"] == "Repair Warp Core"
        assert loaded[0]["progress"] == 2
        assert loaded[0]["resistance"] == 5

    def test_scene_types(self, test_session, sample_campaign):
        """Scene should support different types."""
        campaign_id = sample_campaign["campaign"].id

        narrative = SceneRecord(campaign_id=campaign_id, scene_type="narrative")
        starship = SceneRecord(campaign_id=campaign_id, scene_type="starship_encounter")
        personal = SceneRecord(campaign_id=campaign_id, scene_type="personal_encounter")
        social = SceneRecord(campaign_id=campaign_id, scene_type="social_encounter")

        test_session.add_all([narrative, starship, personal, social])
        test_session.flush()

        assert narrative.scene_type == "narrative"
        assert starship.scene_type == "starship_encounter"
        assert personal.scene_type == "personal_encounter"
        assert social.scene_type == "social_encounter"


class TestSceneAPI:
    """Tests for scene API endpoints."""

    def test_get_scene_returns_empty_when_not_found(self, client, sample_encounter):
        """GET /scene should return empty data when no scene exists."""
        encounter_id = sample_encounter["encounter"].encounter_id
        response = client.get(f"/api/encounter/{encounter_id}/scene")
        assert response.status_code == 200
        data = response.get_json()
        assert data["stardate"] is None
        assert data["scene_picture_url"] is None
        assert data["scene_traits"] == []
        assert data["challenges"] == []
        assert data["show_picture"] is False

    def test_post_scene_creates_new_scene(self, client, sample_encounter):
        """POST /scene should create a new scene record."""
        encounter_id = sample_encounter["encounter"].encounter_id
        response = client.post(
            f"/api/encounter/{encounter_id}/scene",
            json={
                "stardate": "47988.5",
                "scene_picture_url": "https://example.com/image.png",
                "scene_traits": ["Dark", "Foggy"],
                "show_picture": True,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["stardate"] == "47988.5"
        assert data["scene_picture_url"] == "https://example.com/image.png"
        assert "Dark" in data["scene_traits"]
        assert data["show_picture"] is True

    def test_post_scene_updates_existing(self, client, sample_encounter):
        """POST /scene should update an existing scene."""
        encounter_id = sample_encounter["encounter"].encounter_id

        # Create initial scene
        client.post(
            f"/api/encounter/{encounter_id}/scene", json={"stardate": "47988.0"}
        )

        # Update scene
        response = client.post(
            f"/api/encounter/{encounter_id}/scene", json={"stardate": "47989.0"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["stardate"] == "47989.0"

    def test_get_scene_returns_created_scene(self, client, sample_encounter):
        """GET /scene should return the created scene data."""
        encounter_id = sample_encounter["encounter"].encounter_id

        # Create scene
        client.post(
            f"/api/encounter/{encounter_id}/scene",
            json={"stardate": "47990.0", "scene_traits": ["Hostile"]},
        )

        # Get scene
        response = client.get(f"/api/encounter/{encounter_id}/scene")
        data = response.get_json()
        assert data["stardate"] == "47990.0"
        assert "Hostile" in data["scene_traits"]

    def test_scene_with_challenges(self, client, sample_encounter):
        """Scene should store and return challenges with progress."""
        encounter_id = sample_encounter["encounter"].encounter_id

        challenges = [
            {"name": "Repair Warp Core", "progress": 2, "resistance": 5},
            {"name": "Treat Wounded", "progress": 0, "resistance": 3},
        ]

        response = client.post(
            f"/api/encounter/{encounter_id}/scene", json={"challenges": challenges}
        )
        assert response.status_code == 200

        response = client.get(f"/api/encounter/{encounter_id}/scene")
        data = response.get_json()
        assert len(data["challenges"]) == 2
        assert data["challenges"][0]["name"] == "Repair Warp Core"
        assert data["challenges"][0]["progress"] == 2
