"""Tests for VTT Character and Ship Import/Export API endpoints."""

import json
import pytest
from sta.database.vtt_schema import VTTCharacterRecord, VTTShipRecord


@pytest.fixture
def sample_vtt_character(test_session):
    """Create a sample VTT character for export/import tests."""
    char = VTTCharacterRecord(
        name="Captain Janeway",
        species="Human",
        rank="Captain",
        role="Command",
        attributes_json=json.dumps(
            {
                "control": 9,
                "fitness": 8,
                "daring": 10,
                "insight": 9,
                "presence": 11,
                "reason": 10,
            }
        ),
        disciplines_json=json.dumps(
            {
                "command": 4,
                "conn": 2,
                "engineering": 2,
                "medicine": 1,
                "science": 2,
                "security": 2,
            }
        ),
        talents_json=json.dumps(["Command Presence", "Resolve"]),
        focuses_json=json.dumps(["Astrophysics", "Photonics"]),
        stress=4,
        stress_max=5,
        determination=2,
        determination_max=3,
        character_type="main",
        pronouns="she/her",
        description="Captain of Voyager",
        values_json=json.dumps(["Integrity", "Discovery"]),
        equipment_json=json.dumps(["Commbadge", "Tricorder"]),
        environment="Indiana",
        upbringing="Military Academy",
        career_path="Starfleet",
    )

    test_session.add(char)
    test_session.commit()

    return char


@pytest.fixture
def sample_vtt_ship(test_session):
    """Create a sample VTT ship for export/import tests."""
    ship = VTTShipRecord(
        name="USS Voyager",
        ship_class="Intrepid-class",
        ship_registry="NCC-74656",
        scale=5,
        systems_json=json.dumps(
            {
                "comms": 8,
                "computers": 10,
                "engines": 11,
                "sensors": 10,
                "structure": 8,
                "weapons": 8,
            }
        ),
        departments_json=json.dumps(
            {
                "command": 2,
                "conn": 4,
                "engineering": 3,
                "medicine": 3,
                "science": 4,
                "security": 2,
            }
        ),
        weapons_json=json.dumps(
            [
                {
                    "name": "Phasers",
                    "weapon_type": "energy",
                    "damage": 5,
                    "range": "long",
                    "qualities": ["reload"],
                    "requires_calibration": False,
                }
            ]
        ),
        talents_json=json.dumps(["Efficient Repairs"]),
        traits_json=json.dumps(["Intrepid-class"]),
        breaches_json=json.dumps([]),
        shields=35,
        shields_max=35,
        resistance=5,
        has_reserve_power=True,
        shields_raised=False,
        weapons_armed=False,
        crew_quality=None,
    )

    test_session.add(ship)
    test_session.commit()

    return ship


