"""
Tests for ship visibility in STA Starship Simulator.

These tests verify that:
- Players cannot see enemy ships in hidden terrain (dust clouds, nebulae)
- Players CAN see enemies in open terrain
- Players CAN see enemies in same hex (even in hidden terrain)
- GMs cannot see player ships in hidden terrain
- GMs CAN see player if enemy is in same hex (detected)
"""

import json
import pytest
from sta.database.schema import EncounterRecord, StarshipRecord


class TestAPIVisibility:
    """Tests for visibility via API endpoints."""

    def test_status_api_filters_hidden_enemies_dust_cloud(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/status filters enemies in dust cloud for players."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with dust cloud at enemy position
        tactical_map = {
            "radius": 3,
            "tiles": [
                {"coord": {"q": 2, "r": 0}, "terrain": "dust_cloud"}
            ]
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position enemy in dust cloud
        ship_positions = {
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 2, "r": 0}  # In dust cloud
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request status as player
        response = client.get(f"/api/encounter/{encounter.encounter_id}/status?role=player")
        assert response.status_code == 200

        data = response.get_json()

        # ships_info should NOT contain the hidden enemy
        ships_info = data.get("ships_info", [])
        enemy_names = [s.get("name") for s in ships_info]
        assert enemy_ship.name not in enemy_names

    def test_status_api_filters_hidden_enemies_dense_nebula(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/status filters enemies in dense nebula for players."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with dense nebula at enemy position
        tactical_map = {
            "radius": 3,
            "tiles": [
                {"coord": {"q": 2, "r": 0}, "terrain": "dense_nebula"}
            ]
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position enemy in dense nebula
        ship_positions = {
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 2, "r": 0}  # In dense nebula
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request status as player
        response = client.get(f"/api/encounter/{encounter.encounter_id}/status?role=player")
        assert response.status_code == 200

        data = response.get_json()

        # ships_info should NOT contain the hidden enemy
        ships_info = data.get("ships_info", [])
        enemy_names = [s.get("name") for s in ships_info]
        assert enemy_ship.name not in enemy_names

    def test_status_api_shows_enemy_in_open_terrain(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/status shows enemies in open terrain to players."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with NO fog terrain
        tactical_map = {
            "radius": 3,
            "tiles": []  # Open terrain
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position enemy in open terrain
        ship_positions = {
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 2, "r": 0}  # Open terrain
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request status as player
        response = client.get(f"/api/encounter/{encounter.encounter_id}/status?role=player")
        assert response.status_code == 200

        data = response.get_json()

        # ships_info SHOULD contain the visible enemy
        ships_info = data.get("ships_info", [])
        enemy_names = [s.get("name") for s in ships_info]
        assert enemy_ship.name in enemy_names

    def test_status_api_shows_enemy_in_same_hex(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/status shows enemies in same hex even in fog."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with dust cloud
        tactical_map = {
            "radius": 3,
            "tiles": [
                {"coord": {"q": 1, "r": 1}, "terrain": "dust_cloud"}
            ]
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position both ships in same hex (in dust cloud)
        ship_positions = {
            "player": {"q": 1, "r": 1},
            "enemy_0": {"q": 1, "r": 1}  # Same hex as player
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request status as player
        response = client.get(f"/api/encounter/{encounter.encounter_id}/status?role=player")
        assert response.status_code == 200

        data = response.get_json()

        # ships_info SHOULD contain the enemy (same hex = visible)
        ships_info = data.get("ships_info", [])
        enemy_names = [s.get("name") for s in ships_info]
        assert enemy_ship.name in enemy_names

    def test_status_api_shows_all_to_gm(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/status shows all enemies to GM."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with dust cloud at enemy position
        tactical_map = {
            "radius": 3,
            "tiles": [
                {"coord": {"q": 2, "r": 0}, "terrain": "dust_cloud"}
            ]
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position enemy in dust cloud
        ship_positions = {
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 2, "r": 0}  # In dust cloud
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request status as GM
        response = client.get(f"/api/encounter/{encounter.encounter_id}/status?role=gm")
        assert response.status_code == 200

        data = response.get_json()

        # ships_info SHOULD contain the hidden enemy (GM sees all)
        ships_info = data.get("ships_info", [])
        enemy_names = [s.get("name") for s in ships_info]
        assert enemy_ship.name in enemy_names


class TestMapAPIVisibility:
    """Tests for visibility via map API endpoint."""

    def test_map_api_filters_hidden_enemies(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/map filters hidden enemies for players."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with dust cloud at enemy position
        tactical_map = {
            "radius": 3,
            "tiles": [
                {"coord": {"q": 2, "r": 0}, "terrain": "dust_cloud"}
            ]
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position enemy in dust cloud
        ship_positions = {
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 2, "r": 0}  # In dust cloud
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request map as player
        response = client.get(f"/api/encounter/{encounter.encounter_id}/map?role=player")
        assert response.status_code == 200

        data = response.get_json()

        # ship_positions should NOT contain the hidden enemy
        positions = data.get("ship_positions", [])
        ship_names = [s.get("name") for s in positions]
        assert enemy_ship.name not in ship_names

    def test_map_api_shows_enemy_in_open_terrain(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/map shows enemies in open terrain."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with NO fog terrain
        tactical_map = {
            "radius": 3,
            "tiles": []  # Open terrain
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position enemy in open terrain
        ship_positions = {
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 2, "r": 0}  # Open terrain
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request map as player
        response = client.get(f"/api/encounter/{encounter.encounter_id}/map?role=player")
        assert response.status_code == 200

        data = response.get_json()

        # ship_positions SHOULD contain the visible enemy
        positions = data.get("ship_positions", [])
        ship_names = [s.get("name") for s in positions]
        assert enemy_ship.name in ship_names

    def test_map_api_shows_all_to_gm(self, client, sample_encounter, test_session):
        """Test that /api/encounter/<id>/map shows all enemies to GM."""
        encounter = sample_encounter["encounter"]
        enemy_ship = sample_encounter["enemy_ship"]

        # Set up tactical map with dust cloud at enemy position
        tactical_map = {
            "radius": 3,
            "tiles": [
                {"coord": {"q": 2, "r": 0}, "terrain": "dust_cloud"}
            ]
        }
        encounter.tactical_map_json = json.dumps(tactical_map)

        # Position enemy in dust cloud
        ship_positions = {
            "player": {"q": 0, "r": 0},
            "enemy_0": {"q": 2, "r": 0}  # In dust cloud
        }
        encounter.ship_positions_json = json.dumps(ship_positions)
        test_session.commit()

        # Request map as GM
        response = client.get(f"/api/encounter/{encounter.encounter_id}/map?role=gm")
        assert response.status_code == 200

        data = response.get_json()

        # ship_positions SHOULD contain the hidden enemy (GM sees all)
        positions = data.get("ship_positions", [])
        ship_names = [s.get("name") for s in positions]
        assert enemy_ship.name in ship_names
