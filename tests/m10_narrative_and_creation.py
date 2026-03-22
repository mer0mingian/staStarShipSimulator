"""
Tests for M10.9 - Character Sheet Narrative Tab & M10.10 - Guided Creation Flow.

Tests verify:
- LogEntry model and API endpoints
- Value status tracking and interactions
- Character creation wizard validation
- Ship creation wizard validation
- Personal log visibility (players can see others' logs)
- Value mechanics (Used/Challenged/Complied)
"""

import json
import pytest
from sta.database.vtt_schema import VTTCharacterRecord, LogEntryRecord, VTTShipRecord
from sta.database.schema import CampaignRecord, CampaignPlayerRecord


@pytest.mark.m10_narrative_and_creation
class TestLogEntryModel:
    """Tests for LogEntryRecord model."""

    async def test_create_log_entry(self, client, test_session):
        """Test creating a log entry via API."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/logs",
            json={
                "log_type": "PERSONAL",
                "content": "My character is reflecting on the mission.",
                "event_type": "note",
                "user_id": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["log_type"] == "PERSONAL"
        assert "reflecting" in data["content"]

    async def test_create_log_entry_invalid_type(self, client, test_session):
        """Test creating log entry with invalid type."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/logs",
            json={"log_type": "INVALID", "content": "Test"},
        )
        assert response.status_code == 400
        assert "PERSONAL, MISSION, or VALUE" in response.json()["detail"]

    async def test_get_character_logs(self, client, test_session):
        """Test getting all logs for a character."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.flush()

        log1 = LogEntryRecord(
            character_id=char.id,
            log_type="PERSONAL",
            content="Personal note",
            event_type="note",
            character_name=char.name,
        )
        log2 = LogEntryRecord(
            character_id=char.id,
            log_type="MISSION",
            content="Entered the bridge",
            event_type="scene_enter",
            character_name=char.name,
        )
        test_session.add_all([log1, log2])
        await test_session.commit()

        response = client.get(f"/api/characters/{char.id}/logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 2

    async def test_get_character_logs_filter_by_type(self, client, test_session):
        """Test filtering logs by type."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.flush()

        log1 = LogEntryRecord(
            character_id=char.id,
            log_type="PERSONAL",
            content="Personal note",
            event_type="note",
            character_name=char.name,
        )
        log2 = LogEntryRecord(
            character_id=char.id,
            log_type="MISSION",
            content="Mission log",
            event_type="scene_enter",
            character_name=char.name,
        )
        test_session.add_all([log1, log2])
        await test_session.commit()

        response = client.get(f"/api/characters/{char.id}/logs?log_type=PERSONAL")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 1
        assert data["logs"][0]["log_type"] == "PERSONAL"

    async def test_update_log_entry(self, client, test_session):
        """Test updating a log entry."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.flush()

        log = LogEntryRecord(
            character_id=char.id,
            log_type="PERSONAL",
            content="Original content",
            event_type="note",
            character_name=char.name,
        )
        test_session.add(log)
        await test_session.commit()

        response = client.put(
            f"/api/characters/{char.id}/logs/{log.id}",
            json={"content": "Updated content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"

    async def test_delete_log_entry(self, client, test_session):
        """Test deleting a log entry."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.flush()

        log = LogEntryRecord(
            character_id=char.id,
            log_type="PERSONAL",
            content="To be deleted",
            event_type="note",
            character_name=char.name,
        )
        test_session.add(log)
        await test_session.commit()
        log_id = log.id

        response = client.delete(f"/api/characters/{char.id}/logs/{log_id}")
        assert response.status_code == 200

        response = client.get(f"/api/characters/{char.id}/logs")
        data = response.json()
        assert len(data["logs"]) == 0


