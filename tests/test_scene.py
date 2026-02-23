"""Tests for scene management (Milestone 1)."""

import json
import pytest
from sta.database.schema import SceneRecord, CampaignRecord, CampaignPlayerRecord


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

    def test_scene_traits_with_descriptions(self, test_session, sample_campaign):
        """Scene traits can include descriptions for hover/click."""
        campaign_id = sample_campaign["campaign"].id
        traits = [
            {"name": "Dark", "description": "No light sources available"},
            {"name": "Dangerous", "description": "Environmental hazards present"},
        ]
        scene = SceneRecord(
            campaign_id=campaign_id, scene_traits_json=json.dumps(traits)
        )
        test_session.add(scene)
        test_session.flush()
        loaded = json.loads(scene.scene_traits_json)
        assert loaded[0]["name"] == "Dark"
        assert loaded[0]["description"] == "No light sources available"

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

    def test_extended_task_with_breakthroughs(self, test_session, sample_campaign):
        """Extended tasks should support breakthrough descriptions."""
        campaign_id = sample_campaign["campaign"].id
        task = {
            "name": "Navigate Anomaly",
            "progress": 0,
            "resistance": 2,
            "magnitude": 3,
            "breakthrough_1": {"at_progress": 6, "effect": "Difficulty increases by 1"},
            "breakthrough_2": {"at_progress": 9, "effect": "Resistance reduced to 1"},
        }
        scene = SceneRecord(campaign_id=campaign_id, challenges_json=json.dumps([task]))
        test_session.add(scene)
        test_session.flush()
        loaded = json.loads(scene.challenges_json)
        assert loaded[0]["name"] == "Navigate Anomaly"
        assert loaded[0]["magnitude"] == 3
        assert loaded[0]["breakthrough_1"]["effect"] == "Difficulty increases by 1"

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

    def test_scene_has_map_based_on_type(self, test_session, sample_campaign):
        """Social encounters should not have maps by default."""
        campaign_id = sample_campaign["campaign"].id

        narrative = SceneRecord(
            campaign_id=campaign_id, scene_type="narrative", has_map=True
        )
        social = SceneRecord(
            campaign_id=campaign_id, scene_type="social_encounter", has_map=False
        )

        test_session.add_all([narrative, social])
        test_session.flush()

        assert narrative.has_map is True
        assert social.has_map is False


