"""Ship routes for VTT ship management."""

import json
from flask import Blueprint, request, jsonify
from sta.database import (
    get_session,
    VTTShipRecord,
    CampaignRecord,
    CampaignPlayerRecord,
)
from sta.models.enums import SystemType, CrewQuality

ships_bp = Blueprint("ships", __name__)


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


def _serialize_ship(ship: VTTShipRecord) -> dict:
    """Serialize a VTTShipRecord to JSON."""
    return {
        "id": ship.id,
        "name": ship.name,
        "ship_class": ship.ship_class,
        "ship_registry": ship.ship_registry,
        "scale": ship.scale,
        "systems": json.loads(ship.systems_json),
        "departments": json.loads(ship.departments_json),
        "weapons": json.loads(ship.weapons_json),
        "talents": json.loads(ship.talents_json),
        "traits": json.loads(ship.traits_json),
        "breaches": json.loads(ship.breaches_json),
        "shields": ship.shields,
        "shields_max": ship.shields_max,
        "resistance": ship.resistance,
        "has_reserve_power": ship.has_reserve_power,
        "shields_raised": ship.shields_raised,
        "weapons_armed": ship.weapons_armed,
        "crew_quality": ship.crew_quality,
        "token_url": ship.token_url,
        "token_scale": ship.token_scale,
        "is_visible_to_players": ship.is_visible_to_players,
        "vtt_position_json": json.loads(ship.vtt_position_json),
        "vtt_status_effects_json": json.loads(ship.vtt_status_effects_json),
        "vtt_facing_direction": ship.vtt_facing_direction,
        "campaign_id": ship.campaign_id,
        "scene_id": ship.scene_id,
        "created_at": ship.created_at.isoformat() if ship.created_at else None,
        "updated_at": ship.updated_at.isoformat() if ship.updated_at else None,
    }


# =============================================================================
# Ship CRUD Endpoints
# =============================================================================


@ships_bp.route("/api/ships", methods=["GET"])
def list_ships():
    """List all ships with optional filters: campaign_id."""
    session = get_session()
    try:
        campaign_id = request.args.get("campaign_id", type=int)

        query = session.query(VTTShipRecord)

        if campaign_id is not None:
            query = query.filter_by(campaign_id=campaign_id)

        ships = query.all()
        return jsonify([_serialize_ship(s) for s in ships])
    finally:
        session.close()


