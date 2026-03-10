"""Character routes for VTT character management."""

import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from sta.database import (
    get_session,
    VTTCharacterRecord,
    CampaignRecord,
    CampaignPlayerRecord,
)
from sta.generators.data import GENERAL_TALENTS

characters_bp = Blueprint("characters", __name__)


VALID_STATES = ["Ok", "Fatigued", "Injured", "Dead"]


def _require_gm_auth(session, campaign_id: int):
    """Verify GM authentication for a campaign. Returns GM player or error tuple."""
    session_token = request.cookies.get("sta_session_token")
    if not session_token:
        return None, jsonify({"error": "GM authentication required"}), 401

    gm_player = (
        session.query(CampaignPlayerRecord)
        .filter_by(campaign_id=campaign_id, is_gm=True)
        .first()
    )

    if not gm_player or session_token != gm_player.session_token:
        return None, jsonify({"error": "GM authentication required"}), 401

    return gm_player, None, None


def _serialize_character(char: VTTCharacterRecord) -> dict:
    """Serialize a VTTCharacterRecord to JSON."""
    return {
        "id": char.id,
        "name": char.name,
        "species": char.species,
        "rank": char.rank,
        "role": char.role,
        "attributes": json.loads(char.attributes_json),
        "disciplines": json.loads(char.disciplines_json),
        "talents": json.loads(char.talents_json),
        "focuses": json.loads(char.focuses_json),
        "stress": char.stress,
        "stress_max": char.stress_max,
        "determination": char.determination,
        "determination_max": char.determination_max,
        "character_type": char.character_type,
        "pronouns": char.pronouns,
        "avatar_url": char.avatar_url,
        "description": char.description,
        "values": json.loads(char.values_json),
        "equipment": json.loads(char.equipment_json),
        "environment": char.environment,
        "upbringing": char.upbringing,
        "career_path": char.career_path,
        "campaign_id": char.campaign_id,
        "scene_id": char.scene_id,
        "is_visible_to_players": char.is_visible_to_players,
        "created_at": char.created_at.isoformat() if char.created_at else None,
        "updated_at": char.updated_at.isoformat() if char.updated_at else None,
        "state": getattr(char, "state", "Ok"),
    }


# =============================================================================
# Character CRUD Endpoints
# =============================================================================


@characters_bp.route("/api/characters", methods=["GET"])
def list_characters():
    """List all characters with optional filters: campaign_id, type."""
    session = get_session()
    try:
        campaign_id = request.args.get("campaign_id", type=int)
        char_type = request.args.get("type")

        query = session.query(VTTCharacterRecord)

        if campaign_id is not None:
            query = query.filter_by(campaign_id=campaign_id)

        if char_type:
            query = query.filter_by(character_type=char_type)

        characters = query.all()
        return jsonify([_serialize_character(c) for c in characters])
    finally:
        session.close()


