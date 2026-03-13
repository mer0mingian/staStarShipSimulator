"""
Pytest fixtures for STA Starship Simulator testing.

Provides test database, FastAPI app client, and sample data.
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import random
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from sta.database.schema import (
    Base,
    CharacterRecord,
    StarshipRecord,
    EncounterRecord,
    CampaignRecord,
    CampaignPlayerRecord,
    SceneRecord,
    CombatLogRecord,
)
from sta.database.vtt_schema import VTTCharacterRecord, VTTShipRecord
from sta.database import get_db
from sta.database.async_db import engine as async_engine, AsyncSessionLocal

# ============== SHARED TEST DATABASE ==============

_test_session_factory = None


async def get_test_session_factory():
    global _test_session_factory
    if _test_session_factory is None:
        _test_session_factory = async_sessionmaker(
            bind=async_engine, expire_on_commit=False
        )
    return _test_session_factory


# ============== DATABASE FIXTURES ==============


@pytest.fixture(scope="function", autouse=True)
async def reset_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(scope="function")
async def test_session():
    factory = await get_test_session_factory()
    async with factory() as session:
        yield session


@pytest.fixture(scope="function")
async def app(test_session):
    from sta.web.app import create_app
    from sta.database import get_db

    fastapi_app = create_app()

    async def override_get_db():
        yield test_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with patch("sta.database.get_session", lambda: test_session):
        yield fastapi_app


@pytest.fixture(scope="function")
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)


# ============== SAMPLE DATA FIXTURES ==============


@pytest.fixture
def sample_character_data():
    return {
        "name": "Test Captain",
        "species": "Human",
        "rank": "Captain",
        "role": "Commanding Officer",
        "attributes_json": json.dumps(
            {
                "control": 10,
                "daring": 9,
                "fitness": 8,
                "insight": 11,
                "presence": 12,
                "reason": 10,
            }
        ),
        "disciplines_json": json.dumps(
            {
                "command": 5,
                "conn": 3,
                "engineering": 2,
                "medicine": 2,
                "science": 3,
                "security": 4,
            }
        ),
        "talents_json": json.dumps(["Bold (Command)", "Inspirational"]),
        "focuses_json": json.dumps(["Leadership", "Tactics", "Diplomacy"]),
        "stress": 12,
        "stress_max": 12,
        "determination": 3,
        "determination_max": 3,
    }


@pytest.fixture
def sample_player_ship_data():
    return {
        "name": "USS Endeavour",
        "ship_class": "Constitution",
        "registry": "NCC-1895",
        "scale": 4,
        "systems_json": json.dumps(
            {
                "comms": 9,
                "computers": 10,
                "engines": 10,
                "sensors": 11,
                "structure": 9,
                "weapons": 10,
            }
        ),
        "departments_json": json.dumps(
            {
                "command": 3,
                "conn": 3,
                "engineering": 3,
                "medicine": 2,
                "science": 3,
                "security": 3,
            }
        ),
        "weapons_json": json.dumps(
            [
                {
                    "name": "Phaser Banks",
                    "weapon_type": "energy",
                    "damage": 7,
                    "range": "medium",
                    "qualities": ["versatile 2"],
                    "requires_calibration": False,
                }
            ]
        ),
        "talents_json": json.dumps(["Redundant Systems"]),
        "traits_json": json.dumps(["Federation Starship"]),
        "breaches_json": json.dumps([]),
        "shields": 10,
        "shields_max": 10,
        "resistance": 4,
        "has_reserve_power": True,
        "shields_raised": True,
        "weapons_armed": True,
    }


@pytest.fixture
def sample_enemy_ship_data():
    return {
        "name": "IKS Predator",
        "ship_class": "D7 Battlecruiser",
        "scale": 4,
        "systems_json": json.dumps(
            {
                "comms": 8,
                "computers": 8,
                "engines": 9,
                "sensors": 8,
                "structure": 10,
                "weapons": 11,
            }
        ),
        "departments_json": json.dumps(
            {
                "command": 2,
                "conn": 3,
                "engineering": 2,
                "medicine": 1,
                "science": 2,
                "security": 4,
            }
        ),
        "weapons_json": json.dumps(
            [
                {
                    "name": "Disruptor Cannons",
                    "weapon_type": "energy",
                    "damage": 8,
                    "range": "medium",
                }
            ]
        ),
        "talents_json": json.dumps([]),
        "traits_json": json.dumps(["Klingon Starship"]),
        "breaches_json": json.dumps([]),
        "shields": 9,
        "shields_max": 9,
        "resistance": 4,
        "has_reserve_power": False,
        "shields_raised": True,
        "weapons_armed": True,
        "crew_quality": "basic",
    }


@pytest.fixture
async def sample_campaign(test_session, sample_player_ship_data):
    player_ship = StarshipRecord(**sample_player_ship_data)
    test_session.add(player_ship)
    await test_session.flush()
    campaign = CampaignRecord(
        campaign_id="test-campaign-001",
        name="Test Campaign",
        active_ship_id=player_ship.id,
        is_active=True,
    )
    test_session.add(campaign)
    await test_session.flush()

    players = []
    positions = ["captain", "tactical", "conn", "engineering", "science"]
    for i, pos in enumerate(positions):
        player = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name=f"Player {i + 1}",
            session_token=f"test-token-{i + 1}",
            position=pos,
            is_gm=(i == 0),
            is_active=True,
        )
        test_session.add(player)

    await test_session.commit()
    return {"campaign": campaign, "player_ship": player_ship, "players": players}


@pytest.fixture
async def sample_encounter(
    test_session,
    sample_character_data,
    sample_player_ship_data,
    sample_enemy_ship_data,
    sample_campaign,
):
    campaign = sample_campaign["campaign"]
    character = CharacterRecord(**sample_character_data)
    test_session.add(character)
    player_ship = StarshipRecord(**sample_player_ship_data)
    test_session.add(player_ship)
    enemy_ship = StarshipRecord(**sample_enemy_ship_data)
    test_session.add(enemy_ship)
    await test_session.flush()
    encounter = EncounterRecord(
        encounter_id="test-001",
        name="Test",
        campaign_id=campaign.id,
        player_ship_id=player_ship.id,
        player_character_id=character.id,
        enemy_ship_ids_json=json.dumps([enemy_ship.id]),
        round=1,
        current_turn="player",
        is_active=True,
        active_effects_json="[]",
    )
    test_session.add(encounter)
    await test_session.commit()
    return {
        "encounter": encounter,
        "campaign": campaign,
        "character": character,
        "player_ship": player_ship,
        "enemy_ship": enemy_ship,
    }


@pytest.fixture
async def multiplayer_encounter(test_session, sample_campaign, sample_enemy_ship_data):
    campaign = sample_campaign["campaign"]
    player_ship = sample_campaign["player_ship"]
    players = sample_campaign["players"]
    enemy_ship = StarshipRecord(**sample_enemy_ship_data)
    test_session.add(enemy_ship)
    await test_session.flush()
    encounter = EncounterRecord(
        encounter_id="test-multiplayer-001",
        name="Multi",
        campaign_id=campaign.id,
        player_ship_id=player_ship.id,
        enemy_ship_ids_json=json.dumps([enemy_ship.id]),
        round=1,
        current_turn="player",
        is_active=True,
        players_turns_used_json="{}",
        active_effects_json="[]",
    )
    test_session.add(encounter)
    await test_session.commit()
    return {
        "encounter": encounter,
        "campaign": campaign,
        "player_ship": player_ship,
        "enemy_ship": enemy_ship,
        "players": players,
    }


# ============== HELPER FIXTURES ==============


@pytest.fixture
def execute_action(client):
    def _execute(encounter_id, action_name, role="player", **kwargs):
        return client.post(
            f"/api/execute-action",
            json={
                "encounter_id": encounter_id,
                "action_name": action_name,
                "role": role,
                **kwargs,
            },
        )

    return _execute


@pytest.fixture
def claim_turn(client):
    def _claim(encounter_id, player_id):
        return client.post(
            f"/api/encounter/{encounter_id}/claim-turn", json={"player_id": player_id}
        )

    return _claim


@pytest.fixture
def release_turn(client):
    def _release(encounter_id, force=False):
        return client.post(
            f"/api/encounter/{encounter_id}/release-turn", json={"force": force}
        )

    return _release


@pytest.fixture
def next_turn(client):
    def _next(encounter_id):
        return client.post(f"/api/encounter/{encounter_id}/next-turn")

    return _next


@pytest.fixture
def get_encounter_status(client):
    def _status(encounter_id, role="player"):
        return client.get(f"/api/encounter/{encounter_id}/status?role={role}")

    return _status


@pytest.fixture
def get_combat_log(client):
    def _get(encounter_id, limit=None, since_id=None, round_filter=None):
        url = f"/api/encounter/{encounter_id}/combat-log"
        params = {}
        if limit is not None:
            params["limit"] = limit
        if since_id is not None:
            params["since_id"] = since_id
        if round_filter is not None:
            params["round_filter"] = round_filter
        return client.get(url, params=params)

    return _get


@pytest.fixture
async def scene(test_session, sample_campaign):
    campaign = sample_campaign["campaign"]
    scene = SceneRecord(
        campaign_id=campaign.id,
        name="Test Scene",
        scene_type="narrative",
        status="draft",
    )
    test_session.add(scene)
    await test_session.commit()
    return scene


@pytest.fixture
async def gm_session(sample_campaign):
    for p in sample_campaign["players"]:
        if p.is_gm:
            return p
    return sample_campaign["players"][0]


@pytest.fixture
def mock_dice_success():
    with patch("random.randint", return_value=1):
        yield


@pytest.fixture
def mock_dice_failure():
    with patch("random.randint", return_value=20):
        yield
