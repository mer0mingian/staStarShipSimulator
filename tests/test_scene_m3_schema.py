"""Tests for M3 scene management schema changes."""

import pytest
from sqlalchemy import inspect
from sta.database.schema import (
    Base,
    SceneRecord,
    SceneParticipantRecord,
    SceneShipRecord,
    CampaignRecord,
)
from sta.database.vtt_schema import VTTCharacterRecord, VTTShipRecord
from sta.database.async_db import engine as async_engine


async def get_table_inspector(async_session):
    """Get a synchronous inspector from an async session."""
    inspector_data = {}

    async with async_session.bind.begin() as conn:

        def _capture_inspector(sync_conn):
            insp = inspect(sync_conn)
            inspector_data["tables"] = insp.get_table_names()
            inspector_data["participant_columns"] = insp.get_columns(
                "scene_participants"
            )
            inspector_data["participant_fks"] = insp.get_foreign_keys(
                "scene_participants"
            )
            inspector_data["participant_unique"] = insp.get_unique_constraints(
                "scene_participants"
            )
            inspector_data["ship_columns"] = insp.get_columns("scene_ships")
            inspector_data["ship_fks"] = insp.get_foreign_keys("scene_ships")
            inspector_data["ship_unique"] = insp.get_unique_constraints("scene_ships")

        await conn.run_sync(_capture_inspector)

    return inspector_data


class TestSceneRecordM3Columns:
    """Test that SceneRecord has the new M3 columns with correct defaults."""

    @pytest.mark.asyncio
    async def test_next_scene_ids_column_exists(self, test_session):
        """SceneRecord should have next_scene_ids_json column."""
        campaign = CampaignRecord(campaign_id="test-m3-001", name="M3 Test Campaign")
        test_session.add(campaign)
        await test_session.flush()

        scene = SceneRecord(campaign_id=campaign.id, name="M3 Test Scene")
        test_session.add(scene)
        await test_session.flush()

        assert hasattr(scene, "next_scene_ids_json")
        assert scene.next_scene_ids_json == "[]"

    @pytest.mark.asyncio
    async def test_previous_scene_ids_column_exists(self, test_session):
        """SceneRecord should have previous_scene_ids_json column."""
        campaign = CampaignRecord(campaign_id="test-m3-002", name="M3 Test Campaign 2")
        test_session.add(campaign)
        await test_session.flush()

        scene = SceneRecord(campaign_id=campaign.id, name="M3 Test Scene 2")
        test_session.add(scene)
        await test_session.flush()

        assert hasattr(scene, "previous_scene_ids_json")
        assert scene.previous_scene_ids_json == "[]"

    @pytest.mark.asyncio
    async def test_encounter_config_json_column_exists(self, test_session):
        """SceneRecord should have encounter_config_json column."""
        campaign = CampaignRecord(campaign_id="test-m3-003", name="M3 Test Campaign 3")
        test_session.add(campaign)
        await test_session.flush()

        scene = SceneRecord(campaign_id=campaign.id, name="M3 Test Scene 3")
        test_session.add(scene)
        await test_session.flush()

        assert hasattr(scene, "encounter_config_json")
        assert scene.encounter_config_json == "{}"

    @pytest.mark.asyncio
    async def test_deprecation_comments_present(self):
        """Check that deprecation comments are present in source code."""
        import inspect
        import sta.database.schema as schema_module

        source = inspect.getsource(schema_module)

        # Check that deprecation comments are present (flexible location)
        assert "characters_present_json" in source
        assert "Deprecated: use scene_participants table" in source
        assert "enemy_ships_json" in source
        assert "Deprecated: use scene_ships table" in source


