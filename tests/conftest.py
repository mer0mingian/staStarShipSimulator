"""
Pytest fixtures for STA Starship Simulator testing.

Provides test database, Flask app client, and sample data for testing
turn order, actions, and combat logging.
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from sta.database.schema import (
    Base,
    CharacterRecord,
    StarshipRecord,
    EncounterRecord,
    CombatLogRecord,
    CampaignRecord,
    CampaignPlayerRecord,
)


# ============== SHARED TEST DATABASE ==============

# Create a module-level test engine that will be shared
_test_engine = None
_test_session_factory = None


def get_test_engine():
    """Get or create the shared test engine."""
    global _test_engine
    if _test_engine is None:
        _test_engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(_test_engine)
    return _test_engine


def get_test_session_factory():
    """Get or create the shared session factory."""
    global _test_session_factory
    if _test_session_factory is None:
        _test_session_factory = sessionmaker(bind=get_test_engine())
    return _test_session_factory


def reset_test_database():
    """Reset the test database (drop and recreate all tables)."""
    global _test_engine, _test_session_factory
    if _test_engine:
        Base.metadata.drop_all(_test_engine)
        Base.metadata.create_all(_test_engine)


def mock_get_session():
    """Mock get_session that returns a session from the test database."""
    return get_test_session_factory()()


# ============== DATABASE FIXTURES ==============

@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Reset the database before each test."""
    reset_test_database()
    yield


@pytest.fixture(scope="function")
def test_session():
    """Create a database session for testing."""
    session = mock_get_session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def app():
    """Create a Flask app configured for testing."""
    # Patch get_session in all the places it's used
    with patch('sta.database.get_session', mock_get_session):
        with patch('sta.database.db.get_session', mock_get_session):
            with patch('sta.web.routes.api.get_session', mock_get_session):
                with patch('sta.web.routes.encounters.get_session', mock_get_session):
                    with patch('sta.web.routes.campaigns.get_session', mock_get_session):
                        # Import and create app after patching
                        from sta.web.app import create_app
                        flask_app = create_app()
                        flask_app.config["TESTING"] = True
                        yield flask_app


@pytest.fixture(scope="function")
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


# ============== SAMPLE DATA FIXTURES ==============

@pytest.fixture
def sample_character_data():
    """Sample character data for tests."""
    return {
        "name": "Test Captain",
        "species": "Human",
        "rank": "Captain",
        "role": "Commanding Officer",
        "attributes_json": json.dumps({
            "control": 10,
            "daring": 9,
            "fitness": 8,
            "insight": 11,
            "presence": 12,
            "reason": 10,
        }),
        "disciplines_json": json.dumps({
            "command": 5,
            "conn": 3,
            "engineering": 2,
            "medicine": 2,
            "science": 3,
            "security": 4,
        }),
        "talents_json": json.dumps(["Bold (Command)", "Inspirational"]),
        "focuses_json": json.dumps(["Leadership", "Tactics", "Diplomacy"]),
        "stress": 12,
        "stress_max": 12,
        "determination": 3,
        "determination_max": 3,
    }


@pytest.fixture
def sample_player_ship_data():
    """Sample player ship data for tests."""
    return {
        "name": "USS Endeavour",
        "ship_class": "Constitution",
        "registry": "NCC-1895",
        "scale": 4,
        "systems_json": json.dumps({
            "comms": 9,
            "computers": 10,
            "engines": 10,
            "sensors": 11,
            "structure": 9,
            "weapons": 10,
        }),
        "departments_json": json.dumps({
            "command": 3,
            "conn": 3,
            "engineering": 3,
            "medicine": 2,
            "science": 3,
            "security": 3,
        }),
        "weapons_json": json.dumps([
            {
                "name": "Phaser Banks",
                "weapon_type": "energy",
                "damage": 7,
                "range": "medium",
                "qualities": ["versatile 2"],
                "requires_calibration": False,
            },
            {
                "name": "Photon Torpedoes",
                "weapon_type": "torpedo",
                "damage": 5,
                "range": "long",
                "qualities": ["high yield"],
                "requires_calibration": True,
            },
        ]),
        "talents_json": json.dumps(["Redundant Systems", "Improved Warp Drive"]),
        "traits_json": json.dumps(["Federation Starship"]),
        "breaches_json": json.dumps([]),
        "shields": 10,
        "shields_max": 10,
        "resistance": 4,
        "has_reserve_power": True,
        "shields_raised": True,
        "weapons_armed": True,
        "crew_quality": None,
    }


