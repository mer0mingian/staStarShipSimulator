"""
Tests for Ship Management API endpoints.

Tests verify:
- Ship CRUD operations
- Validation (systems 7-12, departments 0-5, scale 1-7)
- Shield adjustments
- Power adjustments
- Breach management
- Weapons management
- Crew quality management
"""

import json
import pytest
from sta.database.vtt_schema import VTTShipRecord


class TestShipCRUD:
    """Tests for Ship CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_ship(self, client, test_session):
        """Test creating a new ship with validation."""
        response = client.post(
            "/api/ships",
            json={
                "name": "USS Endeavour",
                "ship_class": "Constitution Class",
                "registry": "NCC-1895",
                "scale": 4,
                "systems": {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                },
                "departments": {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                },
                "shields": 10,
                "shields_max": 10,
                "resistance": 4,
            },
            
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "USS Endeavour"
        assert data["scale"] == 4
        assert data["shields"] == 10

    @pytest.mark.asyncio
    async def test_create_ship_invalid_system(self, client, test_session):
        """Test creating ship with invalid system value (outside 7-12)."""
        response = client.post(
            "/api/ships",
            json={
                "name": "Invalid Ship",
                "scale": 4,
                "systems": {
                    "comms": 15,  # Invalid - too high
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                },
                "departments": {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                },
            },
            
        )
        assert response.status_code == 400
        assert "must be between 7-12" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_ship_invalid_department(self, client, test_session):
        """Test creating ship with invalid department value (outside 0-5)."""
        response = client.post(
            "/api/ships",
            json={
                "name": "Invalid Ship",
                "scale": 4,
                "systems": {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                },
                "departments": {
                    "command": 6,  # Invalid - too high
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                },
            },
            
        )
        assert response.status_code == 400
        assert "must be between 0-5" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_ship_invalid_scale(self, client, test_session):
        """Test creating ship with invalid scale (outside 1-7)."""
        response = client.post(
            "/api/ships",
            json={
                "name": "Invalid Ship",
                "scale": 10,  # Invalid - too high
                "systems": {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                },
                "departments": {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                },
            },
            
        )
        assert response.status_code == 400
        assert "Scale must be between 1-7" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_ships(self, client, test_session):
        """Test listing all ships."""
        ship = VTTShipRecord(
            name="USS Test",
            ship_class="Test Class",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()

        response = client.get("/api/ships")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "USS Test"

    @pytest.mark.asyncio
    async def test_list_ships_filter_by_campaign(self, client, test_session):
        """Test listing ships filtered by campaign_id."""
        ship1 = VTTShipRecord(
            name="USS Test 1",
            ship_class="Test Class",
            scale=4,
            campaign_id=1,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        ship2 = VTTShipRecord(
            name="USS Test 2",
            ship_class="Test Class",
            scale=4,
            campaign_id=2,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add_all([ship1, ship2])
        await test_session.commit()

        response = client.get("/api/ships?campaign_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "USS Test 1"

    @pytest.mark.asyncio
    async def test_get_ship(self, client, test_session):
        """Test getting a single ship."""
        ship = VTTShipRecord(
            name="USS GetTest",
            ship_class="Test Class",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.get(f"/api/ships/{ship_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "USS GetTest"

    @pytest.mark.asyncio
    async def test_get_ship_not_found(self, client, test_session):
        """Test getting a non-existent ship."""
        response = client.get("/api/ships/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_ship(self, client, test_session):
        """Test updating a ship."""
        ship = VTTShipRecord(
            name="USS Original",
            ship_class="Test Class",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}",
            json={"name": "USS Updated"},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "USS Updated"

    @pytest.mark.asyncio
    async def test_update_ship_invalid_system(self, client, test_session):
        """Test updating ship with invalid system value."""
        ship = VTTShipRecord(
            name="USS Test",
            ship_class="Test Class",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}",
            json={"systems": {"comms": 15}},
            
        )
        assert response.status_code == 400
        assert "must be between 7-12" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_ship(self, client, test_session):
        """Test deleting a ship."""
        ship = VTTShipRecord(
            name="USS DeleteTest",
            ship_class="Test Class",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.delete(f"/api/ships/{ship_id}")
        assert response.status_code == 200

        response = client.get(f"/api/ships/{ship_id}")
        assert response.status_code == 404


class TestShipModel:
    """Tests for ship model endpoint."""

    @pytest.mark.asyncio
    async def test_get_ship_model(self, client, test_session):
        """Test getting ship as legacy Starship model."""
        ship = VTTShipRecord(
            name="USS Model",
            ship_class="Test Class",
            ship_registry="NCC-1234",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
            weapons_json=json.dumps([]),
            talents_json=json.dumps([]),
            traits_json=json.dumps([]),
            breaches_json=json.dumps([]),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.get(f"/api/ships/{ship_id}/model")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "USS Model"
        assert data["registry"] == "NCC-1234"
        assert "systems" in data
        assert "departments" in data


class TestShipShields:
    """Tests for ship shields endpoints."""

    @pytest.mark.asyncio
    async def test_adjust_shields(self, client, test_session):
        """Test adjusting shields."""
        ship = VTTShipRecord(
            name="USS Shields",
            ship_class="Test Class",
            scale=4,
            shields=10,
            shields_max=10,
            shields_raised=True,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}/shields",
            json={"shields": 5, "raised": False},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert data["shields"] == 5
        assert data["shields_raised"] == False

    @pytest.mark.asyncio
    async def test_adjust_shields_invalid(self, client, test_session):
        """Test adjusting shields with invalid value."""
        ship = VTTShipRecord(
            name="USS Shields",
            ship_class="Test Class",
            scale=4,
            shields=10,
            shields_max=10,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}/shields",
            json={"shields": 15},
            
        )
        assert response.status_code == 400


class TestShipPower:
    """Tests for ship power endpoints."""

    @pytest.mark.asyncio
    async def test_adjust_power(self, client, test_session):
        """Test adjusting reserve power."""
        ship = VTTShipRecord(
            name="USS Power",
            ship_class="Test Class",
            scale=4,
            has_reserve_power=True,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}/power",
            json={"current": 0},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_reserve_power"] == False


class TestShipBreaches:
    """Tests for ship breach endpoints."""

    @pytest.mark.asyncio
    async def test_add_breach(self, client, test_session):
        """Test adding a system breach."""
        ship = VTTShipRecord(
            name="USS Breach",
            ship_class="Test Class",
            scale=4,
            breaches_json=json.dumps([]),
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}/breach",
            json={"system": "structure", "potency": 2, "action": "add"},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["breaches"]) == 1
        assert data["breaches"][0]["system"] == "structure"
        assert data["breaches"][0]["potency"] == 2

    @pytest.mark.asyncio
    async def test_remove_breach(self, client, test_session):
        """Test removing a system breach."""
        ship = VTTShipRecord(
            name="USS Breach",
            ship_class="Test Class",
            scale=4,
            breaches_json=json.dumps([{"system": "structure", "potency": 2}]),
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}/breach",
            json={"system": "structure", "action": "remove"},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["breaches"]) == 0


class TestShipWeapons:
    """Tests for ship weapons endpoints."""

    @pytest.mark.asyncio
    async def test_update_weapons(self, client, test_session):
        """Test updating weapons list."""
        ship = VTTShipRecord(
            name="USS Weapons",
            ship_class="Test Class",
            scale=4,
            weapons_json=json.dumps([]),
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        weapons = [
            {
                "name": "Phaser Banks",
                "weapon_type": "energy",
                "damage": 7,
                "range": "medium",
                "qualities": ["versatile 2"],
                "requires_calibration": False,
            }
        ]

        response = client.put(
            f"/api/ships/{ship_id}/weapons",
            json={"weapons": weapons},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["weapons"]) == 1
        assert data["weapons"][0]["name"] == "Phaser Banks"

    @pytest.mark.asyncio
    async def test_arm_weapon(self, client, test_session):
        """Test arming/disarming a weapon."""
        ship = VTTShipRecord(
            name="USS Weapons",
            ship_class="Test Class",
            scale=4,
            weapons_armed=False,
            weapons_json=json.dumps(
                [
                    {
                        "name": "Phaser Banks",
                        "weapon_type": "energy",
                        "damage": 7,
                        "range": "medium",
                        "qualities": [],
                        "requires_calibration": False,
                    }
                ]
            ),
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.post(
            f"/api/ships/{ship_id}/weapons/Phaser%20Banks/arm",
            json={"armed": True},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert data["weapons_armed"] == True


class TestShipCrewQuality:
    """Tests for ship crew quality endpoints."""

    @pytest.mark.asyncio
    async def test_get_crew_quality(self, client, test_session):
        """Test getting crew quality."""
        ship = VTTShipRecord(
            name="USS Crew",
            ship_class="Test Class",
            scale=4,
            crew_quality="veteran",
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.get(f"/api/ships/{ship_id}/crew-quality")
        assert response.status_code == 200
        data = response.json()
        assert data["crew_quality"] == "veteran"

    @pytest.mark.asyncio
    async def test_set_crew_quality(self, client, test_session):
        """Test setting crew quality."""
        ship = VTTShipRecord(
            name="USS Crew",
            ship_class="Test Class",
            scale=4,
            crew_quality=None,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}/crew-quality",
            json={"crew_quality": "exceptional"},
            
        )
        assert response.status_code == 200
        data = response.json()
        assert data["crew_quality"] == "exceptional"

    @pytest.mark.asyncio
    async def test_set_crew_quality_invalid(self, client, test_session):
        """Test setting invalid crew quality."""
        ship = VTTShipRecord(
            name="USS Crew",
            ship_class="Test Class",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 9,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 11,
                    "structure": 9,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 2,
                    "science": 3,
                    "security": 3,
                }
            ),
        )
        test_session.add(ship)
        await test_session.commit()
        ship_id = ship.id

        response = client.put(
            f"/api/ships/{ship_id}/crew-quality",
            json={"crew_quality": "invalid_quality"},
            
        )
        assert response.status_code == 400