@characters_bp.route("/api/characters/<int:char_id>", methods=["GET"])
def get_character(char_id: int):
    """Get single character with full details."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        return jsonify(_serialize_character(char))
    finally:
        session.close()


@characters_bp.route("/api/characters", methods=["POST"])
def create_character():
    """Create new character with validation.

    Validates:
    - attributes: 7-12 each
    - disciplines: 0-5 each
    - stress: 0-max
    """
    session = get_session()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get("name", "Unnamed Character")

        attributes = data.get("attributes", {})
        for attr_name, value in attributes.items():
            if not (7 <= value <= 12):
                return jsonify(
                    {
                        "error": f"Attribute {attr_name} must be between 7-12, got {value}"
                    }
                ), 400

        disciplines = data.get("disciplines", {})
        for disc_name, value in disciplines.items():
            if not (0 <= value <= 5):
                return jsonify(
                    {
                        "error": f"Discipline {disc_name} must be between 0-5, got {value}"
                    }
                ), 400

        stress_max = data.get("stress_max", 5)
        stress = data.get("stress", 0)
        if not (0 <= stress <= stress_max):
            return jsonify(
                {"error": f"Stress must be between 0-{stress_max}, got {stress}"}
            ), 400

        determination_max = data.get("determination_max", 3)
        determination = data.get("determination", 0)
        if not (0 <= determination <= determination_max):
            return jsonify(
                {
                    "error": f"Determination must be between 0-{determination_max}, got {determination}"
                }
            ), 400

        campaign_id = data.get("campaign_id")

        char = VTTCharacterRecord(
            name=name,
            species=data.get("species"),
            rank=data.get("rank"),
            role=data.get("role"),
            attributes_json=json.dumps(attributes),
            disciplines_json=json.dumps(disciplines),
            talents_json=json.dumps(data.get("talents", [])),
            focuses_json=json.dumps(data.get("focuses", [])),
            stress=stress,
            stress_max=stress_max,
            determination=determination,
            determination_max=determination_max,
            character_type=data.get("character_type", "support"),
            pronouns=data.get("pronouns"),
            avatar_url=data.get("avatar_url"),
            description=data.get("description"),
            values_json=json.dumps(data.get("values", [])),
            equipment_json=json.dumps(data.get("equipment", [])),
            environment=data.get("environment"),
            upbringing=data.get("upbringing"),
            career_path=data.get("career_path"),
            campaign_id=campaign_id,
            is_visible_to_players=data.get("is_visible_to_players", True),
        )

        session.add(char)
        session.commit()

        return jsonify(_serialize_character(char)), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@characters_bp.route("/api/characters/<int:char_id>", methods=["PUT"])
def update_character(char_id: int):
    """Update character with validation."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        if "name" in data:
            char.name = data["name"]
        if "species" in data:
            char.species = data["species"]
        if "rank" in data:
            char.rank = data["rank"]
        if "role" in data:
            char.role = data["role"]
        if "character_type" in data:
            char.character_type = data["character_type"]
        if "pronouns" in data:
            char.pronouns = data["pronouns"]
        if "avatar_url" in data:
            char.avatar_url = data["avatar_url"]
        if "description" in data:
            char.description = data["description"]
        if "environment" in data:
            char.environment = data["environment"]
        if "upbringing" in data:
            char.upbringing = data["upbringing"]
        if "career_path" in data:
            char.career_path = data["career_path"]
        if "is_visible_to_players" in data:
            char.is_visible_to_players = data["is_visible_to_players"]
        if "campaign_id" in data:
            char.campaign_id = data["campaign_id"]

        if "attributes" in data:
            attrs = data["attributes"]
            for attr_name, value in attrs.items():
                if not (7 <= value <= 12):
                    return jsonify(
                        {
                            "error": f"Attribute {attr_name} must be between 7-12, got {value}"
                        }
                    ), 400
            char.attributes_json = json.dumps(attrs)

        if "disciplines" in data:
            discs = data["disciplines"]
            for disc_name, value in discs.items():
                if not (0 <= value <= 5):
                    return jsonify(
                        {
                            "error": f"Discipline {disc_name} must be between 0-5, got {value}"
                        }
                    ), 400
            char.disciplines_json = json.dumps(discs)

        if "stress" in data or "stress_max" in data:
            stress_max = data.get("stress_max", char.stress_max)
            stress = data.get("stress", char.stress)
            if not (0 <= stress <= stress_max):
                return jsonify(
                    {"error": f"Stress must be between 0-{stress_max}, got {stress}"}
                ), 400
            char.stress = stress
            char.stress_max = stress_max

        if "determination" in data or "determination_max" in data:
            determination_max = data.get("determination_max", char.determination_max)
            determination = data.get("determination", char.determination)
            if not (0 <= determination <= determination_max):
                return jsonify(
                    {
                        "error": f"Determination must be between 0-{determination_max}, got {determination}"
                    }
                ), 400
            char.determination = determination
            char.determination_max = determination_max

        if "talents" in data:
            char.talents_json = json.dumps(data["talents"])
        if "focuses" in data:
            char.focuses_json = json.dumps(data["focuses"])
        if "values" in data:
            char.values_json = json.dumps(data["values"])
        if "equipment" in data:
            char.equipment_json = json.dumps(data["equipment"])

        if "state" in data:
            if data["state"] not in VALID_STATES:
                return jsonify({"error": f"State must be one of {VALID_STATES}"}), 400
            char.state = data["state"]

        session.commit()
        return jsonify(_serialize_character(char))
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@characters_bp.route("/api/characters/<int:char_id>", methods=["DELETE"])
def delete_character(char_id: int):
    """Delete character (GM only)."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        if char.campaign_id:
            gm_player, error_response, status = _require_gm_auth(
                session, char.campaign_id
            )
            if error_response:
                return error_response, status

        session.delete(char)
        session.commit()
        return jsonify({"success": True})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Character Model Endpoint
# =============================================================================


@characters_bp.route("/api/characters/<int:char_id>/model", methods=["GET"])
def get_character_model(char_id: int):
    """Return character as legacy Character model."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        model = char.to_model()

        return jsonify(
            {
                "name": model.name,
                "attributes": {
                    "control": model.attributes.control,
                    "fitness": model.attributes.fitness,
                    "daring": model.attributes.daring,
                    "insight": model.attributes.insight,
                    "presence": model.attributes.presence,
                    "reason": model.attributes.reason,
                },
                "disciplines": {
                    "command": model.disciplines.command,
                    "conn": model.disciplines.conn,
                    "engineering": model.disciplines.engineering,
                    "medicine": model.disciplines.medicine,
                    "science": model.disciplines.science,
                    "security": model.disciplines.security,
                },
                "talents": model.talents,
                "focuses": model.focuses,
                "stress": model.stress,
                "stress_max": model.stress_max,
                "determination": model.determination,
                "determination_max": model.determination_max,
                "rank": model.rank,
                "species": model.species,
                "role": model.role,
                "character_type": model.character_type,
                "pronouns": model.pronouns,
                "avatar_url": model.avatar_url,
                "description": model.description,
                "values": model.values,
                "equipment": model.equipment,
                "environment": model.environment,
                "upbringing": model.upbringing,
                "career_path": model.career_path,
            }
        )
    finally:
        session.close()