@pytest.fixture
def sample_enemy_ship_data():
    """Sample enemy ship data for tests."""
    return {
        "name": "IKS Predator",
        "ship_class": "D7 Battlecruiser",
        "registry": None,
        "scale": 4,
        "systems_json": json.dumps({
            "comms": 8,
            "computers": 8,
            "engines": 9,
            "sensors": 8,
            "structure": 10,
            "weapons": 11,
        }),
        "departments_json": json.dumps({
            "command": 2,
            "conn": 3,
            "engineering": 2,
            "medicine": 1,
            "science": 2,
            "security": 4,
        }),
        "weapons_json": json.dumps([
            {
                "name": "Disruptor Cannons",
                "weapon_type": "energy",
                "damage": 8,
                "range": "medium",
                "qualities": ["vicious 1"],
                "requires_calibration": False,
            },
        ]),
        "talents_json": json.dumps([]),
        "traits_json": json.dumps(["Klingon Starship"]),
        "breaches_json": json.dumps([]),
        "shields": 9,
        "shields_max": 9,
        "resistance": 4,
        "has_reserve_power": False,  # NPCs don't have reserve power
        "shields_raised": True,
        "weapons_armed": True,
        "crew_quality": "basic",
    }


@pytest.fixture
def sample_encounter(test_session, sample_character_data, sample_player_ship_data, sample_enemy_ship_data):
    """Create a sample encounter with ships and character."""
    # Create character
    character = CharacterRecord(**sample_character_data)
    test_session.add(character)
    test_session.flush()

    # Create player ship
    player_ship = StarshipRecord(**sample_player_ship_data)
    test_session.add(player_ship)
    test_session.flush()

    # Create enemy ship
    enemy_ship = StarshipRecord(**sample_enemy_ship_data)
    test_session.add(enemy_ship)
    test_session.flush()

    # Create encounter
    encounter = EncounterRecord(
        encounter_id="test-encounter-001",
        name="Test Combat",
        description="A test combat encounter",
        player_ship_id=player_ship.id,
        player_character_id=character.id,
        player_position="captain",
        enemy_ship_ids_json=json.dumps([enemy_ship.id]),
        momentum=2,
        threat=3,
        round=1,
        current_turn="player",
        is_active=True,
        ships_turns_used_json=json.dumps({}),
        player_turns_used=0,
        player_turns_total=4,  # Scale 4 ship
        players_turns_used_json=json.dumps({}),
        current_player_id=None,
        turn_claimed_at=None,
        active_effects_json=json.dumps([]),
        tactical_map_json=json.dumps({"radius": 3, "tiles": []}),
        ship_positions_json=json.dumps({
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 1, "r": 0},  # Medium range (1 hex)
        }),
    )
    test_session.add(encounter)
    test_session.commit()

    return {
        "encounter": encounter,
        "character": character,
        "player_ship": player_ship,
        "enemy_ship": enemy_ship,
    }


@pytest.fixture
def sample_campaign(test_session, sample_player_ship_data):
    """Create a sample campaign with multiple players."""
    # Create player ship for campaign
    player_ship = StarshipRecord(**sample_player_ship_data)
    test_session.add(player_ship)
    test_session.flush()

    # Create campaign
    campaign = CampaignRecord(
        campaign_id="test-campaign-001",
        name="Test Campaign",
        description="A test campaign",
        active_ship_id=player_ship.id,
        is_active=True,
    )
    test_session.add(campaign)
    test_session.flush()

    # Create players
    players = []
    positions = ["captain", "tactical", "conn", "engineering", "science"]
    for i, pos in enumerate(positions):
        player = CampaignPlayerRecord(
            campaign_id=campaign.id,
            character_id=None,  # No linked character for simplicity
            player_name=f"Player {i+1}",
            session_token=f"test-token-{i+1}",
            position=pos,
            is_gm=(i == 0),  # First player is GM
            is_active=True,
        )
        test_session.add(player)
        players.append(player)

    test_session.commit()

    return {
        "campaign": campaign,
        "player_ship": player_ship,
        "players": players,
    }