@pytest.mark.m10_narrative_and_creation
class TestSceneEventLogging:
    """Tests for auto-generated scene event logs."""

    async def test_log_scene_enter(self, client, test_session):
        """Test auto-creating log for scene enter."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/logs/scene-event",
            json={
                "event_type": "scene_enter",
                "scene_name": "Bridge",
                "description": "Entering the bridge to address the crew.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "scene_enter"
        assert data["log_type"] == "MISSION"
        assert "Bridge" in data["content"]

    async def test_log_scene_exit(self, client, test_session):
        """Test auto-creating log for scene exit."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/logs/scene-event",
            json={"event_type": "scene_exit", "scene_name": "Ready Room"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "scene_exit"

    async def test_log_scene_invalid_event(self, client, test_session):
        """Test invalid scene event type."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/logs/scene-event",
            json={"event_type": "invalid_event", "scene_name": "Bridge"},
        )
        assert response.status_code == 400


@pytest.mark.m10_narrative_and_creation
class TestValueEventLogging:
    """Tests for auto-generated Value interaction logs."""

    async def test_log_value_challenged(self, client, test_session):
        """Test logging Value challenged event."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                    }
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/logs/value-event",
            json={
                "event_type": "value_challenged",
                "value_name": "Integrity",
                "description": "Had to lie to protect crew.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "value_challenged"
        assert data["log_type"] == "VALUE"
        assert "Integrity" in data["content"]

    async def test_log_value_complied(self, client, test_session):
        """Test logging Value complied event."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Logic",
                        "description": "I trust rational analysis",
                        "helpful": True,
                    }
                ]
            ),
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/logs/value-event",
            json={
                "event_type": "value_complied",
                "value_name": "Logic",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "value_complied"


@pytest.mark.m10_narrative_and_creation
class TestValueStatusTracking:
    """Tests for Value status tracking (M10.9)."""

    async def test_get_values_with_status(self, client, test_session):
        """Test getting Values with full status information."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                        "used_this_session": False,
                    },
                    {
                        "name": "Courage",
                        "description": "I face danger",
                        "helpful": True,
                        "used_this_session": True,
                    },
                ]
            ),
            determination=2,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.get(f"/api/characters/{char.id}/values/status")
        assert response.status_code == 200
        data = response.json()

        assert len(data["values"]) == 2
        assert data["determination"] == 2

        available = [v for v in data["values"] if v["name"] == "Integrity"][0]
        assert available["status"] == "Available"
        assert available["used_this_session"] is False

        used = [v for v in data["values"] if v["name"] == "Courage"][0]
        assert used["status"] == "Used"
        assert used["used_this_session"] is True

    async def test_interact_with_value_use(self, client, test_session):
        """Test using a Value (spends Determination)."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                        "used_this_session": False,
                    }
                ]
            ),
            determination=2,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={
                "value_name": "Integrity",
                "action": "use",
                "description": "Invoking integrity to resist temptation.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "use"
        assert data["determination"] == 1

    async def test_interact_with_value_challenge(self, client, test_session):
        """Test challenging a Value (gains Determination)."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                        "used_this_session": False,
                    }
                ]
            ),
            determination=1,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={
                "value_name": "Integrity",
                "action": "challenge",
                "description": "Had to lie to protect the crew.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "challenge"
        assert data["determination"] == 2

    async def test_interact_with_value_comply(self, client, test_session):
        """Test complying a Value (gains Determination)."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                        "used_this_session": False,
                    }
                ]
            ),
            determination=1,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={
                "value_name": "Integrity",
                "action": "comply",
                "description": "Followed orders despite doubts.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "comply"
        assert data["determination"] == 2

    async def test_use_value_already_used_fails(self, client, test_session):
        """Test that using an already-used Value fails."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                        "used_this_session": True,
                    }
                ]
            ),
            determination=1,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={"value_name": "Integrity", "action": "use"},
        )
        assert response.status_code == 400
        assert "already been used" in response.json()["detail"]

    async def test_challenge_value_at_max_determination(self, client, test_session):
        """Test challenging Value when Determination is at max (no gain)."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                    }
                ]
            ),
            determination=3,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={"value_name": "Integrity", "action": "challenge"},
        )
        assert response.status_code == 400
        assert "already at maximum" in response.json()["detail"]

    async def test_use_value_no_determination_fails(self, client, test_session):
        """Test using Value when Determination is 0."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                    }
                ]
            ),
            determination=0,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={"value_name": "Integrity", "action": "use"},
        )
        assert response.status_code == 400
        assert "Not enough Determination" in response.json()["detail"]