class TestVTTCharacterExportImport:
    """Tests for VTT Character export/import endpoints."""

    def test_export_character(self, client, sample_vtt_character):
        """Test exporting a single VTT character."""
        response = client.get(f"/api/vtt/characters/{sample_vtt_character.id}/export")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["name"] == "Captain Janeway"
        assert data["species"] == "Human"
        assert data["rank"] == "Captain"
        assert data["role"] == "Command"
        assert data["pronouns"] == "she/her"
        assert data["description"] == "Captain of Voyager"
        assert "attributes" in data
        assert "disciplines" in data
        assert data["attributes"]["control"] == 9
        assert data["disciplines"]["command"] == 4

    def test_export_character_not_found(self, client):
        """Test exporting non-existent character returns 404."""
        response = client.get("/api/vtt/characters/99999/export")
        assert response.status_code == 404

    def test_import_character(self, client, test_session):
        """Test importing a new VTT character."""
        import_data = {
            "name": "New Character",
            "species": "Vulcan",
            "rank": "Lieutenant",
            "role": "Science",
            "attributes": {
                "control": 10,
                "fitness": 8,
                "daring": 8,
                "insight": 11,
                "presence": 9,
                "reason": 12,
            },
            "disciplines": {
                "command": 1,
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 5,
                "security": 1,
            },
            "stress": 2,
            "stress_max": 5,
            "determination": 2,
            "determination_max": 3,
            "talents": ["Analytical Mind"],
            "focuses": ["Quantum Mechanics"],
        }

        response = client.post(
            "/api/vtt/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "New Character"
        assert data["species"] == "Vulcan"
        assert data["rank"] == "Lieutenant"

    def test_import_character_in_container(self, client, test_session):
        """Test importing character wrapped in 'characters' key."""
        import_data = {
            "characters": [
                {
                    "name": "Container Character",
                    "species": "Human",
                    "attributes": {
                        "control": 8,
                        "fitness": 8,
                        "daring": 8,
                        "insight": 8,
                        "presence": 8,
                        "reason": 8,
                    },
                    "disciplines": {
                        "command": 1,
                        "conn": 1,
                        "engineering": 1,
                        "medicine": 1,
                        "science": 1,
                        "security": 1,
                    },
                }
            ]
        }

        response = client.post(
            "/api/vtt/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "Container Character"

    def test_import_character_invalid_attribute(self, client, test_session):
        """Test importing character with invalid attribute fails."""
        import_data = {
            "name": "Invalid Character",
            "species": "Human",
            "attributes": {
                "control": 15,  # Invalid - too high
                "fitness": 8,
                "daring": 8,
                "insight": 8,
                "presence": 8,
                "reason": 8,
            },
            "disciplines": {
                "command": 1,
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 1,
                "security": 1,
            },
        }

        response = client.post(
            "/api/vtt/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Attribute control must be between 7-12" in response.data.decode()

    def test_import_character_invalid_discipline(self, client, test_session):
        """Test importing character with invalid discipline fails."""
        import_data = {
            "name": "Invalid Character",
            "species": "Human",
            "attributes": {
                "control": 8,
                "fitness": 8,
                "daring": 8,
                "insight": 8,
                "presence": 8,
                "reason": 8,
            },
            "disciplines": {
                "command": 10,  # Invalid - too high
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 1,
                "security": 1,
            },
        }

        response = client.post(
            "/api/vtt/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Discipline command must be between 0-5" in response.data.decode()

    def test_import_character_invalid_stress(self, client, test_session):
        """Test importing character with invalid stress fails."""
        import_data = {
            "name": "Invalid Character",
            "species": "Human",
            "attributes": {
                "control": 8,
                "fitness": 8,
                "daring": 8,
                "insight": 8,
                "presence": 8,
                "reason": 8,
            },
            "disciplines": {
                "command": 1,
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 1,
                "security": 1,
            },
            "stress": 10,  # Invalid - higher than stress_max
            "stress_max": 5,
        }

        response = client.post(
            "/api/vtt/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Stress must be between 0-5" in response.data.decode()

    def test_import_character_no_data(self, client, test_session):
        """Test importing with no data fails."""
        response = client.post(
            "/api/vtt/characters/import",
            data=json.dumps(None),
            content_type="application/json",
        )

        assert response.status_code == 400


class TestVTTShipExportImport:
    """Tests for VTT Ship export/import endpoints."""

    def test_export_ship(self, client, sample_vtt_ship):
        """Test exporting a single VTT ship."""
        response = client.get(f"/api/vtt/ships/{sample_vtt_ship.id}/export")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["name"] == "USS Voyager"
        assert data["ship_class"] == "Intrepid-class"
        assert data["ship_registry"] == "NCC-74656"
        assert data["scale"] == 5
        assert "systems" in data
        assert "departments" in data
        assert data["systems"]["comms"] == 8
        assert data["systems"]["engines"] == 11
        assert data["departments"]["conn"] == 4

    def test_export_ship_not_found(self, client):
        """Test exporting non-existent ship returns 404."""
        response = client.get("/api/vtt/ships/99999/export")
        assert response.status_code == 404

    def test_import_ship(self, client, test_session):
        """Test importing a new VTT ship."""
        import_data = {
            "name": "USS Enterprise",
            "ship_class": "Constitution-class",
            "ship_registry": "NCC-1701",
            "scale": 6,
            "systems": {
                "comms": 9,
                "computers": 10,
                "engines": 10,
                "sensors": 9,
                "structure": 9,
                "weapons": 9,
            },
            "departments": {
                "command": 3,
                "conn": 3,
                "engineering": 3,
                "medicine": 2,
                "science": 3,
                "security": 2,
            },
            "shields": 40,
            "shields_max": 40,
            "resistance": 6,
            "has_reserve_power": True,
        }

        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "USS Enterprise"
        assert data["ship_class"] == "Constitution-class"
        assert data["ship_registry"] == "NCC-1701"
        assert data["scale"] == 6

    def test_import_ship_in_container(self, client, test_session):
        """Test importing ship wrapped in 'ships' key."""
        import_data = {
            "ships": [
                {
                    "name": "USS Discovery",
                    "ship_class": "Crossfield-class",
                    "scale": 5,
                    "systems": {
                        "comms": 8,
                        "computers": 10,
                        "engines": 9,
                        "sensors": 10,
                        "structure": 8,
                        "weapons": 8,
                    },
                    "departments": {
                        "command": 2,
                        "conn": 3,
                        "engineering": 3,
                        "medicine": 2,
                        "science": 4,
                        "security": 2,
                    },
                }
            ]
        }

        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "USS Discovery"

    def test_import_ship_invalid_system(self, client, test_session):
        """Test importing ship with invalid system value fails."""
        import_data = {
            "name": "Invalid Ship",
            "ship_class": "Test-class",
            "scale": 4,
            "systems": {
                "comms": 15,  # Invalid - too high
                "computers": 10,
                "engines": 10,
                "sensors": 9,
                "structure": 9,
                "weapons": 9,
            },
            "departments": {
                "command": 3,
                "conn": 3,
                "engineering": 3,
                "medicine": 2,
                "science": 3,
                "security": 2,
            },
        }

        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "System comms must be between 7-12" in response.data.decode()

    def test_import_ship_invalid_department(self, client, test_session):
        """Test importing ship with invalid department value fails."""
        import_data = {
            "name": "Invalid Ship",
            "ship_class": "Test-class",
            "scale": 4,
            "systems": {
                "comms": 8,
                "computers": 10,
                "engines": 10,
                "sensors": 9,
                "structure": 9,
                "weapons": 9,
            },
            "departments": {
                "command": 10,  # Invalid - too high
                "conn": 3,
                "engineering": 3,
                "medicine": 2,
                "science": 3,
                "security": 2,
            },
        }

        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Department command must be between 0-5" in response.data.decode()

    def test_import_ship_invalid_scale(self, client, test_session):
        """Test importing ship with invalid scale fails."""
        import_data = {
            "name": "Invalid Ship",
            "ship_class": "Test-class",
            "scale": 10,  # Invalid - too high
            "systems": {
                "comms": 8,
                "computers": 10,
                "engines": 10,
                "sensors": 9,
                "structure": 9,
                "weapons": 9,
            },
            "departments": {
                "command": 3,
                "conn": 3,
                "engineering": 3,
                "medicine": 2,
                "science": 3,
                "security": 2,
            },
        }

        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Scale must be between 1-7" in response.data.decode()

    def test_import_ship_invalid_shields(self, client, test_session):
        """Test importing ship with invalid shields fails."""
        import_data = {
            "name": "Invalid Ship",
            "ship_class": "Test-class",
            "scale": 4,
            "systems": {
                "comms": 8,
                "computers": 10,
                "engines": 10,
                "sensors": 9,
                "structure": 9,
                "weapons": 9,
            },
            "departments": {
                "command": 3,
                "conn": 3,
                "engineering": 3,
                "medicine": 2,
                "science": 3,
                "security": 2,
            },
            "shields": 50,  # Invalid - higher than shields_max
            "shields_max": 30,
        }

        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Shields must be between 0-30" in response.data.decode()

    def test_import_ship_no_data(self, client, test_session):
        """Test importing with no data fails."""
        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(None),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_import_ship_with_registry_key(self, client, test_session):
        """Test importing ship using 'registry' key instead of 'ship_registry'."""
        import_data = {
            "name": "USS Enterprise",
            "ship_class": "Constitution-class",
            "registry": "NCC-1701",  # Using 'registry' key
            "scale": 6,
            "systems": {
                "comms": 9,
                "computers": 10,
                "engines": 10,
                "sensors": 9,
                "structure": 9,
                "weapons": 9,
            },
            "departments": {
                "command": 3,
                "conn": 3,
                "engineering": 3,
                "medicine": 2,
                "science": 3,
                "security": 2,
            },
        }

        response = client.post(
            "/api/vtt/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["ship_registry"] == "NCC-1701"
