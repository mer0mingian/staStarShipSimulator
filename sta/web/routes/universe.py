"""Universe Library API routes for managing reusable characters and ships."""

import json
from flask import Blueprint, request, jsonify
from sta.database import (
    get_session,
    UniverseItemRecord,
    UniverseLibraryRecord,
    VTTCharacterRecord,
    VTTShipRecord,
    CampaignRecord,
)

universe_bp = Blueprint("universe", __name__)

VALID_CATEGORIES = ["pcs", "npcs", "creatures", "ships"]
VALID_ITEM_TYPES = ["character", "ship"]


@universe_bp.route("/api/universe", methods=["GET"])
def list_universe_items():
    """List all library items."""
    session = get_session()
    try:
        items = session.query(UniverseItemRecord).all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "item_type": item.item_type,
                    "description": item.description,
                    "image_url": item.image_url,
                    "data": json.loads(item.data_json),
                }
                for item in items
            ]
        )
    finally:
        session.close()


@universe_bp.route("/api/universe/characters", methods=["POST"])
def add_character_to_library():
    """Add a character to the library from a VTTCharacterRecord."""
    session = get_session()
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        character_id = data.get("character_id")
        category = data.get("category", "pcs")

        if not character_id:
            return jsonify({"error": "character_id is required"}), 400

        if category not in VALID_CATEGORIES:
            return jsonify(
                {"error": f"Invalid category. Must be one of: {VALID_CATEGORIES}"}
            ), 400

        character = session.query(VTTCharacterRecord).filter_by(id=character_id).first()
        if not character:
            return jsonify({"error": "Character not found"}), 404

        existing = (
            session.query(UniverseItemRecord)
            .filter_by(name=character.name, item_type="character")
            .first()
        )
        if existing:
            return jsonify({"error": "Character already in library"}), 409

        new_item = UniverseItemRecord(
            name=character.name,
            category=category,
            item_type="character",
            data_json=character.attributes_json,
            description=character.description,
            image_url=character.avatar_url,
        )
        session.add(new_item)
        session.commit()

        return jsonify(
            {
                "id": new_item.id,
                "name": new_item.name,
                "category": new_item.category,
                "item_type": new_item.item_type,
            }
        ), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@universe_bp.route("/api/universe/ships", methods=["POST"])
def add_ship_to_library():
    """Add a ship to the library from a VTTShipRecord."""
    session = get_session()
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        ship_id = data.get("ship_id")

        if not ship_id:
            return jsonify({"error": "ship_id is required"}), 400

        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        existing = (
            session.query(UniverseItemRecord)
            .filter_by(name=ship.name, item_type="ship")
            .first()
        )
        if existing:
            return jsonify({"error": "Ship already in library"}), 409

        new_item = UniverseItemRecord(
            name=ship.name,
            category="ships",
            item_type="ship",
            data_json=ship.systems_json,
            description=ship.ship_class,
            image_url=ship.token_url,
        )
        session.add(new_item)
        session.commit()

        return jsonify(
            {
                "id": new_item.id,
                "name": new_item.name,
                "category": new_item.category,
                "item_type": new_item.item_type,
            }
        ), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@universe_bp.route("/api/universe/<category>", methods=["GET"])
def get_items_by_category(category):
    """Get items filtered by category."""
    if category not in VALID_CATEGORIES:
        return jsonify(
            {"error": f"Invalid category. Must be one of: {VALID_CATEGORIES}"}
        ), 400

    session = get_session()
    try:
        items = session.query(UniverseItemRecord).filter_by(category=category).all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "item_type": item.item_type,
                    "description": item.description,
                    "image_url": item.image_url,
                    "data": json.loads(item.data_json),
                }
                for item in items
            ]
        )
    finally:
        session.close()


@universe_bp.route("/api/universe/item/<int:item_id>", methods=["GET"])
def get_universe_item(item_id):
    """Get a specific universe item by ID."""
    session = get_session()
    try:
        item = session.query(UniverseItemRecord).filter_by(id=item_id).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404

        return jsonify(
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "item_type": item.item_type,
                "description": item.description,
                "image_url": item.image_url,
                "data": json.loads(item.data_json),
            }
        )
    finally:
        session.close()


