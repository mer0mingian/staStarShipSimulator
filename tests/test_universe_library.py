"""Tests for Universe Library API (Milestone 2, Task 2.2)."""

import json
import pytest
from sta.database.vtt_schema import (
    VTTCharacterRecord,
    VTTShipRecord,
    UniverseItemRecord,
)


class TestUniverseLibraryAPI:
    """Tests for Universe Library API endpoints."""

    @pytest.mark.asyncio
    async def test_list_empty_library(self, client, test_session):
        """GET /api/universe should return empty list when no items."""
        response = client.get("/api/universe")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_list_library_with_items(self, client, test_session):
        """GET /api/universe should return all library items."""
        item1 = UniverseItemRecord(
            name="Test Character",
            category="pcs",
            item_type="character",
            data_json='{"test": "data"}',
            description="A test character",
        )
        item2 = UniverseItemRecord(
            name="Test Ship",
            category="ships",
            item_type="ship",
            data_json='{"test": "ship"}',
            description="A test ship",
        )
        test_session.add(item1)
        test_session.add(item2)
        await test_session.commit()

        response = client.get("/api/universe")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Test Character"
        assert data[1]["name"] == "Test Ship"

    @pytest.mark.asyncio
    async def test_add_character_to_library(self, client, test_session):
        """POST /api/universe/characters should add character to library."""
        char = VTTCharacterRecord(
            name="Captain Picard",
            species="Human",
            rank="Captain",
            attributes_json=json.dumps(
                {
                    "control": 10,
                    "daring": 9,
                    "fitness": 8,
                    "insight": 11,
                    "presence": 12,
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
                    "security": 1,
                }
            ),
            talents_json="[]",
            focuses_json="[]",
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            "/api/universe/characters",
            json={"character_id": char.id, "category": "pcs"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Captain Picard"
        assert data["category"] == "pcs"
        assert data["item_type"] == "character"

    @pytest.mark.asyncio
    async def test_add_character_missing_id(self, client):
        """POST /api/universe/characters should return 400 when no character_id."""
        response = client.post("/api/universe/characters", json={})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_character_not_found(self, client):
        """POST /api/universe/characters should return 404 for nonexistent character."""
        response = client.post(
            "/api/universe/characters",
            json={"character_id": 99999, "category": "pcs"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_character_invalid_category(self, client, test_session):
        """POST /api/universe/characters should return 400 for invalid category."""
        char = VTTCharacterRecord(
            name="Test Char",
            species="Human",
            attributes_json='{"control": 10, "daring": 9, "fitness": 8, "insight": 11, "presence": 12, "reason": 10}',
            disciplines_json='{"command": 1, "conn": 1, "engineering": 1, "medicine": 1, "science": 1, "security": 1}',
            talents_json="[]",
            focuses_json="[]",
        )
        test_session.add(char)
        await test_session.commit()

        response = client.post(
            "/api/universe/characters",
            json={"character_id": char.id, "category": "invalid"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_ship_to_library(self, client, test_session):
        """POST /api/universe/ships should add ship to library."""
        ship = VTTShipRecord(
            name="USS Enterprise",
            ship_class="Constitution",
            ship_registry="NCC-1701",
            scale=4,
            systems_json=json.dumps(
                {
                    "comms": 10,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 10,
                    "structure": 10,
                    "weapons": 10,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": 3,
                    "conn": 3,
                    "engineering": 3,
                    "medicine": 1,
                    "science": 2,
                    "security": 2,
                }
            ),
            weapons_json="[]",
            talents_json="[]",
            traits_json="[]",
            breaches_json="[]",
        )
        test_session.add(ship)
        await test_session.commit()

        response = client.post("/api/universe/ships", json={"ship_id": ship.id})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "USS Enterprise"
        assert data["category"] == "ships"
        assert data["item_type"] == "ship"

    @pytest.mark.asyncio
    async def test_add_ship_missing_id(self, client):
        """POST /api/universe/ships should return 400 when no ship_id."""
        response = client.post("/api/universe/ships", json={})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_ship_not_found(self, client):
        """POST /api/universe/ships should return 404 for nonexistent ship."""
        response = client.post("/api/universe/ships", json={"ship_id": 99999})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_items_by_category(self, client, test_session):
        """GET /api/universe/<category> should filter by category."""
        item1 = UniverseItemRecord(
            name="PC Character",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        item2 = UniverseItemRecord(
            name="NPC Character",
            category="npcs",
            item_type="character",
            data_json="{}",
        )
        item3 = UniverseItemRecord(
            name="Ship",
            category="ships",
            item_type="ship",
            data_json="{}",
        )
        test_session.add_all([item1, item2, item3])
        await test_session.commit()

        response = client.get("/api/universe/pcs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "PC Character"

        response = client.get("/api/universe/npcs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "NPC Character"

        response = client.get("/api/universe/ships")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Ship"

    @pytest.mark.asyncio
    async def test_get_items_by_invalid_category(self, client):
        """GET /api/universe/<category> should return 400 for invalid category."""
        response = client.get("/api/universe/invalid")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_specific_item(self, client, test_session):
        """GET /api/universe/item/<id> should return specific item."""
        item = UniverseItemRecord(
            name="Specific Item",
            category="pcs",
            item_type="character",
            data_json='{"key": "value"}',
            description="A specific item",
            image_url="http://example.com/image.png",
        )
        test_session.add(item)
        await test_session.commit()
        item_id = item.id

        response = client.get(f"/api/universe/item/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Specific Item"
        assert data["description"] == "A specific item"
        assert data["image_url"] == "http://example.com/image.png"

    @pytest.mark.asyncio
    async def test_get_specific_item_not_found(self, client):
        """GET /api/universe/item/<id> should return 404 for nonexistent item."""
        response = client.get("/api/universe/item/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_item(self, client, test_session):
        """PUT /api/universe/item/<id> should update item."""
        item = UniverseItemRecord(
            name="Original Name",
            category="pcs",
            item_type="character",
            data_json='{"old": "data"}',
            description="Original description",
        )
        test_session.add(item)
        await test_session.commit()
        item_id = item.id

        response = client.put(
            f"/api/universe/item/{item_id}",
            json={
                "name": "New Name",
                "description": "New description",
                "data": {"new": "data"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_update_item_not_found(self, client):
        """PUT /api/universe/item/<id> should return 404 for nonexistent item."""
        response = client.put("/api/universe/item/99999", json={"name": "Test"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_item_invalid_category(self, client, test_session):
        """PUT /api/universe/item/<id> should return 400 for invalid category."""
        item = UniverseItemRecord(
            name="Test",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add(item)
        await test_session.commit()
        item_id = item.id

        response = client.put(
            f"/api/universe/item/{item_id}",
            json={"category": "invalid"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_item(self, client, test_session):
        """DELETE /api/universe/item/<id> should delete item."""
        item = UniverseItemRecord(
            name="To Delete",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add(item)
        await test_session.commit()
        item_id = item.id

        response = client.delete(f"/api/universe/item/{item_id}")
        assert response.status_code == 200

        response = client.get(f"/api/universe/item/{item_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_item_not_found(self, client):
        """DELETE /api/universe/item/<id> should return 404 for nonexistent item."""
        response = client.delete("/api/universe/item/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_duplicate_character_prevented(self, client, test_session):
        """Adding same character twice should return 409."""
        char = VTTCharacterRecord(
            name="Duplicate",
            species="Human",
            attributes_json='{"control": 10, "daring": 9, "fitness": 8, "insight": 11, "presence": 12, "reason": 10}',
            disciplines_json='{"command": 1, "conn": 1, "engineering": 1, "medicine": 1, "science": 1, "security": 1}',
            talents_json="[]",
            focuses_json="[]",
        )
        test_session.add(char)
        await test_session.commit()

        client.post(
            "/api/universe/characters",
            json={"character_id": char.id, "category": "pcs"},
        )

        response = client.post(
            "/api/universe/characters",
            json={"character_id": char.id, "category": "pcs"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_duplicate_ship_prevented(self, client, test_session):
        """Adding same ship twice should return 409."""
        ship = VTTShipRecord(
            name="Duplicate Ship",
            ship_class="Test",
            scale=4,
            systems_json='{"comms": 10, "computers": 10, "engines": 10, "sensors": 10, "structure": 10, "weapons": 10}',
            departments_json='{"command": 1, "conn": 1, "engineering": 1, "medicine": 1, "science": 1, "security": 1}',
            weapons_json="[]",
            talents_json="[]",
            traits_json="[]",
            breaches_json="[]",
        )
        test_session.add(ship)
        await test_session.commit()

        client.post("/api/universe/ships", json={"ship_id": ship.id})

        response = client.post("/api/universe/ships", json={"ship_id": ship.id})
        assert response.status_code == 409