@pytest.mark.m10_narrative_and_creation
class TestPersonalLogVisibility:
    """Tests for personal log visibility - all players can see others' logs."""

    async def test_personal_log_visible_to_players(self, client, test_session):
        """Test that personal logs are visible to other players."""
        campaign = CampaignRecord(
            campaign_id="test-campaign", name="Test Campaign", is_active=True
        )
        test_session.add(campaign)
        await test_session.flush()

        char1 = VTTCharacterRecord(
            name="Character One",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            campaign_id=campaign.id,
        )
        char2 = VTTCharacterRecord(
            name="Character Two",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            campaign_id=campaign.id,
        )
        test_session.add_all([char1, char2])
        await test_session.flush()

        log = LogEntryRecord(
            character_id=char1.id,
            log_type="PERSONAL",
            content="My secret thoughts about the mission.",
            event_type="note",
            character_name=char1.name,
            created_by_user_id=1,
        )
        test_session.add(log)
        await test_session.commit()

        response = client.get(
            f"/api/characters/{char1.id}/logs/personal?campaign_id={campaign.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 1
        assert data["logs"][0]["content"] == "My secret thoughts about the mission."

    async def test_personal_log_excludes_owner(self, client, test_session):
        """Test that players can get their own personal logs for viewing purposes."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
        )
        test_session.add(char)
        await test_session.flush()

        log = LogEntryRecord(
            character_id=char.id,
            log_type="PERSONAL",
            content="Personal reflection",
            event_type="note",
            character_name=char.name,
            created_by_user_id=1,
        )
        test_session.add(log)
        await test_session.commit()

        response = client.get(f"/api/characters/{char.id}/logs/personal")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 1


@pytest.mark.m10_narrative_and_creation
class TestCharacterCreationWizard:
    """Tests for guided character creation wizard (M10.10)."""

    async def test_get_creation_options(self, client, test_session):
        """Test getting available options for character creation."""
        response = client.get("/api/characters/wizard/options")
        assert response.status_code == 200
        data = response.json()

        assert "species" in data
        assert "Human" in data["species"]
        assert "Vulcan" in data["species"]

        assert "attributes" in data
        assert data["attributes"]["min"] == 7
        assert data["attributes"]["max"] == 12

        assert "departments" in data
        assert "talents" in data
        assert "focuses" in data
        assert "ranks" in data
        assert "value_templates" in data

        assert "Integrity" in [v["name"] for v in data["value_templates"]]

    async def test_wizard_step_validation_step1(self, client, test_session):
        """Test Step 1 validation (Foundation)."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 1,
                "character": {
                    "name": "Test Captain",
                    "species": "Human",
                    "attributes": {
                        "control": 10,
                        "fitness": 9,
                        "daring": 8,
                        "insight": 7,
                        "presence": 11,
                        "reason": 9,
                    },
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["step_received"] == 1

    async def test_wizard_step_validation_step1_invalid_attribute(
        self, client, test_session
    ):
        """Test Step 1 validation with invalid attribute."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 1,
                "character": {
                    "name": "Test Captain",
                    "species": "Human",
                    "attributes": {
                        "control": 15,  # Invalid - too high
                        "fitness": 9,
                        "daring": 8,
                        "insight": 7,
                        "presence": 11,
                        "reason": 9,
                    },
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["validation_passed"] is False
        assert any("7-12" in e for e in data["errors"])

    async def test_wizard_step_validation_step2(self, client, test_session):
        """Test Step 2 validation (Specialization)."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 2,
                "character": {
                    "disciplines": {
                        "command": 3,
                        "conn": 2,
                        "engineering": 3,
                        "medicine": 2,
                        "science": 3,
                        "security": 2,
                    },
                    "talents": ["Bold (Command)", "Tough"],
                    "focuses": ["Leadership", "Tactics", "Diplomacy"],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["step_received"] == 2

    async def test_wizard_step_validation_step2_invalid_talent(
        self, client, test_session
    ):
        """Test Step 2 validation with invalid talent."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 2,
                "character": {
                    "talents": ["Invalid Talent"],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["validation_passed"] is False
        assert any("Invalid talent" in e for e in data["errors"])

    async def test_wizard_step_validation_step3_requires_2_values(
        self, client, test_session
    ):
        """Test Step 3 validation requires minimum 2 Values."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 3,
                "character": {
                    "values": [{"name": "Integrity"}],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["validation_passed"] is False
        assert any("At least 2 Values" in e for e in data["errors"])

    async def test_wizard_step_validation_step3_valid(self, client, test_session):
        """Test Step 3 validation with valid Values."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 3,
                "character": {
                    "values": [
                        {"name": "Integrity", "description": "I uphold principles"},
                        {"name": "Courage", "description": "I face danger"},
                    ],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["validation_passed"] is True

    async def test_wizard_final_creation(self, client, test_session):
        """Test final character creation via wizard."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": "final",
                "character": {
                    "name": "Captain Kirk",
                    "species": "Human",
                    "rank": "Captain",
                    "attributes": {
                        "control": 10,
                        "fitness": 9,
                        "daring": 8,
                        "insight": 7,
                        "presence": 11,
                        "reason": 7,
                    },
                    "disciplines": {
                        "command": 3,
                        "conn": 2,
                        "engineering": 2,
                        "medicine": 1,
                        "science": 2,
                        "security": 2,
                    },
                    "talents": ["Bold (Command)"],
                    "focuses": ["Diplomacy", "Strategy / Tactics"],
                    "values": [
                        {
                            "name": "Integrity",
                            "description": "I uphold principles",
                            "helpful": True,
                        },
                        {
                            "name": "Courage",
                            "description": "I face danger",
                            "helpful": True,
                        },
                    ],
                    "equipment": ["Starfleet Uniform", "Combadge"],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        if not data.get("success"):
            print("ERRORS:", data.get("errors"))
        assert data["success"] is True
        assert data["character"]["name"] == "Captain Kirk"
        assert data["character"]["species"] == "Human"
        assert data["character"]["rank"] == "Captain"
        assert data["character"]["stress_max"] == 9  # Fitness = 9
        assert data["character"]["determination"] == 1
        assert data["character"]["determination_max"] == 3
        assert data["character"]["name"] == "Captain Kirk"
        assert data["character"]["species"] == "Human"
        assert data["character"]["rank"] == "Captain"
        assert data["character"]["stress_max"] == 9  # Fitness = 9
        assert data["character"]["determination"] == 1
        assert data["character"]["determination_max"] == 3

    async def test_wizard_final_creation_fails_with_validation_errors(
        self, client, test_session
    ):
        """Test final creation fails if validation errors exist."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": "final",
                "character": {
                    "name": "Invalid Captain",
                    "species": "Human",
                    "attributes": {
                        "control": 10,
                        "fitness": 9,
                        "daring": 8,
                        "insight": 7,
                        "presence": 11,
                        "reason": 9,
                    },
                    "values": [{"name": "Integrity"}],  # Only 1 Value
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is False
        assert any("At least 2 Values" in e for e in data["errors"])

    async def test_wizard_validation_enforces_attribute_range(
        self, client, test_session
    ):
        """Test wizard enforces attribute range 7-12."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 1,
                "character": {
                    "attributes": {
                        "control": 6,  # Too low
                        "fitness": 9,
                        "daring": 8,
                        "insight": 7,
                        "presence": 11,
                        "reason": 9,
                    },
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["validation_passed"] is False

    async def test_wizard_validation_enforces_discipline_range(
        self, client, test_session
    ):
        """Test wizard enforces discipline range 0-5."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": 2,
                "character": {
                    "disciplines": {
                        "command": 6,  # Too high
                        "conn": 3,
                        "engineering": 1,
                        "medicine": 2,
                        "science": 1,
                        "security": 2,
                    },
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["validation_passed"] is False
        assert any("0-5" in e for e in data["errors"])


@pytest.mark.m10_narrative_and_creation
class TestShipCreationWizard:
    """Tests for ship creation wizard (M10.10)."""

    async def test_get_ship_creation_options(self, client, test_session):
        """Test getting available options for ship creation."""
        response = client.get("/api/ships/wizard/options")
        assert response.status_code == 200
        data = response.json()

        assert "ship_classes" in data
        assert "Constitution" in data["ship_classes"]
        assert "scale_range" in data
        assert "systems" in data
        assert "departments" in data
        assert "weapons" in data

    async def test_create_ship_wizard(self, client, test_session):
        """Test creating a ship via wizard."""
        response = client.post(
            "/api/ships/wizard",
            json={
                "ship": {
                    "name": "USS Enterprise",
                    "ship_class": "Constitution",
                    "registry": "NCC-1701",
                    "scale": 4,
                    "systems": {
                        "comms": 3,
                        "computers": 3,
                        "engines": 4,
                        "sensors": 4,
                        "structure": 3,
                        "weapons": 3,
                    },
                    "departments": {
                        "command": 2,
                        "conn": 1,
                        "engineering": 1,
                        "medicine": 1,
                        "science": 1,
                        "security": 1,
                    },
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        if not data.get("success"):
            print("ERRORS:", data.get("errors"))
        assert data["success"] is True
        assert data["ship"]["name"] == "USS Enterprise"
        assert data["ship"]["registry"] == "NCC-1701"

    async def test_create_ship_wizard_invalid_scale(self, client, test_session):
        """Test creating ship with invalid scale fails."""
        response = client.post(
            "/api/ships/wizard",
            json={
                "ship": {
                    "name": "Invalid Ship",
                    "scale": 10,  # Invalid
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is False
        assert any("Scale" in e for e in data["errors"])

    async def test_create_ship_wizard_invalid_system(self, client, test_session):
        """Test creating ship with invalid system rating fails."""
        response = client.post(
            "/api/ships/wizard",
            json={
                "ship": {
                    "name": "Invalid Ship",
                    "scale": 4,
                    "systems": {
                        "comms": 7,
                        "computers": 10,  # Invalid - too high
                        "engines": 8,
                        "sensors": 8,
                        "structure": 7,
                        "weapons": 7,
                    },
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is False
        assert any("0-5" in e for e in data["errors"])


@pytest.mark.m10_narrative_and_creation
class TestValueRulesCompliance:
    """Tests to verify STA 2E rules compliance for Value mechanics."""

    async def test_determination_starts_at_1(self, client, test_session):
        """Test that new characters have Determination starting at 1."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": "final",
                "character": {
                    "name": "New Character",
                    "species": "Human",
                    "attributes": {
                        "control": 10,
                        "fitness": 9,
                        "daring": 7,
                        "insight": 8,
                        "presence": 9,
                        "reason": 8,
                    },
                    "values": [
                        {"name": "Integrity", "description": "Test"},
                        {"name": "Courage", "description": "Test"},
                    ],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["character"]["determination"] == 1
        assert data["character"]["determination_max"] == 3

    async def test_stress_max_equals_fitness(self, client, test_session):
        """Test that Stress max equals Fitness attribute."""
        response = client.post(
            "/api/characters/wizard",
            json={
                "step": "final",
                "character": {
                    "name": "Test Character",
                    "species": "Vulcan",
                    "attributes": {
                        "control": 12,
                        "fitness": 11,
                        "daring": 7,
                        "insight": 10,
                        "presence": 8,
                        "reason": 12,
                    },
                    "values": [
                        {"name": "Logic", "description": "Test"},
                        {"name": "Duty", "description": "Test"},
                    ],
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["character"]["stress_max"] == 11  # Fitness = 11

    async def test_value_used_consumes_determination(self, client, test_session):
        """Test that using a Value consumes 1 Determination."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                    }
                ]
            ),
            determination=2,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={"value_name": "Integrity", "action": "use"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["determination"] == 1  # Lost 1 from 2

    async def test_challenge_comply_grants_determination(self, client, test_session):
        """Test that challenging/complying a Value grants 1 Determination."""
        char = VTTCharacterRecord(
            name="Test Character",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 10,
                    "daring": 8,
                    "insight": 7,
                    "presence": 11,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 2,
                    "science": 4,
                    "security": 2,
                }
            ),
            values_json=json.dumps(
                [
                    {
                        "name": "Integrity",
                        "description": "I uphold principles",
                        "helpful": True,
                    },
                    {
                        "name": "Courage",
                        "description": "I face danger",
                        "helpful": True,
                    },
                ]
            ),
            determination=1,
            determination_max=3,
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={"value_name": "Integrity", "action": "challenge"},
        )
        assert response.status_code == 200
        assert response.json()["determination"] == 2

        response = client.post(
            f"/api/characters/{char.id}/values/interact",
            json={"value_name": "Courage", "action": "comply"},
        )
        assert response.status_code == 200
        assert response.json()["determination"] == 3