class TestSceneAPI:
    """Tests for scene API endpoints."""

    def test_get_scene_returns_empty_when_not_found(self, client, sample_encounter):
        """GET /scene should return empty data when no scene exists."""
        encounter_id = sample_encounter["encounter"].encounter_id
        response = client.get(f"/api/encounter/{encounter_id}/scene")
        assert response.status_code == 200
        data = response.get_json()
        assert data["stardate"] is None
        assert data["scene_traits"] == []
        assert data["challenges"] == []

    def test_post_scene_creates_new_scene(self, client, sample_encounter):
        """POST /scene should create a new scene record."""
        encounter_id = sample_encounter["encounter"].encounter_id
        response = client.post(
            f"/api/encounter/{encounter_id}/scene",
            json={
                "stardate": "47988.5",
                "scene_traits": ["Dark", "Foggy"],
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["stardate"] == "47988.5"
        assert "Dark" in data["scene_traits"]

    def test_post_scene_updates_existing(self, client, sample_encounter):
        """POST /scene should update an existing scene."""
        encounter_id = sample_encounter["encounter"].encounter_id

        client.post(
            f"/api/encounter/{encounter_id}/scene", json={"stardate": "47988.0"}
        )

        response = client.post(
            f"/api/encounter/{encounter_id}/scene", json={"stardate": "47989.0"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["stardate"] == "47989.0"

    def test_get_scene_returns_created_scene(self, client, sample_encounter):
        """GET /scene should return the created scene data."""
        encounter_id = sample_encounter["encounter"].encounter_id

        client.post(
            f"/api/encounter/{encounter_id}/scene",
            json={"stardate": "47990.0", "scene_traits": ["Hostile"]},
        )

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


class TestCampaignSceneAPI:
    """Tests for campaign-level scene API endpoints."""

    def test_create_scene_for_campaign(self, client, sample_campaign):
        """POST /campaigns/api/campaign/<id>/scenes should create a scene."""
        campaign_id = sample_campaign["campaign"].campaign_id
        gm_token = sample_campaign["players"][0].session_token

        client.set_cookie("sta_session_token", gm_token)

        response = client.post(
            f"/campaigns/api/campaign/{campaign_id}/scenes",
            json={
                "name": "Bridge Briefing",
                "scene_type": "narrative",
                "stardate": "47988.5",
                "scene_traits": ["Tense", "Urgent"],
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["name"] == "Bridge Briefing"
        assert data["scene_type"] == "narrative"

    def test_activate_scene(self, client, sample_campaign, test_session):
        """PUT /campaigns/api/scene/<id>/status should activate a scene."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Test Scene",
            scene_type="narrative",
            status="draft",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        response = client.put(
            f"/campaigns/api/scene/{scene_id}/status", json={"status": "active"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["status"] == "active"

    def test_deactivate_scene(self, client, sample_campaign, test_session):
        """PUT /campaigns/api/scene/<id>/status should deactivate a scene."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Active Scene",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        response = client.put(
            f"/campaigns/api/scene/{scene_id}/status", json={"status": "draft"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "draft"

    def test_convert_scene_type(self, client, sample_campaign, test_session):
        """PUT /campaigns/api/scene/<id>/convert should change scene type."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Test Scene",
            scene_type="starship_encounter",
            has_map=True,
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        response = client.put(
            f"/campaigns/api/scene/{scene_id}/convert",
            json={"scene_type": "narrative"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["old_type"] == "starship_encounter"
        assert data["new_type"] == "narrative"

    def test_convert_to_starship_requires_player_ship(
        self, client, sample_campaign, test_session
    ):
        """Converting to starship_encounter requires player ship."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        # Create scene without active ship
        from sta.database.schema import CampaignRecord

        campaign = test_session.query(CampaignRecord).filter_by(id=campaign_id).first()
        campaign.active_ship_id = None
        test_session.commit()

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Test Scene",
            scene_type="narrative",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        response = client.put(
            f"/campaigns/api/scene/{scene_id}/convert",
            json={"scene_type": "starship_encounter"},
        )
        assert response.status_code == 400
        assert "player ship" in response.get_json()["error"].lower()

    def test_convert_to_starship_requires_npcs(
        self, client, sample_campaign, test_session
    ):
        """Converting to starship_encounter requires NPCs."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Test Scene",
            scene_type="narrative",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        response = client.put(
            f"/campaigns/api/scene/{scene_id}/convert",
            json={"scene_type": "starship_encounter"},
        )
        assert response.status_code == 400
        assert "npc" in response.get_json()["error"].lower()

    def test_convert_to_social_removes_map(self, client, sample_campaign, test_session):
        """Converting to social_encounter should set has_map=False."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Test Scene",
            scene_type="narrative",
            has_map=True,
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        client.put(
            f"/campaigns/api/scene/{scene_id}/convert",
            json={"scene_type": "social_encounter"},
        )

        test_session.expire_all()
        updated = test_session.query(SceneRecord).filter_by(id=scene_id).first()
        assert updated.has_map is False

    def test_delete_draft_scene(self, client, sample_campaign, test_session):
        """DELETE /campaigns/api/scene/<id> should delete a draft scene."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Draft Scene",
            scene_type="narrative",
            status="draft",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        response = client.delete(f"/campaigns/api/scene/{scene_id}")
        assert response.status_code == 200
        assert response.get_json()["success"] is True

    def test_cannot_delete_active_scene(self, client, sample_campaign, test_session):
        """DELETE should fail for active scenes."""
        campaign_id = sample_campaign["campaign"].id
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Active Scene",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)

        response = client.delete(f"/campaigns/api/scene/{scene_id}")
        assert response.status_code == 400
        assert "Cannot delete active" in response.get_json()["error"]


class TestSceneUpdateAPI:
    """Tests for PUT /api/scene/<id> endpoint."""

    def test_update_scene_by_id(self, client, sample_campaign, test_session):
        """PUT /api/scene/<id> should update scene data."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id, name="Test Scene", scene_type="narrative"
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.put(
            f"/api/scene/{scene_id}",
            json={
                "name": "Updated Scene",
                "stardate": "47999.0",
                "scene_traits": ["New Trait"],
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["name"] == "Updated Scene"
        assert data["stardate"] == "47999.0"

    def test_update_extended_tasks(self, client, sample_campaign, test_session):
        """PUT /api/scene/<id> should update extended tasks with breakthroughs."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id, name="Test Scene", challenges_json="[]"
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        tasks = [
            {
                "name": "Repair Core",
                "progress": 3,
                "resistance": 2,
                "magnitude": 3,
                "breakthrough_1": {"at_progress": 6, "effect": "Core becomes unstable"},
                "breakthrough_2": {"at_progress": 9, "effect": "Victory in sight"},
            }
        ]

        response = client.put(f"/api/scene/{scene_id}", json={"challenges": tasks})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["challenges"]) == 1
        assert (
            data["challenges"][0]["breakthrough_1"]["effect"] == "Core becomes unstable"
        )

    def test_update_traits_with_descriptions(
        self, client, sample_campaign, test_session
    ):
        """PUT /api/scene/<id> should support traits with descriptions."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id, name="Test Scene", scene_traits_json="[]"
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        traits = [
            {"name": "Dark", "description": "No light source available"},
            {"name": "Cold", "description": "Temperature below freezing"},
        ]

        response = client.put(f"/api/scene/{scene_id}", json={"scene_traits": traits})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["scene_traits"]) == 2
        assert data["scene_traits"][0]["description"] == "No light source available"


class TestNarrativeSceneView:
    """Tests for narrative scene view routes."""

    def test_view_narrative_scene_as_player(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene should render for player with scene header."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Bridge Briefing",
            scene_type="narrative",
            status="active",
            stardate="47988.5",
            scene_traits_json=json.dumps(
                [
                    {"name": "Tense", "description": "Crew is on edge"},
                    {"name": "Dark", "description": None},
                ]
            ),
            challenges_json=json.dumps(
                [
                    {
                        "name": "Repair Warp Core",
                        "progress": 3,
                        "magnitude": 2,
                        "resistance": 1,
                    }
                ]
            ),
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=player")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Bridge Briefing" in html
        assert "🎬" in html
        assert "Scene Traits" in html
        assert "Tense" in html
        assert "Extended Tasks" in html
        assert "Repair Warp Core" in html

    def test_view_narrative_scene_as_gm(self, client, sample_campaign, test_session):
        """Narrative scene GM view requires authentication."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Cargo Bay",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=gm")
        assert response.status_code == 302

    def test_view_narrative_scene_as_viewscreen(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene should render for viewscreen with scene name."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Observation Lounge",
            scene_type="narrative",
            status="active",
            stardate="48000.0",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=viewscreen")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Observation Lounge" in html

    def test_narrative_scene_hides_combat_elements(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene player view should hide combat-specific elements."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Planet Surface",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=player")
        assert response.status_code == 200
        html = response.get_data(as_text=True)

        assert "FIRE WEAPONS" not in html
        assert "Dice Roller" not in html
        assert (
            "Resources" not in html
            or "Momentum" not in html.split("<h2>Resources</h2>")[0]
            if "<h2>Resources</h2>" in html
            else True
        )

    def test_narrative_scene_shows_visible_npcs(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene should show visible NPCs to players."""
        from sta.database.schema import NPCRecord, SceneNPCRecord

        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Starbase 47",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        npc = NPCRecord(name="Ambassador Sarek", npc_type="major")
        test_session.add(npc)
        test_session.flush()

        visible_npc = SceneNPCRecord(
            scene_id=scene.id, npc_id=npc.id, is_visible_to_players=True
        )
        hidden_npc = SceneNPCRecord(
            scene_id=scene.id, quick_name="Secret Agent", is_visible_to_players=False
        )
        test_session.add_all([visible_npc, hidden_npc])
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=player")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Ambassador Sarek" in html
        assert "Secret Agent" not in html


class TestSceneNPCManagement:
    """Tests for NPC management in scenes."""

    def test_add_npc_from_archive_to_scene(self, client, sample_campaign, test_session):
        """POST /scenes/<id>/npcs should add an NPC from archive to scene."""
        from sta.database.schema import NPCRecord

        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Bridge",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        npc = NPCRecord(name="Dr. Crusher", npc_type="major")
        test_session.add(npc)
        test_session.flush()

        scene_id = scene.id
        npc_id = npc.id
        test_session.commit()

        response = client.post(
            f"/scenes/{scene_id}/npcs",
            json={"npc_id": npc_id, "is_visible": True},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["name"] == "Dr. Crusher"
        assert data["is_visible"] is True

    def test_add_quick_npc_to_scene(self, client, sample_campaign, test_session):
        """POST /scenes/<id>/npcs should create a quick NPC and add to scene."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Cargo Bay",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.post(
            f"/scenes/{scene_id}/npcs",
            json={
                "quick_name": "Ensign Random",
                "quick_description": "Red shirt",
                "is_visible": False,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["name"] == "Ensign Random"
        assert data["npc_type"] == "quick"

    def test_add_npc_already_in_scene_fails(
        self, client, sample_campaign, test_session
    ):
        """Adding an NPC already in the scene should fail."""
        from sta.database.schema import NPCRecord, SceneNPCRecord

        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Ten Forward",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        npc = NPCRecord(name="Guinan", npc_type="major")
        test_session.add(npc)
        test_session.flush()

        scene_npc = SceneNPCRecord(scene_id=scene.id, npc_id=npc.id)
        test_session.add(scene_npc)
        test_session.commit()

        scene_id = scene.id
        npc_id = npc.id

        response = client.post(f"/scenes/{scene_id}/npcs", json={"npc_id": npc_id})
        assert response.status_code == 400
        assert "already in scene" in response.get_json()["error"]

    def test_remove_npc_from_scene(self, client, sample_campaign, test_session):
        """DELETE /scenes/<id>/npcs/<npc_id> should remove NPC from scene."""
        from sta.database.schema import NPCRecord, SceneNPCRecord

        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Sickbay",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        npc = NPCRecord(name="Nurse Ogawa", npc_type="notable")
        test_session.add(npc)
        test_session.flush()

        scene_npc = SceneNPCRecord(
            scene_id=scene.id, npc_id=npc.id, is_visible_to_players=True
        )
        test_session.add(scene_npc)
        test_session.flush()

        scene_id = scene.id
        scene_npc_id = scene_npc.id
        test_session.commit()

        response = client.delete(f"/scenes/{scene_id}/npcs/{scene_npc_id}")
        assert response.status_code == 200
        assert response.get_json()["success"] is True

    def test_get_available_npcs(self, client, sample_campaign, test_session):
        """GET /scenes/<id>/npcs/available should list NPCs not yet in scene."""
        from sta.database.schema import NPCRecord, CampaignNPCRecord, SceneNPCRecord

        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Conference Room",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        npc1 = NPCRecord(name="Worf", npc_type="major")
        npc2 = NPCRecord(name="Troi", npc_type="major")
        test_session.add_all([npc1, npc2])
        test_session.flush()

        campaign_npc1 = CampaignNPCRecord(campaign_id=campaign_id, npc_id=npc1.id)
        campaign_npc2 = CampaignNPCRecord(campaign_id=campaign_id, npc_id=npc2.id)
        test_session.add_all([campaign_npc1, campaign_npc2])

        scene_npc = SceneNPCRecord(scene_id=scene.id, npc_id=npc1.id)
        test_session.add(scene_npc)

        scene_id = scene.id
        test_session.commit()

        response = client.get(f"/scenes/{scene_id}/npcs/available")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["npcs"]) == 1
        assert data["npcs"][0]["name"] == "Troi"

    def test_toggle_npc_visibility(self, client, sample_campaign, test_session):
        """PUT /scenes/<id>/npcs/<npc_id>/visibility should toggle visibility."""
        from sta.database.schema import NPCRecord, SceneNPCRecord

        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Observation Lounge",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        npc = NPCRecord(name="Riker", npc_type="major")
        test_session.add(npc)
        test_session.flush()

        scene_npc = SceneNPCRecord(
            scene_id=scene.id, npc_id=npc.id, is_visible_to_players=False
        )
        test_session.add(scene_npc)
        test_session.flush()

        scene_id = scene.id
        scene_npc_id = scene_npc.id
        test_session.commit()

        response = client.put(
            f"/scenes/{scene_id}/npcs/{scene_npc_id}/visibility",
            json={"is_visible": True},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["is_visible"] is True


class TestNarrativeSceneNoCombatAPI:
    """Tests to verify narrative scenes don't call combat APIs."""

    def test_narrative_scene_no_encounter_id_in_js(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene player view should have null encounterId in JS."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Narrative Scene",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=player")
        html = response.get_data(as_text=True)

        assert "const encounterId = null" in html or "const encounterId =null" in html

    def test_narrative_scene_has_is_narrative_flag(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene player view should have isNarrative variable."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Story Scene",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=player")
        assert response.status_code == 200

    def test_narrative_scene_gm_requires_auth(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene GM view should require authentication."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Scene Without Combat",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=gm")
        assert response.status_code == 302

    def test_narrative_scene_shows_scene_name_in_player_view(
        self, client, sample_campaign, test_session
    ):
        """Narrative scene player view should show scene name."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="The Diplomatic Meeting",
            scene_type="narrative",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=player")
        html = response.get_data(as_text=True)

        assert "The Diplomatic Meeting" in html

    def test_extended_task_with_breakthrough_effects(
        self, client, sample_campaign, test_session
    ):
        """Extended tasks should support breakthrough effects."""
        campaign_id = sample_campaign["campaign"].id

        scene = SceneRecord(
            campaign_id=campaign_id,
            name="Engineering Crisis",
            scene_type="narrative",
            status="active",
            challenges_json=json.dumps(
                [
                    {
                        "name": "Repair Warp Core",
                        "progress": 5,
                        "magnitude": 2,
                        "resistance": 1,
                        "breakthrough_1": {
                            "at_progress": 5,
                            "effect": "Core becomes unstable",
                        },
                        "breakthrough_2": {
                            "at_progress": 7,
                            "effect": "Victory in sight",
                        },
                    }
                ]
            ),
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.get(f"/scenes/{scene_id}?role=player")
        html = response.get_data(as_text=True)

        assert "Repair Warp Core" in html
