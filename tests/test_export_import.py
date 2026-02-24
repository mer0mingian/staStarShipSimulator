"""Tests for export/import API endpoints."""

import json
import pytest


@pytest.fixture
def sample_characters(test_session):
    """Create sample characters for export/import tests."""
    from sta.database.schema import CharacterRecord

    chars = [
        CharacterRecord(
            name="Captain Picard",
            species="Human",
            rank="Captain",
            role="Command",
            attributes_json=json.dumps(
                {
                    "control": 8,
                    "fitness": 7,
                    "daring": 9,
                    "insight": 10,
                    "presence": 11,
                    "reason": 10,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 4,
                    "conn": 2,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 2,
                    "security": 2,
                }
            ),
            talents_json=json.dumps(["Talent 1", "Talent 2"]),
            focuses_json=json.dumps(["Diplomacy", "History"]),
            stress=4,
            stress_max=5,
            determination=2,
            determination_max=3,
            character_type="main",
            pronouns="he/him",
            description="Captain of the Enterprise",
        ),
        CharacterRecord(
            name="Commander Riker",
            species="Human",
            rank="Commander",
            role="First Officer",
            attributes_json=json.dumps(
                {
                    "control": 9,
                    "fitness": 9,
                    "daring": 10,
                    "insight": 8,
                    "presence": 10,
                    "reason": 8,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 1,
                    "security": 3,
                }
            ),
            stress=3,
            stress_max=5,
            determination=1,
            determination_max=3,
            character_type="support",
        ),
    ]

    for char in chars:
        test_session.add(char)
    test_session.commit()

    return chars


@pytest.fixture
def sample_npcs(test_session):
    """Create sample NPCs for export/import tests."""
    from sta.database.schema import NPCRecord

    npcs = [
        NPCRecord(
            name="Ambassador Spock",
            npc_type="major",
            attributes_json=json.dumps(
                {
                    "control": 11,
                    "fitness": 8,
                    "daring": 8,
                    "insight": 12,
                    "presence": 9,
                    "reason": 12,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 2,
                    "conn": 1,
                    "engineering": 2,
                    "medicine": 1,
                    "science": 5,
                    "security": 1,
                }
            ),
            stress=4,
            stress_max=5,
            appearance="Half-Vulcan, pointed ears",
            motivation="Seek logical solutions",
            affiliation="Federation",
        ),
        NPCRecord(
            name="Dr. McCoy",
            npc_type="major",
            attributes_json=json.dumps(
                {
                    "control": 8,
                    "fitness": 7,
                    "daring": 7,
                    "insight": 10,
                    "presence": 10,
                    "reason": 9,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": 1,
                    "conn": 1,
                    "engineering": 1,
                    "medicine": 5,
                    "science": 2,
                    "security": 1,
                }
            ),
            stress=5,
            stress_max=5,
            appearance="Human male, graying hair",
            motivation="Save lives at any cost",
            affiliation="Federation",
        ),
    ]

    for npc in npcs:
        test_session.add(npc)
    test_session.commit()

    return npcs


@pytest.fixture
def sample_ships(test_session):
    """Create sample ships for export/import tests."""
    from sta.database.schema import StarshipRecord

    ships = [
        StarshipRecord(
            name="USS Enterprise",
            ship_class="Constitution-class",
            ship_registry="NCC-1701",
            scale=6,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 9,
                    "structure": 9,
                    "weapons": 9,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
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
                    },
                    {
                        "name": "Photon Torpedoes",
                        "weapon_type": "torpedo",
                        "damage": 6,
                        "range": "extreme",
                        "qualities": ["explosive"],
                        "requires_calibration": True,
                    },
                ]
            ),
            talents_json=json.dumps(["Dedicated Engineering", "Resolve"]),
            shields=40,
            shields_max=40,
            resistance=6,
        ),
        StarshipRecord(
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
            shields=35,
            shields_max=35,
            resistance=5,
        ),
    ]

    for ship in ships:
        test_session.add(ship)
    test_session.commit()

    return ships