@pytest.fixture
def multiplayer_encounter(test_session, sample_campaign, sample_enemy_ship_data):
    """Create a multiplayer encounter with campaign players."""
    campaign = sample_campaign["campaign"]
    player_ship = sample_campaign["player_ship"]
    players = sample_campaign["players"]

    # Create enemy ship
    enemy_ship = StarshipRecord(**sample_enemy_ship_data)
    test_session.add(enemy_ship)
    test_session.flush()

    # Create multiplayer encounter
    encounter = EncounterRecord(
        encounter_id="test-multiplayer-001",
        name="Multiplayer Test Combat",
        description="A multiplayer test combat encounter",
        campaign_id=campaign.id,
        player_ship_id=player_ship.id,
        player_character_id=None,  # Multiplayer mode
        player_position="captain",
        enemy_ship_ids_json=json.dumps([enemy_ship.id]),
        momentum=2,
        threat=3,
        round=1,
        current_turn="player",
        is_active=True,
        ships_turns_used_json=json.dumps({}),
        player_turns_used=0,
        player_turns_total=len(players),  # One turn per player
        players_turns_used_json=json.dumps({}),
        current_player_id=None,
        turn_claimed_at=None,
        active_effects_json=json.dumps([]),
        tactical_map_json=json.dumps({"radius": 3, "tiles": []}),
        ship_positions_json=json.dumps({
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 1, "r": 0},
        }),
    )
    test_session.add(encounter)
    test_session.commit()

    return {
        "encounter": encounter,
        "campaign": campaign,
        "player_ship": player_ship,
        "enemy_ship": enemy_ship,
        "players": players,
    }


# ============== DICE MOCKING FIXTURES ==============

@pytest.fixture
def mock_dice_success():
    """Mock dice to always succeed (roll 1s for criticals)."""
    def mock_randint(a, b):
        return 1  # Natural 1 = critical success (2 successes)

    with patch('random.randint', mock_randint):
        yield


@pytest.fixture
def mock_dice_failure():
    """Mock dice to always fail (roll 20s for complications)."""
    def mock_randint(a, b):
        return 20  # Natural 20 = complication + failure

    with patch('random.randint', mock_randint):
        yield


@pytest.fixture
def mock_dice_average():
    """Mock dice to roll average (success depends on target number)."""
    def mock_randint(a, b):
        return 10  # Middle roll - succeeds if target >= 10

    with patch('random.randint', mock_randint):
        yield


@pytest.fixture
def mock_dice_controlled():
    """Provide a context manager for controlling specific dice results."""
    class DiceController:
        def __init__(self):
            self.results = []
            self.index = 0

        def set_results(self, results):
            """Set the sequence of dice results to return."""
            self.results = results
            self.index = 0

        def __call__(self, a, b):
            if self.index < len(self.results):
                result = self.results[self.index]
                self.index += 1
                return result
            return random.randint(a, b)  # Fall back to random

    controller = DiceController()
    with patch('random.randint', controller):
        yield controller


# ============== HELPER FIXTURES ==============

@pytest.fixture
def execute_action(client):
    """Helper function to execute an action via API."""
    def _execute(encounter_id, action_name, role="player", **kwargs):
        data = {
            "action_name": action_name,
            "role": role,
            **kwargs,
        }
        response = client.post(
            f"/api/encounter/{encounter_id}/execute-action",
            json=data,
            content_type="application/json",
        )
        return response

    return _execute


@pytest.fixture
def claim_turn(client):
    """Helper function to claim a turn via API."""
    def _claim(encounter_id, player_id):
        response = client.post(
            f"/api/encounter/{encounter_id}/claim-turn",
            json={"player_id": player_id},
            content_type="application/json",
        )
        return response

    return _claim


@pytest.fixture
def release_turn(client):
    """Helper function to release a turn via API."""
    def _release(encounter_id, force=False):
        response = client.post(
            f"/api/encounter/{encounter_id}/release-turn",
            json={"force": force},
            content_type="application/json",
        )
        return response

    return _release


@pytest.fixture
def next_turn(client):
    """Helper function to pass/end turn via API."""
    def _next(encounter_id):
        response = client.post(
            f"/api/encounter/{encounter_id}/next-turn",
            content_type="application/json",
        )
        return response

    return _next


@pytest.fixture
def get_encounter_status(client):
    """Helper function to get encounter status via API."""
    def _status(encounter_id, role="player"):
        response = client.get(
            f"/api/encounter/{encounter_id}/status?role={role}",
        )
        return response

    return _status


@pytest.fixture
def get_combat_log(client):
    """Helper function to get combat log via API."""
    def _log(encounter_id, since_id=None, round_filter=None, limit=50):
        params = [f"limit={limit}"]
        if since_id:
            params.append(f"since_id={since_id}")
        if round_filter is not None:
            params.append(f"round={round_filter}")
        query = "&".join(params)
        response = client.get(f"/api/encounter/{encounter_id}/combat-log?{query}")
        return response

    return _log