# =============================================================================
# Character Stress & Determination Endpoints
# =============================================================================


@characters_bp.route("/api/characters/<int:char_id>/stress", methods=["PUT"])
def adjust_stress(char_id: int):
    """Adjust stress (body: {adjustment: int})."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        data = request.get_json()
        if not data or "adjustment" not in data:
            return jsonify({"error": "adjustment is required"}), 400

        adjustment = data["adjustment"]
        new_stress = char.stress + adjustment

        if new_stress < 0:
            new_stress = 0
        if new_stress > char.stress_max:
            new_stress = char.stress_max

        char.stress = new_stress
        session.commit()

        return jsonify(
            {
                "stress": char.stress,
                "stress_max": char.stress_max,
                "adjustment": adjustment,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@characters_bp.route("/api/characters/<int:char_id>/determination", methods=["PUT"])
def adjust_determination(char_id: int):
    """Adjust determination."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        data = request.get_json()
        if not data or "adjustment" not in data:
            return jsonify({"error": "adjustment is required"}), 400

        adjustment = data["adjustment"]
        new_determination = char.determination + adjustment

        if new_determination < 0:
            new_determination = 0
        if new_determination > char.determination_max:
            new_determination = char.determination_max

        char.determination = new_determination
        session.commit()

        return jsonify(
            {
                "determination": char.determination,
                "determination_max": char.determination_max,
                "adjustment": adjustment,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Character State Endpoint
# =============================================================================


@characters_bp.route("/api/characters/<int:char_id>/state", methods=["PUT"])
def update_character_state(char_id: int):
    """Update character state (Ok, Fatigued, Injured, Dead)."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        data = request.get_json()
        if not data or "state" not in data:
            return jsonify({"error": "state is required"}), 400

        new_state = data["state"]
        if new_state not in VALID_STATES:
            return jsonify({"error": f"State must be one of {VALID_STATES}"}), 400

        char.state = new_state
        session.commit()

        return jsonify({"state": char.state})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Character Talents Endpoints
# =============================================================================


@characters_bp.route("/api/characters/<int:char_id>/talents", methods=["GET"])
def list_talents(char_id: int):
    """List available talents for a character."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        current_talents = json.loads(char.talents_json)

        return jsonify(
            {
                "character_talents": current_talents,
                "available_talents": GENERAL_TALENTS,
            }
        )
    finally:
        session.close()


@characters_bp.route("/api/characters/<int:char_id>/talents", methods=["POST"])
def add_talent(char_id: int):
    """Add talent to character (body: {talent_name: string})."""
    session = get_session()
    try:
        char = session.query(VTTCharacterRecord).filter_by(id=char_id).first()
        if not char:
            return jsonify({"error": "Character not found"}), 404

        data = request.get_json()
        if not data or "talent_name" not in data:
            return jsonify({"error": "talent_name is required"}), 400

        talent_name = data["talent_name"]

        if talent_name not in GENERAL_TALENTS:
            return jsonify({"error": f"Unknown talent: {talent_name}"}), 400

        current_talents = json.loads(char.talents_json)

        if talent_name in current_talents:
            return jsonify({"error": "Character already has this talent"}), 400

        current_talents.append(talent_name)
        char.talents_json = json.dumps(current_talents)
        session.commit()

        return jsonify(
            {
                "talents": current_talents,
                "added": talent_name,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