class TestCharacterExportImport:
    """Tests for character export/import endpoints."""

    def test_export_characters(self, client, sample_characters):
        """Test exporting characters."""
        response = client.get("/api/characters/export")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["version"] == "1.0"
        assert "exported_at" in data
        assert len(data["characters"]) == 2

        names = [c["name"] for c in data["characters"]]
        assert "Captain Picard" in names
        assert "Commander Riker" in names

    def test_import_new_characters(self, client, test_session):
        """Test importing new characters."""
        import_data = {
            "characters": [
                {
                    "name": "New Character",
                    "species": "Human",
                    "rank": "Lieutenant",
                    "role": "Science",
                    "attributes": {
                        "control": 8,
                        "fitness": 7,
                        "daring": 8,
                        "insight": 9,
                        "presence": 8,
                        "reason": 10,
                    },
                    "disciplines": {
                        "command": 1,
                        "conn": 1,
                        "engineering": 1,
                        "medicine": 1,
                        "science": 4,
                        "security": 1,
                    },
                    "stress": 5,
                    "stress_max": 5,
                    "determination": 1,
                    "determination_max": 3,
                }
            ]
        }

        response = client.post(
            "/api/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["imported"] == 1
        assert data["updated"] == 0

        # Verify character was added
        from sta.database.schema import CharacterRecord

        char = (
            test_session.query(CharacterRecord).filter_by(name="New Character").first()
        )
        assert char is not None
        assert char.species == "Human"

    def test_import_updates_existing_character(
        self, client, sample_characters, test_session
    ):
        """Test importing updates existing character by name."""
        import_data = {
            "characters": [
                {
                    "name": "Captain Picard",
                    "species": "Human",
                    "rank": "Captain (Updated)",
                    "role": "Command",
                    "attributes": {
                        "control": 9,
                        "fitness": 8,
                        "daring": 10,
                        "insight": 11,
                        "presence": 12,
                        "reason": 11,
                    },
                    "disciplines": {
                        "command": 5,
                        "conn": 2,
                        "engineering": 1,
                        "medicine": 1,
                        "science": 2,
                        "security": 2,
                    },
                }
            ]
        }

        response = client.post(
            "/api/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["imported"] == 0
        assert data["updated"] == 1

        # Verify character was updated
        from sta.database.schema import CharacterRecord

        char = (
            test_session.query(CharacterRecord).filter_by(name="Captain Picard").first()
        )
        assert char.rank == "Captain (Updated)"

    def test_import_multiple_characters(self, client, sample_characters):
        """Test importing multiple characters."""
        import_data = {
            "characters": [
                {
                    "name": "Character A",
                    "species": "Human",
                    "attributes": {
                        "control": 7,
                        "fitness": 7,
                        "daring": 7,
                        "insight": 7,
                        "presence": 7,
                        "reason": 7,
                    },
                    "disciplines": {
                        "command": 1,
                        "conn": 1,
                        "engineering": 1,
                        "medicine": 1,
                        "science": 1,
                        "security": 1,
                    },
                },
                {
                    "name": "Character B",
                    "species": "Vulcan",
                    "attributes": {
                        "control": 10,
                        "fitness": 8,
                        "daring": 8,
                        "insight": 10,
                        "presence": 8,
                        "reason": 12,
                    },
                    "disciplines": {
                        "command": 2,
                        "conn": 1,
                        "engineering": 1,
                        "medicine": 1,
                        "science": 4,
                        "security": 1,
                    },
                },
            ]
        }

        response = client.post(
            "/api/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["imported"] == 2

    def test_import_missing_key_fails(self, client):
        """Test importing without characters key fails."""
        response = client.post(
            "/api/characters/import",
            data=json.dumps({"something": "else"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_import_missing_name_skips(self, client):
        """Test importing character without name is skipped."""
        import_data = {
            "characters": [
                {"species": "Human"},  # Missing name
            ]
        }

        response = client.post(
            "/api/characters/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["errors"]) == 1


class TestNPCExportImport:
    """Tests for NPC export/import endpoints."""

    def test_export_npcs(self, client, sample_npcs):
        """Test exporting NPCs."""
        response = client.get("/api/npcs/export")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["version"] == "1.0"
        assert len(data["npcs"]) == 2

        names = [n["name"] for n in data["npcs"]]
        assert "Ambassador Spock" in names
        assert "Dr. McCoy" in names

    def test_import_new_npc(self, client, test_session):
        """Test importing new NPC."""
        import_data = {
            "npcs": [
                {
                    "name": "New NPC",
                    "npc_type": "minor",
                    "affiliation": "Klingon",
                    "motivation": "Conquer",
                }
            ]
        }

        response = client.post(
            "/api/npcs/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["imported"] == 1

        from sta.database.schema import NPCRecord

        npc = test_session.query(NPCRecord).filter_by(name="New NPC").first()
        assert npc is not None
        assert npc.affiliation == "Klingon"

    def test_import_updates_existing_npc(self, client, sample_npcs, test_session):
        """Test importing updates existing NPC by name."""
        import_data = {
            "npcs": [
                {
                    "name": "Ambassador Spock",
                    "npc_type": "major",
                    "affiliation": "Federation (Updated)",
                }
            ]
        }

        response = client.post(
            "/api/npcs/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["updated"] == 1

        from sta.database.schema import NPCRecord

        npc = test_session.query(NPCRecord).filter_by(name="Ambassador Spock").first()
        assert npc.affiliation == "Federation (Updated)"


class TestShipExportImport:
    """Tests for ship export/import endpoints."""

    def test_export_ships(self, client, sample_ships):
        """Test exporting ships."""
        response = client.get("/api/ships/export")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["version"] == "1.0"
        assert len(data["ships"]) == 2

        names = [s["name"] for s in data["ships"]]
        assert "USS Enterprise" in names
        assert "USS Voyager" in names

    def test_import_new_ship(self, client, test_session):
        """Test importing new ship."""
        import_data = {
            "ships": [
                {
                    "name": "New Ship",
                    "ship_class": "Defiant-class",
                    "scale": 4,
                    "systems": {
                        "comms": 7,
                        "computers": 8,
                        "engines": 8,
                        "sensors": 7,
                        "structure": 7,
                        "weapons": 9,
                    },
                    "departments": {
                        "command": 2,
                        "conn": 3,
                        "engineering": 3,
                        "medicine": 1,
                        "science": 1,
                        "security": 4,
                    },
                    "shields": 25,
                    "shields_max": 25,
                    "resistance": 4,
                }
            ]
        }

        response = client.post(
            "/api/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["imported"] == 1

        from sta.database.schema import StarshipRecord

        ship = test_session.query(StarshipRecord).filter_by(name="New Ship").first()
        assert ship is not None
        assert ship.ship_class == "Defiant-class"

    def test_import_updates_existing_ship(self, client, sample_ships, test_session):
        """Test importing updates existing ship by name."""
        import_data = {
            "ships": [
                {
                    "name": "USS Enterprise",
                    "ship_class": "Constitution-class (Updated)",
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
            ]
        }

        response = client.post(
            "/api/ships/import",
            data=json.dumps(import_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["updated"] == 1

        from sta.database.schema import StarshipRecord

        ship = (
            test_session.query(StarshipRecord).filter_by(name="USS Enterprise").first()
        )
        assert ship.ship_registry == "NCC-1701"  # Preserved


class TestBackupExport:
    """Tests for full backup endpoint."""

    def test_export_full_backup(
        self, client, sample_characters, sample_npcs, sample_ships
    ):
        """Test exporting full backup."""
        response = client.get("/api/backup")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["version"] == "1.0"
        assert "exported_at" in data
        assert len(data["characters"]) == 2
        assert len(data["npcs"]) == 2
        assert len(data["ships"]) == 2

    def test_backup_structure(
        self, client, sample_characters, sample_npcs, sample_ships
    ):
        """Test backup has correct structure."""
        response = client.get("/api/backup")
        data = json.loads(response.data)

        # Check top-level keys
        assert "version" in data
        assert "exported_at" in data
        assert "characters" in data
        assert "npcs" in data
        assert "ships" in data
        assert "campaigns" in data

        # Check character structure
        if data["characters"]:
            char = data["characters"][0]
            assert "name" in char
            assert "species" in char
            assert "attributes" in char
            assert "disciplines" in char

        # Check NPC structure
        if data["npcs"]:
            npc = data["npcs"][0]
            assert "name" in npc
            assert "npc_type" in npc

        # Check ship structure
        if data["ships"]:
            ship = data["ships"][0]
            assert "name" in ship
            assert "ship_class" in ship
            assert "scale" in ship
            assert "systems" in ship
            assert "departments" in ship
