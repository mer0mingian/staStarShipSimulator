"""Tests for Scene → Encounter derivation (M10.1, M10.3) and Value session tracking (M10.4)."""

import json
import pytest
from sqlalchemy import select

from sta.database.schema import (
    SceneRecord,
    CampaignRecord,
    StarshipRecord,
    EncounterRecord,
    PersonnelEncounterRecord,
    CampaignPlayerRecord,
)
from sta.database.vtt_schema import VTTCharacterRecord as VTTChar
from sta.database.schema import SceneShipRecord, SceneParticipantRecord


class TestSceneEncounterDerivation:
    """Tests for Scene → Encounter derivation."""

    @pytest.mark.asyncio
    async def test_standalone_encounter_creation_returns_410(
        self, client, test_session, sample_campaign
    ):
        """POST /encounters/new returns 410 Gone - standalone creation deprecated."""
        response = client.post("/encounters/new")
        assert response.status_code == 410
        data = response.json()
        assert data["error"] == "deprecated"
        assert "Scene activation" in data["message"]

    @pytest.mark.asyncio
    async def test_standalone_encounter_get_shows_deprecation(
        self, client, test_session, sample_campaign
    ):
        """GET /encounters/new shows deprecation message (HTML)."""
        response = client.get("/encounters/new")
        assert response.status_code == 200
        assert "deprecated" in response.text.lower()
        assert "Scene activation" in response.text

    @pytest.mark.asyncio
    async def test_activate_starship_wires_encounter_config(
        self, client, test_session, sample_campaign, sample_enemy_ship_data
    ):
        """Scene activation wires encounter_config_json into EncounterRecord."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Starship Scene",
            scene_type="starship_encounter",
            status="draft",
            encounter_config_json=json.dumps(
                {
                    "npc_turn_mode": "all_npcs",
                    "gm_spends_threat_to_start": True,
                }
            ),
        )
        test_session.add(scene)
        await test_session.flush()

        player_ship_id = campaign.active_ship_id
        test_session.add(
            SceneShipRecord(
                scene_id=scene.id, ship_id=player_ship_id, is_visible_to_players=False
            )
        )

        enemy_ship = StarshipRecord(**sample_enemy_ship_data)
        test_session.add(enemy_ship)
        await test_session.flush()
        test_session.add(
            SceneShipRecord(
                scene_id=scene.id, ship_id=enemy_ship.id, is_visible_to_players=False
            )
        )
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene.id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "encounter_id" in data

        await test_session.commit()

        encounter_id = data["encounter_id"]
        result = await test_session.execute(
            select(EncounterRecord).filter(EncounterRecord.id == encounter_id)
        )
        encounter = result.scalars().first()

        assert encounter is not None
        config = json.loads(encounter.encounter_config_json)
        assert config["npc_turn_mode"] == "all_npcs"
        assert config["gm_spends_threat_to_start"] is True

    @pytest.mark.asyncio
    async def test_activate_starship_wires_scene_traits(
        self, client, test_session, sample_campaign, sample_enemy_ship_data
    ):
        """Scene activation wires scene_traits_json into EncounterRecord."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene_traits = [
            {
                "name": "Dark Environment",
                "effect": "difficulty_plus",
                "potency": 1,
                "description": "Limited visibility",
            },
            {
                "name": "Hostile Terrain",
                "effect": "complication_plus",
                "potency": 1,
                "description": "Rough conditions",
            },
        ]

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Starship Scene",
            scene_type="starship_encounter",
            status="draft",
            scene_traits_json=json.dumps(scene_traits),
        )
        test_session.add(scene)
        await test_session.flush()

        player_ship_id = campaign.active_ship_id
        test_session.add(
            SceneShipRecord(
                scene_id=scene.id, ship_id=player_ship_id, is_visible_to_players=False
            )
        )

        enemy_ship = StarshipRecord(**sample_enemy_ship_data)
        test_session.add(enemy_ship)
        await test_session.flush()
        test_session.add(
            SceneShipRecord(
                scene_id=scene.id, ship_id=enemy_ship.id, is_visible_to_players=False
            )
        )
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene.id}/activate")
        assert response.status_code == 200

        await test_session.commit()

        encounter_id = response.json()["encounter_id"]
        result = await test_session.execute(
            select(EncounterRecord).filter(EncounterRecord.id == encounter_id)
        )
        encounter = result.scalars().first()

        traits = json.loads(encounter.scene_traits_json)
        assert len(traits) == 2
        assert traits[0]["name"] == "Dark Environment"
        assert traits[0]["effect"] == "difficulty_plus"
        assert traits[1]["name"] == "Hostile Terrain"