class TestSceneParticipantRecord:
    """Test the SceneParticipantRecord model."""

    @pytest.mark.asyncio
    async def test_table_exists(self, test_session):
        """Scene_participants table should exist."""
        inspector_data = await get_table_inspector(test_session)
        tables = inspector_data["tables"]
        assert "scene_participants" in tables

    @pytest.mark.asyncio
    async def test_columns_exist(self, test_session):
        """Scene_participants should have the correct columns."""
        inspector_data = await get_table_inspector(test_session)
        columns = inspector_data["participant_columns"]
        column_names = {col["name"] for col in columns}

        expected = {
            "id",
            "scene_id",
            "character_id",
            "player_id",
            "is_visible_to_players",
        }
        assert expected.issubset(column_names)

    @pytest.mark.asyncio
    async def test_foreign_keys(self, test_session):
        """Check foreign key constraints are set up correctly."""
        inspector_data = await get_table_inspector(test_session)
        fks = inspector_data["participant_fks"]

        # Check scenes FK
        scenes_fk = next((fk for fk in fks if fk["referred_table"] == "scenes"), None)
        assert scenes_fk is not None
        assert "scene_id" in scenes_fk["constrained_columns"]

        # Check vtt_characters FK
        char_fk = next(
            (fk for fk in fks if fk["referred_table"] == "vtt_characters"), None
        )
        assert char_fk is not None
        assert "character_id" in char_fk["constrained_columns"]

        # Check campaign_players FK (player_id is nullable)
        player_fk = next(
            (fk for fk in fks if fk["referred_table"] == "campaign_players"), None
        )
        assert player_fk is not None
        assert "player_id" in player_fk["constrained_columns"]

    @pytest.mark.asyncio
    async def test_unique_constraint(self, test_session):
        """Should have unique constraint on (scene_id, character_id)."""
        inspector_data = await get_table_inspector(test_session)
        constraints = inspector_data["participant_unique"]
        constraint_names = [c["name"] for c in constraints]

        assert "uq_scene_participant" in constraint_names
        uc = next(c for c in constraints if c["name"] == "uq_scene_participant")
        assert set(uc["column_names"]) == {"scene_id", "character_id"}

    @pytest.mark.asyncio
    async def test_model_creation(self, test_session):
        """Should be able to create a SceneParticipantRecord."""
        campaign = CampaignRecord(campaign_id="test-m3-011", name="M3 Test 011")
        test_session.add(campaign)
        await test_session.flush()

        scene = SceneRecord(campaign_id=campaign.id, name="M3 Test Scene 011")
        test_session.add(scene)
        await test_session.flush()

        vtt_char = VTTCharacterRecord(
            name="Test Character",
            attributes_json='{"control": 9, "daring": 10, "fitness": 8, "insight": 11, "presence": 7, "reason": 8}',
            disciplines_json='{"command": 3, "conn": 2, "engineering": 1, "medicine": 1, "science": 2, "security": 3}',
            talents_json="[]",
            focuses_json="[]",
        )
        test_session.add(vtt_char)
        await test_session.flush()

        participant = SceneParticipantRecord(
            scene_id=scene.id,
            character_id=vtt_char.id,
            player_id=None,
            is_visible_to_players=False,
        )
        test_session.add(participant)
        await test_session.flush()

        assert participant.id is not None
        assert participant.scene_id == scene.id
        assert participant.character_id == vtt_char.id
        assert participant.is_visible_to_players is False


class TestSceneShipRecord:
    """Test the SceneShipRecord model."""

    @pytest.mark.asyncio
    async def test_table_exists(self, test_session):
        """Scene_ships table should exist."""
        inspector_data = await get_table_inspector(test_session)
        tables = inspector_data["tables"]
        assert "scene_ships" in tables

    @pytest.mark.asyncio
    async def test_columns_exist(self, test_session):
        """Scene_ships should have the correct columns."""
        inspector_data = await get_table_inspector(test_session)
        columns = inspector_data["ship_columns"]
        column_names = {col["name"] for col in columns}

        expected = {"id", "scene_id", "ship_id", "is_visible_to_players"}
        assert expected.issubset(column_names)

    @pytest.mark.asyncio
    async def test_foreign_keys(self, test_session):
        """Check foreign key constraints are set up correctly."""
        inspector_data = await get_table_inspector(test_session)
        fks = inspector_data["ship_fks"]

        # Check scenes FK
        scenes_fk = next((fk for fk in fks if fk["referred_table"] == "scenes"), None)
        assert scenes_fk is not None
        assert "scene_id" in scenes_fk["constrained_columns"]

        # Check starships FK
        ship_fk = next((fk for fk in fks if fk["referred_table"] == "starships"), None)
        assert ship_fk is not None
        assert "ship_id" in ship_fk["constrained_columns"]

    @pytest.mark.asyncio
    async def test_unique_constraint(self, test_session):
        """Should have unique constraint on (scene_id, ship_id)."""
        inspector_data = await get_table_inspector(test_session)
        constraints = inspector_data["ship_unique"]
        constraint_names = [c["name"] for c in constraints]

        assert "uq_scene_ship" in constraint_names
        uc = next(c for c in constraints if c["name"] == "uq_scene_ship")
        assert set(uc["column_names"]) == {"scene_id", "ship_id"}

    @pytest.mark.asyncio
    async def test_model_creation(self, test_session):
        """Should be able to create a SceneShipRecord."""
        campaign = CampaignRecord(campaign_id="test-m3-021", name="M3 Test 021")
        test_session.add(campaign)
        await test_session.flush()

        scene = SceneRecord(campaign_id=campaign.id, name="M3 Test Scene 021")
        test_session.add(scene)
        await test_session.flush()

        vtt_ship = VTTShipRecord(
            name="Test Ship",
            ship_class="Frigate",
            scale=4,
            systems_json='{"comms": 9, "computers": 9, "engines": 9, "sensors": 9, "structure": 9, "weapons": 9}',
            departments_json='{"command": 3, "conn": 3, "engineering": 3, "medicine": 2, "science": 3, "security": 3}',
            weapons_json="[]",
            talents_json="[]",
            traits_json="[]",
            breaches_json="[]",
            shields=10,
            shields_max=10,
            resistance=4,
        )
        test_session.add(vtt_ship)
        await test_session.flush()

        scene_ship = SceneShipRecord(
            scene_id=scene.id,
            ship_id=vtt_ship.id,
            is_visible_to_players=True,
        )
        test_session.add(scene_ship)
        await test_session.flush()

        assert scene_ship.id is not None
        assert scene_ship.scene_id == scene.id
        assert scene_ship.ship_id == vtt_ship.id
        assert scene_ship.is_visible_to_players is True