@ships_bp.route("/api/ships/<int:ship_id>", methods=["GET"])
def get_ship(ship_id: int):
    """Get single ship with full details."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        return jsonify(_serialize_ship(ship))
    finally:
        session.close()


@ships_bp.route("/api/ships", methods=["POST"])
def create_ship():
    """Create new ship with validation.

    Validates:
    - systems: 7-12 each
    - departments: 0-5 each
    - scale: 1-7
    """
    session = get_session()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get("name", "Unnamed Ship")

        systems = data.get("systems", {})
        for sys_name, value in systems.items():
            if not (7 <= value <= 12):
                return jsonify(
                    {"error": f"System {sys_name} must be between 7-12, got {value}"}
                ), 400

        departments = data.get("departments", {})
        for dept_name, value in departments.items():
            if not (0 <= value <= 5):
                return jsonify(
                    {
                        "error": f"Department {dept_name} must be between 0-5, got {value}"
                    }
                ), 400

        scale = data.get("scale", 4)
        if not (1 <= scale <= 7):
            return jsonify({"error": f"Scale must be between 1-7, got {scale}"}), 400

        campaign_id = data.get("campaign_id")

        ship = VTTShipRecord(
            name=name,
            ship_class=data.get("ship_class"),
            ship_registry=data.get("registry"),
            scale=scale,
            systems_json=json.dumps(systems),
            departments_json=json.dumps(departments),
            weapons_json=json.dumps(data.get("weapons", [])),
            talents_json=json.dumps(data.get("talents", [])),
            traits_json=json.dumps(data.get("traits", [])),
            breaches_json=json.dumps(data.get("breaches", [])),
            shields=data.get("shields", 0),
            shields_max=data.get("shields_max", 0),
            resistance=data.get("resistance", 0),
            has_reserve_power=data.get("has_reserve_power", True),
            shields_raised=data.get("shields_raised", False),
            weapons_armed=data.get("weapons_armed", False),
            crew_quality=data.get("crew_quality"),
            campaign_id=campaign_id,
            is_visible_to_players=data.get("is_visible_to_players", True),
        )

        session.add(ship)
        session.commit()

        return jsonify(_serialize_ship(ship)), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@ships_bp.route("/api/ships/<int:ship_id>", methods=["PUT"])
def update_ship(ship_id: int):
    """Update ship with validation."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        if "name" in data:
            ship.name = data["name"]
        if "ship_class" in data:
            ship.ship_class = data["ship_class"]
        if "ship_registry" in data:
            ship.ship_registry = data["ship_registry"]
        if "campaign_id" in data:
            ship.campaign_id = data["campaign_id"]
        if "scene_id" in data:
            ship.scene_id = data["scene_id"]
        if "is_visible_to_players" in data:
            ship.is_visible_to_players = data["is_visible_to_players"]
        if "token_url" in data:
            ship.token_url = data["token_url"]
        if "token_scale" in data:
            ship.token_scale = data["token_scale"]
        if "vtt_facing_direction" in data:
            ship.vtt_facing_direction = data["vtt_facing_direction"]
        if "crew_quality" in data:
            if data["crew_quality"] is not None:
                try:
                    CrewQuality(data["crew_quality"])
                except ValueError:
                    valid_qualities = [q.value for q in CrewQuality]
                    return jsonify(
                        {"error": f"crew_quality must be one of {valid_qualities}"}
                    ), 400
            ship.crew_quality = data["crew_quality"]

        if "scale" in data:
            scale = data["scale"]
            if not (1 <= scale <= 7):
                return jsonify(
                    {"error": f"Scale must be between 1-7, got {scale}"}
                ), 400
            ship.scale = scale

        if "shields" in data or "shields_max" in data:
            shields_max = data.get("shields_max", ship.shields_max)
            shields = data.get("shields", ship.shields)
            if shields_max < 0:
                return jsonify({"error": "Shields max cannot be negative"}), 400
            if not (0 <= shields <= shields_max):
                return jsonify(
                    {"error": f"Shields must be between 0-{shields_max}, got {shields}"}
                ), 400
            ship.shields = shields
            ship.shields_max = shields_max

        if "resistance" in data:
            ship.resistance = data["resistance"]

        if "has_reserve_power" in data:
            ship.has_reserve_power = data["has_reserve_power"]

        if "shields_raised" in data:
            ship.shields_raised = data["shields_raised"]

        if "weapons_armed" in data:
            ship.weapons_armed = data["weapons_armed"]

        if "systems" in data:
            systems = data["systems"]
            for sys_name, value in systems.items():
                if not (7 <= value <= 12):
                    return jsonify(
                        {
                            "error": f"System {sys_name} must be between 7-12, got {value}"
                        }
                    ), 400
            ship.systems_json = json.dumps(systems)

        if "departments" in data:
            departments = data["departments"]
            for dept_name, value in departments.items():
                if not (0 <= value <= 5):
                    return jsonify(
                        {
                            "error": f"Department {dept_name} must be between 0-5, got {value}"
                        }
                    ), 400
            ship.departments_json = json.dumps(departments)

        if "weapons" in data:
            ship.weapons_json = json.dumps(data["weapons"])

        if "talents" in data:
            ship.talents_json = json.dumps(data["talents"])

        if "traits" in data:
            ship.traits_json = json.dumps(data["traits"])

        if "breaches" in data:
            ship.breaches_json = json.dumps(data["breaches"])

        if "vtt_position" in data:
            ship.vtt_position_json = json.dumps(data["vtt_position"])

        if "vtt_status_effects" in data:
            ship.vtt_status_effects_json = json.dumps(data["vtt_status_effects"])

        session.commit()
        return jsonify(_serialize_ship(ship))
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@ships_bp.route("/api/ships/<int:ship_id>", methods=["DELETE"])
def delete_ship(ship_id: int):
    """Delete ship (GM only)."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        if ship.campaign_id:
            gm_player, error_response, status = _require_gm_auth(
                session, ship.campaign_id
            )
            if error_response:
                return error_response, status

        session.delete(ship)
        session.commit()
        return jsonify({"success": True})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Ship Model Endpoint
# =============================================================================


@ships_bp.route("/api/ships/<int:ship_id>/model", methods=["GET"])
def get_ship_model(ship_id: int):
    """Return ship as legacy Starship model."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        model = ship.to_model()

        return jsonify(
            {
                "name": model.name,
                "ship_class": model.ship_class,
                "registry": model.registry,
                "scale": model.scale,
                "systems": {
                    "comms": model.systems.comms,
                    "computers": model.systems.computers,
                    "engines": model.systems.engines,
                    "sensors": model.systems.sensors,
                    "structure": model.systems.structure,
                    "weapons": model.systems.weapons,
                },
                "departments": {
                    "command": model.departments.command,
                    "conn": model.departments.conn,
                    "engineering": model.departments.engineering,
                    "medicine": model.departments.medicine,
                    "science": model.departments.science,
                    "security": model.departments.security,
                },
                "weapons": [
                    {
                        "name": w.name,
                        "weapon_type": w.weapon_type.value,
                        "damage": w.damage,
                        "range": w.range.value,
                        "qualities": w.qualities,
                        "requires_calibration": w.requires_calibration,
                    }
                    for w in model.weapons
                ],
                "talents": model.talents,
                "traits": model.traits,
                "breaches": [
                    {"system": b.system.value, "potency": b.potency}
                    for b in model.breaches
                ],
                "shields": model.shields,
                "shields_max": model.shields_max,
                "resistance": model.resistance,
                "has_reserve_power": model.has_reserve_power,
                "shields_raised": model.shields_raised,
                "weapons_armed": model.weapons_armed,
                "crew_quality": model.crew_quality.value
                if model.crew_quality
                else None,
            }
        )
    finally:
        session.close()