class TestValueSessionTracking:
    """Tests for Value session tracking (M10.4)."""

    @pytest.mark.asyncio
    async def test_get_character_values_includes_session_status(
        self, client, test_session, sample_campaign
    ):
        """GET /api/characters/{id}/values returns values with used_this_session status."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        char = VTTChar(
            campaign_id=campaign.id,
            name="Test Character",
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
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 3,
                    "science": 3,
                    "security": 3,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Logic Above All",
                        "description": "Trust in rational analysis",
                        "helpful": True,
                    },
                    {
                        "name": "Protect the Crew",
                        "description": "Safety is paramount",
                        "helpful": True,
                    },
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.get(f"/api/characters/{char.id}/values")
        assert response.status_code == 200
        data = response.json()
        assert len(data["values"]) == 2
        assert all(v.get("used_this_session") is False for v in data["values"])

    @pytest.mark.asyncio
    async def test_add_value_initializes_session_status(
        self, client, test_session, sample_campaign
    ):
        """Adding a Value initializes used_this_session to False."""
        campaign = sample_campaign["campaign"]

        char = VTTChar(
            campaign_id=campaign.id,
            name="Test Character",
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
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 3,
                    "science": 3,
                    "security": 3,
                }
            ),
            values_json=json.dumps([]),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values",
            json={"name": "New Value", "description": "Test value", "helpful": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["added"]["used_this_session"] is False
        assert data["added"]["name"] == "New Value"

    @pytest.mark.asyncio
    async def test_mark_value_used_once_per_session(
        self, client, test_session, sample_campaign
    ):
        """A Value can only be used once per session."""
        campaign = sample_campaign["campaign"]

        char = VTTChar(
            campaign_id=campaign.id,
            name="Test Character",
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
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 3,
                    "science": 3,
                    "security": 3,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Test Value",
                        "description": "Test",
                        "helpful": True,
                        "used_this_session": False,
                    },
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.put(f"/api/characters/{char.id}/values/Test Value/use")
        assert response.status_code == 200
        data = response.json()
        assert data["used_this_session"] is True

        response = client.put(f"/api/characters/{char.id}/values/Test Value/use")
        assert response.status_code == 400
        assert "already been used" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_mark_value_challenged_grants_determination(
        self, client, test_session, sample_campaign
    ):
        """Challenging a Value grants 1 Determination."""
        campaign = sample_campaign["campaign"]

        char = VTTChar(
            campaign_id=campaign.id,
            name="Test Character",
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
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 3,
                    "science": 3,
                    "security": 3,
                }
            ),
            determination=1,
            determination_max=3,
            values_json=json.dumps(
                [
                    {"name": "Test Value", "description": "Test", "helpful": True},
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/values/Test Value/challenge",
            json={"reason": "Logic conflicts with saving lives"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["determination"] == 2
        assert "challenged" in data["message"]

    @pytest.mark.asyncio
    async def test_mark_value_complied_grants_determination(
        self, client, test_session, sample_campaign
    ):
        """Complying with a Value grants 1 Determination."""
        campaign = sample_campaign["campaign"]

        char = VTTChar(
            campaign_id=campaign.id,
            name="Test Character",
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
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 3,
                    "science": 3,
                    "security": 3,
                }
            ),
            determination=1,
            determination_max=3,
            values_json=json.dumps(
                [
                    {"name": "Test Value", "description": "Test", "helpful": True},
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/values/Test Value/comply",
            json={"reason": "Following orders despite doubts"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["determination"] == 2
        assert "complied" in data["message"]

    @pytest.mark.asyncio
    async def test_reset_values_session(self, client, test_session, sample_campaign):
        """Resetting session clears used_this_session on all Values."""
        campaign = sample_campaign["campaign"]

        char = VTTChar(
            campaign_id=campaign.id,
            name="Test Character",
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
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 3,
                    "science": 3,
                    "security": 3,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Value 1",
                        "description": "Test 1",
                        "helpful": True,
                        "used_this_session": True,
                    },
                    {
                        "name": "Value 2",
                        "description": "Test 2",
                        "helpful": True,
                        "used_this_session": True,
                    },
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(f"/api/characters/{char.id}/values/reset-session")
        assert response.status_code == 200
        data = response.json()
        assert all(not v.get("used_this_session") for v in data["values"])


class TestSceneTraitsAPI:
    """Tests for Scene Traits API (M10.2)."""

    @pytest.mark.asyncio
    async def test_get_scene_traits_requires_gm_auth(
        self, client, test_session, sample_campaign
    ):
        """Getting scene traits requires GM authentication."""
        campaign = sample_campaign["campaign"]

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            status="draft",
            scene_traits_json=json.dumps([{"name": "Test", "effect": "neutral"}]),
        )
        test_session.add(scene)
        await test_session.commit()

        response = client.get(f"/scenes/{scene.id}/traits")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_scene_traits(self, client, test_session, sample_campaign):
        """GM can get scene traits."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        traits = [
            {
                "name": "Dark",
                "effect": "difficulty_plus",
                "potency": 1,
                "description": "Limited visibility",
            },
        ]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            status="draft",
            scene_traits_json=json.dumps(traits),
        )
        test_session.add(scene)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.get(f"/scenes/{scene.id}/traits")
        assert response.status_code == 200
        data = response.json()
        assert len(data["traits"]) == 1
        assert data["traits"][0]["name"] == "Dark"

    @pytest.mark.asyncio
    async def test_update_scene_traits(self, client, test_session, sample_campaign):
        """GM can update scene traits."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()

        new_traits = [
            {
                "name": "Hostile",
                "effect": "complication_plus",
                "potency": 2,
                "description": "Dangerous",
            },
        ]

        client.cookies.set("sta_session_token", gm_token)
        response = client.put(f"/scenes/{scene.id}/traits", json={"traits": new_traits})
        assert response.status_code == 200

        await test_session.commit()
        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene.id)
        )
        updated_scene = result.scalars().first()
        traits = json.loads(updated_scene.scene_traits_json)
        assert len(traits) == 1
        assert traits[0]["name"] == "Hostile"

    @pytest.mark.asyncio
    async def test_add_scene_trait(self, client, test_session, sample_campaign):
        """GM can add a single trait to scene."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(
            f"/scenes/{scene.id}/traits",
            json={"name": "New Trait", "effect": "difficulty_plus", "potency": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["trait"]["name"] == "New Trait"

    @pytest.mark.asyncio
    async def test_remove_scene_trait(self, client, test_session, sample_campaign):
        """GM can remove a trait from scene."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            status="draft",
            scene_traits_json=json.dumps(
                [
                    {"name": "Keep Me", "effect": "neutral"},
                    {"name": "Remove Me", "effect": "neutral"},
                ]
            ),
        )
        test_session.add(scene)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.delete(f"/scenes/{scene.id}/traits/Remove Me")
        assert response.status_code == 200

        await test_session.commit()
        result = await test_session.execute(
            select(SceneRecord).filter(SceneRecord.id == scene.id)
        )
        updated_scene = result.scalars().first()
        traits = json.loads(updated_scene.scene_traits_json)
        assert len(traits) == 1
        assert traits[0]["name"] == "Keep Me"

    @pytest.mark.asyncio
    async def test_scene_trait_validates_effect(
        self, client, test_session, sample_campaign
    ):
        """Invalid trait effect is rejected."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token

        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Test Scene",
            status="draft",
        )
        test_session.add(scene)
        await test_session.commit()

        client.cookies.set("sta_session_token", gm_token)
        response = client.post(
            f"/scenes/{scene.id}/traits",
            json={"name": "Bad Trait", "effect": "invalid_effect"},
        )
        assert response.status_code == 400
        assert "Invalid effect" in response.json()["detail"]
