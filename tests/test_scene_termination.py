"""Tests for scene termination endpoint (M3 Task 3.4)."""

import json
import uuid
import pytest
from sta.database import (
    SceneRecord,
    CampaignRecord,
    EncounterRecord,
    PersonnelEncounterRecord,
)


class TestSceneTerminationAPI:
    """Tests for POST /api/scenes/<id>/end."""

    def _create_active_starship_scene(self, test_session, sample_campaign):
        """Helper to create an active starship scene with encounter."""
        campaign = sample_campaign["campaign"]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Starship Scene",
            scene_type="starship_encounter",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

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
        test_session.flush()
        scene.encounter_id = encounter.id
        test_session.commit()
        return scene, encounter

    def _create_active_personal_scene(self, test_session, sample_campaign):
        """Helper to create an active personal scene with personnel encounter."""
        campaign = sample_campaign["campaign"]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Personal Scene",
            scene_type="personal_encounter",
            status="active",
        )
        test_session.add(scene)
        test_session.flush()

        pe = PersonnelEncounterRecord(
            scene_id=scene.id,
            momentum=campaign.momentum,
            threat=campaign.threat,
            is_active=True,
        )
        test_session.add(pe)
        test_session.commit()
        return scene, pe

    def test_end_starship_reduces_momentum_and_deactivates(
        self, client, test_session, sample_campaign
    ):
        """Ending a starship scene reduces momentum by 1 (min 0) and deactivates encounter."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 3
        test_session.commit()

        scene, encounter = self._create_active_starship_scene(
            test_session, sample_campaign
        )
        scene_id = scene.id
        encounter_id = encounter.id

        client.set_cookie("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["momentum_remaining"] == 2
        assert "closing_options" in data

        # Commit test session to see changes
        test_session.commit()

        # Verify scene completed
        updated_scene = test_session.query(SceneRecord).filter_by(id=scene_id).first()
        assert updated_scene.status == "completed"

        # Verify encounter deactivated
        updated_encounter = (
            test_session.query(EncounterRecord).filter_by(id=encounter_id).first()
        )
        assert updated_encounter.is_active is False

        # Verify campaign momentum reduced
        updated_campaign = (
            test_session.query(CampaignRecord).filter_by(id=campaign.id).first()
        )
        assert updated_campaign.momentum == 2

    def test_end_personal_reduces_momentum_and_deactivates(
        self, client, test_session, sample_campaign
    ):
        """Ending a personal scene reduces momentum and deactivates personnel encounter."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 2
        test_session.commit()

        scene, pe = self._create_active_personal_scene(test_session, sample_campaign)
        scene_id = scene.id
        pe_id = pe.id

        client.set_cookie("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["momentum_remaining"] == 1

        # Commit test session to see changes
        test_session.commit()

        # Verify personnel encounter deactivated
        updated_pe = (
            test_session.query(PersonnelEncounterRecord).filter_by(id=pe_id).first()
        )
        assert updated_pe.is_active is False

        # Verify scene completed
        updated_scene = test_session.query(SceneRecord).filter_by(id=scene_id).first()
        assert updated_scene.status == "completed"

    def test_end_caps_momentum_at_6_before_reduction(
        self, client, test_session, sample_campaign
    ):
        """If campaign momentum > 6, cap at 6 before reducing."""
        campaign = sample_campaign["campaign"]
        gm_token = sample_campaign["players"][0].session_token
        campaign.momentum = 8
        test_session.commit()

        scene, encounter = self._create_active_starship_scene(
            test_session, sample_campaign
        )
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 200
        data = response.get_json()
        # Expected: cap at 6 -> 6-1 = 5
        assert data["momentum_remaining"] == 5

    def test_end_fails_if_not_active(self, client, test_session, sample_campaign):
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
        test_session.commit()
        scene_id = scene.id

        client.set_cookie("sta_session_token", gm_token)
        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 400
        data = response.get_json()
        assert "must be active" in data["error"]

    def test_end_requires_gm_auth(self, client, test_session, sample_campaign):
        """End requires GM auth."""
        campaign = sample_campaign["campaign"]
        scene = SceneRecord(
            campaign_id=campaign.id,
            name="Active Scene",
            scene_type="starship_encounter",
            status="active",
        )
        test_session.add(scene)
        test_session.commit()
        scene_id = scene.id

        response = client.post(f"/scenes/{scene_id}/end")
        assert response.status_code == 401