# =============================================================================
# Ship Shields Endpoints
# =============================================================================


@ships_bp.route("/api/ships/<int:ship_id>/shields", methods=["PUT"])
def adjust_shields(ship_id: int):
    """Adjust shields (body: {shields: int, raised: bool})."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        if "shields" in data:
            shields = data["shields"]
            if not (0 <= shields <= ship.shields_max):
                return jsonify(
                    {
                        "error": f"Shields must be between 0-{ship.shields_max}, got {shields}"
                    }
                ), 400
            ship.shields = shields

        if "raised" in data:
            ship.shields_raised = data["raised"]

        session.commit()

        return jsonify(
            {
                "shields": ship.shields,
                "shields_max": ship.shields_max,
                "shields_raised": ship.shields_raised,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Ship Power Endpoints
# =============================================================================


@ships_bp.route("/api/ships/<int:ship_id>/power", methods=["PUT"])
def adjust_power(ship_id: int):
    """Adjust power (body: {current: int, reserve: bool})."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        if "current" in data:
            current = data["current"]
            if current not in [0, 1]:
                return jsonify({"error": "current power must be 0 or 1"}), 400
            ship.has_reserve_power = current == 1

        if "reserve" in data:
            ship.has_reserve_power = data["reserve"]

        session.commit()

        return jsonify(
            {
                "has_reserve_power": ship.has_reserve_power,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Ship Breach Endpoints
# =============================================================================


@ships_bp.route("/api/ships/<int:ship_id>/breach", methods=["PUT"])
def adjust_breach(ship_id: int):
    """Add/remove system breach (body: {system: string, potency: int, action: "add"|"remove"})."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        system = data.get("system")
        if not system:
            return jsonify({"error": "system is required"}), 400

        try:
            system_type = SystemType(system)
        except ValueError:
            valid_systems = [s.value for s in SystemType]
            return jsonify(
                {"error": f"Invalid system. Must be one of {valid_systems}"}
            ), 400

        action = data.get("action", "add")
        potency = data.get("potency", 1)

        breaches = json.loads(ship.breaches_json)

        if action == "add":
            existing = [b for b in breaches if b["system"] == system]
            if existing:
                existing[0]["potency"] = potency
            else:
                breaches.append({"system": system, "potency": potency})
        elif action == "remove":
            breaches = [b for b in breaches if b["system"] != system]
        else:
            return jsonify({"error": "action must be 'add' or 'remove'"}), 400

        ship.breaches_json = json.dumps(breaches)
        session.commit()

        return jsonify(
            {
                "breaches": breaches,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Ship Weapons Endpoints
# =============================================================================


@ships_bp.route("/api/ships/<int:ship_id>/weapons", methods=["PUT"])
def update_weapons(ship_id: int):
    """Update weapons list."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json()
        if not data or "weapons" not in data:
            return jsonify({"error": "weapons is required"}), 400

        weapons = data["weapons"]
        ship.weapons_json = json.dumps(weapons)
        session.commit()

        return jsonify(
            {
                "weapons": weapons,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@ships_bp.route("/api/ships/<int:ship_id>/weapons/<weapon_name>/arm", methods=["POST"])
def arm_weapon(ship_id: int, weapon_name: str):
    """Arm/disarm weapon."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json() or {}
        armed = data.get("armed", True)

        weapons = json.loads(ship.weapons_json)

        weapon_found = False
        for weapon in weapons:
            if weapon.get("name") == weapon_name:
                weapon_found = True
                break

        if not weapon_found:
            return jsonify({"error": f"Weapon '{weapon_name}' not found"}), 404

        ship.weapons_armed = armed
        session.commit()

        return jsonify(
            {
                "weapons_armed": ship.weapons_armed,
                "weapon_name": weapon_name,
                "armed": armed,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# =============================================================================
# Ship Crew Quality Endpoints
# =============================================================================


@ships_bp.route("/api/ships/<int:ship_id>/crew-quality", methods=["GET"])
def get_crew_quality(ship_id: int):
    """Get crew quality (NPC ships only)."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        return jsonify(
            {
                "crew_quality": ship.crew_quality,
            }
        )
    finally:
        session.close()


@ships_bp.route("/api/ships/<int:ship_id>/crew-quality", methods=["PUT"])
def set_crew_quality(ship_id: int):
    """Set crew quality (NPC ships only, body: {crew_quality: string})."""
    session = get_session()
    try:
        ship = session.query(VTTShipRecord).filter_by(id=ship_id).first()
        if not ship:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json()
        if not data or "crew_quality" not in data:
            return jsonify({"error": "crew_quality is required"}), 400

        crew_quality = data["crew_quality"]

        if crew_quality is not None:
            try:
                CrewQuality(crew_quality)
            except ValueError:
                valid_qualities = [q.value for q in CrewQuality]
                return jsonify(
                    {"error": f"crew_quality must be one of {valid_qualities}"}
                ), 400

        ship.crew_quality = crew_quality
        session.commit()

        return jsonify(
            {
                "crew_quality": ship.crew_quality,
            }
        )
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