@universe_bp.route("/api/universe/item/<int:item_id>", methods=["PUT"])
def update_universe_item(item_id):
    """Update a universe item."""
    session = get_session()
    try:
        item = session.query(UniverseItemRecord).filter_by(id=item_id).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        if "name" in data:
            item.name = data["name"]
        if "category" in data:
            if data["category"] not in VALID_CATEGORIES:
                return jsonify(
                    {"error": f"Invalid category. Must be one of: {VALID_CATEGORIES}"}
                ), 400
            item.category = data["category"]
        if "description" in data:
            item.description = data["description"]
        if "image_url" in data:
            item.image_url = data["image_url"]
        if "data" in data:
            if isinstance(data["data"], dict):
                item.data_json = json.dumps(data["data"])
            else:
                item.data_json = data["data"]

        session.commit()

        return jsonify(
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "item_type": item.item_type,
                "description": item.description,
                "image_url": item.image_url,
                "data": json.loads(item.data_json),
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@universe_bp.route("/api/universe/item/<int:item_id>", methods=["DELETE"])
def delete_universe_item(item_id):
    """Delete a universe item."""
    session = get_session()
    try:
        item = session.query(UniverseItemRecord).filter_by(id=item_id).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404

        session.delete(item)
        session.commit()

        return jsonify({"message": "Item deleted successfully"})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@universe_bp.route("/api/universe/characters", methods=["GET"])
def list_library_characters():
    """List characters in universe library with optional category filter."""
    session = get_session()
    try:
        category = request.args.get("category")

        query = session.query(UniverseItemRecord).filter_by(item_type="character")

        if category:
            if category not in VALID_CATEGORIES:
                return jsonify(
                    {"error": f"Invalid category. Must be one of: {VALID_CATEGORIES}"}
                ), 400
            query = query.filter_by(category=category)

        items = query.all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "item_type": item.item_type,
                    "description": item.description,
                    "image_url": item.image_url,
                    "data": json.loads(item.data_json),
                }
                for item in items
            ]
        )
    finally:
        session.close()


@universe_bp.route("/api/universe/ships", methods=["GET"])
def list_library_ships():
    """List ships in universe library."""
    session = get_session()
    try:
        items = session.query(UniverseItemRecord).filter_by(item_type="ship").all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "item_type": item.item_type,
                    "description": item.description,
                    "image_url": item.image_url,
                    "data": json.loads(item.data_json),
                }
                for item in items
            ]
        )
    finally:
        session.close()


@universe_bp.route(
    "/api/universe/import/character/<int:universe_item_id>", methods=["POST"]
)
def import_character_to_campaign(universe_item_id):
    """Import a character from universe library to a campaign."""
    session = get_session()
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        campaign_id = data.get("campaign_id")
        if not campaign_id:
            return jsonify({"error": "campaign_id is required"}), 400

        campaign = session.query(CampaignRecord).filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        universe_item = (
            session.query(UniverseItemRecord)
            .filter_by(id=universe_item_id, item_type="character")
            .first()
        )
        if not universe_item:
            return jsonify({"error": "Character not found in library"}), 404

        existing_in_campaign = (
            session.query(VTTCharacterRecord)
            .filter_by(name=universe_item.name, campaign_id=campaign_id)
            .first()
        )
        if existing_in_campaign:
            return jsonify({"error": "Character already exists in campaign"}), 409

        character_data = json.loads(universe_item.data_json)

        new_character = VTTCharacterRecord(
            name=universe_item.name,
            description=universe_item.description,
            avatar_url=universe_item.image_url,
            attributes_json=universe_item.data_json,
            disciplines_json=json.dumps(
                {
                    "command": character_data.get("command", 1),
                    "conn": character_data.get("conn", 1),
                    "engineering": character_data.get("engineering", 1),
                    "medicine": character_data.get("medicine", 1),
                    "science": character_data.get("science", 1),
                    "security": character_data.get("security", 1),
                }
            ),
            talents_json="[]",
            focuses_json="[]",
            campaign_id=campaign_id,
        )
        session.add(new_character)
        session.commit()

        return jsonify(
            {
                "id": new_character.id,
                "name": new_character.name,
                "campaign_id": new_character.campaign_id,
            }
        ), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@universe_bp.route("/api/universe/import/ship/<int:universe_item_id>", methods=["POST"])
