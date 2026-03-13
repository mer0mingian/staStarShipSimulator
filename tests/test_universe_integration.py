"""Tests for Universe Library Integration API (Milestone 4, Task 4.3)."""

import json
import pytest
from sta.database.vtt_schema import (
    VTTCharacterRecord,
    VTTShipRecord,
    UniverseItemRecord,
)
from sta.database.schema import CampaignRecord


class TestUniverseLibraryIntegration:
    """Tests for Universe Library Integration endpoints."""

    def test_list_library_characters_empty(self, client, test_session):
        """GET /api/universe/characters should return empty list when no characters."""
        response = client.get("/api/universe/characters")
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_list_library_characters(self, client, test_session):
        """GET /api/universe/characters should return all character library items."""
        item1 = UniverseItemRecord(
            name="PC Character",
            category="pcs",
            item_type="character",
            data_json='{"command": 2, "conn": 1}',
            description="A player character",
        )
        item2 = UniverseItemRecord(
            name="NPC Character",
            category="npcs",
            item_type="character",
            data_json='{"command": 1}',
            description="An NPC",
        )
        test_session.add_all([item1, item2])
        test_session.commit()

        response = client.get("/api/universe/characters")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert data[0]["name"] == "PC Character"
        assert data[1]["name"] == "NPC Character"

    def test_list_library_characters_filter_by_category(self, client, test_session):
        """GET /api/universe/characters should filter by category."""
        item1 = UniverseItemRecord(
            name="PC",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        item2 = UniverseItemRecord(
            name="NPC",
            category="npcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add_all([item1, item2])
        test_session.commit()

        response = client.get("/api/universe/characters?category=pcs")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "PC"

    def test_list_library_characters_invalid_category(self, client):
        """GET /api/universe/characters should return 400 for invalid category."""
        response = client.get("/api/universe/characters?category=invalid")
        assert response.status_code == 400

    def test_list_library_ships_empty(self, client, test_session):
        """GET /api/universe/ships should return empty list when no ships."""
        response = client.get("/api/universe/ships")
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_list_library_ships(self, client, test_session):
        """GET /api/universe/ships should return all ship library items."""
        item = UniverseItemRecord(
            name="USS Enterprise",
            category="ships",
            item_type="ship",
            data_json='{"comms": 10}',
            description="Constitution class",
        )
        test_session.add(item)
        test_session.commit()

        response = client.get("/api/universe/ships")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "USS Enterprise"

    def test_list_character_templates(self, client, test_session):
        """GET /api/universe/templates/characters should return character templates."""
        item = UniverseItemRecord(
            name="Template Character",
            category="pcs",
            item_type="character",
            data_json='{"command": 3}',
            description="A template",
        )
        test_session.add(item)
        test_session.commit()

        response = client.get("/api/universe/templates/characters")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Template Character"

    def test_list_ship_templates(self, client, test_session):
        """GET /api/universe/templates/ships should return ship templates."""
        item = UniverseItemRecord(
            name="Template Ship",
            category="ships",
            item_type="ship",
            data_json='{"engines": 10}',
            description="A template",
        )
        test_session.add(item)
        test_session.commit()

        response = client.get("/api/universe/templates/ships")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Template Ship"


class TestImportToCampaign:
    """Tests for importing universe items to campaigns."""

    def test_import_character_to_campaign(self, client, test_session):
        """POST /api/universe/import/character/<id> should import character to campaign."""
        campaign = CampaignRecord(campaign_id="test-import-001", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        universe_item = UniverseItemRecord(
            name="Imported Character",
            category="pcs",
            item_type="character",
            data_json=json.dumps(
                {
                    "command": 3,
                    "conn": 2,
                    "engineering": 1,
                    "medicine": 1,
                    "science": 1,
                    "security": 1,
                }
            ),
            description="A character to import",
        )
        test_session.add(universe_item)
        test_session.commit()

        response = client.post(
            f"/api/universe/import/character/{universe_item.id}",
            json={"campaign_id": campaign.id},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Imported Character"
        assert data["campaign_id"] == campaign.id

    def test_import_character_missing_campaign_id(self, client, test_session):
        """POST /api/universe/import/character should return 400 without campaign_id."""
        universe_item = UniverseItemRecord(
            name="Test",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        response = client.post(
            f"/api/universe/import/character/{universe_item.id}",
            json={},
        )
        assert response.status_code == 400

    def test_import_character_campaign_not_found(self, client, test_session):
        """POST /api/universe/import/character should return 404 for nonexistent campaign."""
        universe_item = UniverseItemRecord(
            name="Test",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        response = client.post(
            f"/api/universe/import/character/{universe_item.id}",
            json={"campaign_id": 99999},
        )
        assert response.status_code == 404

    def test_import_character_item_not_found(self, client, test_session):
        """POST /api/universe/import/character should return 404 for nonexistent item."""
        campaign = CampaignRecord(campaign_id="test-import-002", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        response = client.post(
            "/api/universe/import/character/99999",
            json={"campaign_id": campaign.id},
        )
        assert response.status_code == 404

    def test_import_character_already_in_campaign(self, client, test_session):
        """POST /api/universe/import/character should return 409 if already in campaign."""
        campaign = CampaignRecord(campaign_id="test-import-003", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        universe_item = UniverseItemRecord(
            name="Duplicate Character",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        existing_char = VTTCharacterRecord(
            name="Duplicate Character",
            campaign_id=campaign.id,
            attributes_json="{}",
            disciplines_json="{}",
        )
        test_session.add(existing_char)
        test_session.commit()

        response = client.post(
            f"/api/universe/import/character/{universe_item.id}",
            json={"campaign_id": campaign.id},
        )
        assert response.status_code == 409

    def test_import_ship_to_campaign(self, client, test_session):
        """POST /api/universe/import/ship/<id> should import ship to campaign."""
        campaign = CampaignRecord(campaign_id="test-import-004", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        universe_item = UniverseItemRecord(
            name="Imported Ship",
            category="ships",
            item_type="ship",
            data_json=json.dumps(
                {
                    "comms": 10,
                    "computers": 10,
                    "engines": 10,
                    "sensors": 10,
                    "structure": 10,
                    "weapons": 10,
                }
            ),
            description="A ship to import",
        )
        test_session.add(universe_item)
        test_session.commit()

        response = client.post(
            f"/api/universe/import/ship/{universe_item.id}",
            json={"campaign_id": campaign.id},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Imported Ship"
        assert data["campaign_id"] == campaign.id

    def test_import_ship_missing_campaign_id(self, client, test_session):
        """POST /api/universe/import/ship should return 400 without campaign_id."""
        universe_item = UniverseItemRecord(
            name="Test",
            category="ships",
            item_type="ship",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        response = client.post(
            f"/api/universe/import/ship/{universe_item.id}",
            json={},
        )
        assert response.status_code == 400


class TestAvailableItemsForCampaign:
    """Tests for available items endpoints."""

    def test_available_characters_for_campaign(self, client, test_session):
        """GET /api/campaigns/<id>/characters/available should return available characters."""
        campaign = CampaignRecord(campaign_id="test-avail-001", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        universe_item = UniverseItemRecord(
            name="Available Character",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        response = client.get(f"/api/campaigns/{campaign.id}/characters/available")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Available Character"
        assert data[0]["already_in_campaign"] is False

    def test_available_characters_shows_already_in_campaign(self, client, test_session):
        """GET /api/campaigns/<id>/characters/available should mark items already in campaign."""
        campaign = CampaignRecord(campaign_id="test-avail-002", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        universe_item = UniverseItemRecord(
            name="Existing Character",
            category="pcs",
            item_type="character",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        existing_char = VTTCharacterRecord(
            name="Existing Character",
            campaign_id=campaign.id,
            attributes_json="{}",
            disciplines_json="{}",
        )
        test_session.add(existing_char)
        test_session.commit()

        response = client.get(f"/api/campaigns/{campaign.id}/characters/available")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["already_in_campaign"] is True

    def test_available_characters_campaign_not_found(self, client):
        """GET /api/campaigns/<id>/characters/available should return 404 for nonexistent campaign."""
        response = client.get("/api/campaigns/99999/characters/available")
        assert response.status_code == 404

    def test_available_ships_for_campaign(self, client, test_session):
        """GET /api/campaigns/<id>/ships/available should return available ships."""
        campaign = CampaignRecord(campaign_id="test-avail-003", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        universe_item = UniverseItemRecord(
            name="Available Ship",
            category="ships",
            item_type="ship",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        response = client.get(f"/api/campaigns/{campaign.id}/ships/available")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Available Ship"
        assert data[0]["already_in_campaign"] is False

    def test_available_ships_shows_already_in_campaign(self, client, test_session):
        """GET /api/campaigns/<id>/ships/available should mark items already in campaign."""
        campaign = CampaignRecord(campaign_id="test-avail-004", name="Test Campaign")
        test_session.add(campaign)
        test_session.commit()

        universe_item = UniverseItemRecord(
            name="Existing Ship",
            category="ships",
            item_type="ship",
            data_json="{}",
        )
        test_session.add(universe_item)
        test_session.commit()

        existing_ship = VTTShipRecord(
            name="Existing Ship",
            ship_class="Test Class",
            scale=4,
            campaign_id=campaign.id,
            systems_json="{}",
            departments_json="{}",
            weapons_json="[]",
            talents_json="[]",
            traits_json="[]",
            breaches_json="[]",
        )
        test_session.add(existing_ship)
        test_session.commit()

        response = client.get(f"/api/campaigns/{campaign.id}/ships/available")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["already_in_campaign"] is True

    def test_available_ships_campaign_not_found(self, client):
        """GET /api/campaigns/<id>/ships/available should return 404 for nonexistent campaign."""
        response = client.get("/api/campaigns/99999/ships/available")
        assert response.status_code == 404