def import_ship_to_campaign(universe_item_id):
    """Import a ship from universe library to a campaign."""
    session = get_session()
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        campaign_id = data.get("campaign_id")
        if not campaign_id:
            return jsonify({"error": "campaign_id is required"}), 400

        campaign = session.query(CampaignRecord).filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        universe_item = (
            session.query(UniverseItemRecord)
            .filter_by(id=universe_item_id, item_type="ship")
            .first()
        )
        if not universe_item:
            return jsonify({"error": "Ship not found in library"}), 404

        existing_in_campaign = (
            session.query(VTTShipRecord)
            .filter_by(name=universe_item.name, campaign_id=campaign_id)
            .first()
        )
        if existing_in_campaign:
            return jsonify({"error": "Ship already exists in campaign"}), 409

        ship_data = json.loads(universe_item.data_json)

        new_ship = VTTShipRecord(
            name=universe_item.name,
            ship_class=universe_item.description or "Unknown Class",
            scale=ship_data.get("scale", 4),
            token_url=universe_item.image_url,
            systems_json=universe_item.data_json,
            departments_json=json.dumps(
                {
                    "command": ship_data.get("command", 1),
                    "conn": ship_data.get("conn", 1),
                    "engineering": ship_data.get("engineering", 1),
                    "medicine": ship_data.get("medicine", 1),
                    "science": ship_data.get("science", 1),
                    "security": ship_data.get("security", 1),
                }
            ),
            weapons_json="[]",
            talents_json="[]",
            traits_json="[]",
            breaches_json="[]",
            campaign_id=campaign_id,
        )
        session.add(new_ship)
        session.commit()

        return jsonify(
            {
                "id": new_ship.id,
                "name": new_ship.name,
                "campaign_id": new_ship.campaign_id,
            }
        ), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@universe_bp.route("/api/universe/templates/characters", methods=["GET"])
def list_character_templates():
    """List character templates from universe library (characters not assigned to a campaign)."""
    session = get_session()
    try:
        items = session.query(UniverseItemRecord).filter_by(item_type="character").all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "description": item.description,
                    "image_url": item.image_url,
                    "data": json.loads(item.data_json),
                }
                for item in items
            ]
        )
    finally:
        session.close()


@universe_bp.route("/api/universe/templates/ships", methods=["GET"])
def list_ship_templates():
    """List ship templates from universe library."""
    session = get_session()
    try:
        items = session.query(UniverseItemRecord).filter_by(item_type="ship").all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "description": item.description,
                    "image_url": item.image_url,
                    "data": json.loads(item.data_json),
                }
                for item in items
            ]
        )
    finally:
        session.close()


@universe_bp.route(
    "/api/campaigns/<int:campaign_id>/characters/available", methods=["GET"]
)
def list_available_characters(campaign_id):
    """List available characters for a campaign (from universe library)."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        items = session.query(UniverseItemRecord).filter_by(item_type="character").all()

        campaign_character_names = [
            c.name
            for c in session.query(VTTCharacterRecord)
            .filter_by(campaign_id=campaign_id)
            .all()
        ]

        available = [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "description": item.description,
                "image_url": item.image_url,
                "data": json.loads(item.data_json),
                "already_in_campaign": item.name in campaign_character_names,
            }
            for item in items
        ]

        return jsonify(available)
    finally:
        session.close()


@universe_bp.route("/api/campaigns/<int:campaign_id>/ships/available", methods=["GET"])
def list_available_ships(campaign_id):
    """List available ships for a campaign (from universe library)."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        items = session.query(UniverseItemRecord).filter_by(item_type="ship").all()

        campaign_ship_names = [
            s.name
            for s in session.query(VTTShipRecord)
            .filter_by(campaign_id=campaign_id)
            .all()
        ]

        available = [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "description": item.description,
                "image_url": item.image_url,
                "data": json.loads(item.data_json),
                "already_in_campaign": item.name in campaign_ship_names,
            }
            for item in items
        ]

        return jsonify(available)
    finally:
        session.close()
