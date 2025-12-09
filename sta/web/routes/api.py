"""API routes for AJAX operations."""

import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from sta.database import get_session, EncounterRecord, StarshipRecord, CharacterRecord, CombatLogRecord
from sta.mechanics import task_roll, assisted_task_roll
from sta.models.enums import SystemType, TerrainType, Range
from sta.models.combat import ActiveEffect, HexCoord, TacticalMap, HexTile
from sta.mechanics.action_handlers import (
    execute_buff_action,
    execute_task_roll_action,
    apply_task_roll_success,
    check_action_requirements,
    apply_effects_to_attack,
    apply_effects_to_defense,
    execute_defensive_fire,
    execute_reroute_power,
    get_reroute_power_bonus,
    consume_reroute_power_effect,
    ActionCompletionManager,
)
from sta.mechanics.action_config import (
    get_action_config,
    is_buff_action,
    is_task_roll_action,
    is_toggle_action,
    is_npc_action,
    is_action_available,
    get_breach_difficulty_modifier,
    get_all_actions_availability,
    check_action_range,
    get_range_difficulty_modifier as get_action_range_difficulty_modifier,
)

api_bp = Blueprint("api", __name__)


def get_bonus_dice_cost(num_dice: int) -> int:
    """Calculate momentum cost for bonus dice (escalating: 1st=1, 2nd=2, 3rd=3).

    Cost: 1 die = 1, 2 dice = 1+2=3, 3 dice = 1+2+3=6
    """
    if num_dice <= 0:
        return 0
    if num_dice == 1:
        return 1
    if num_dice == 2:
        return 3
    return 6  # 3 dice


def get_max_range_distance(weapon_range: Range) -> int:
    """Convert a weapon's Range to max hex distance.

    Range mapping (STA 2e with hex grid):
    - CONTACT: 0 (must be docked/landed - special state)
    - CLOSE: 0 hexes (same hex)
    - MEDIUM: 1 hex
    - LONG: 2 hexes
    - EXTREME: 3+ hexes (effectively unlimited on standard map)
    """
    if weapon_range == Range.CONTACT:
        return 0
    if weapon_range == Range.CLOSE:
        return 0
    if weapon_range == Range.MEDIUM:
        return 1
    if weapon_range == Range.LONG:
        return 2
    return 999  # EXTREME - no practical limit


def get_range_name_for_distance(distance: int) -> str:
    """Convert hex distance to STA range name."""
    if distance == 0:
        return "Close"
    if distance == 1:
        return "Medium"
    if distance == 2:
        return "Long"
    return "Extreme"


def get_ship_positions_from_encounter(encounter) -> dict:
    """Extract ship positions from encounter's JSON data."""
    try:
        return json.loads(encounter.ship_positions_json) if encounter.ship_positions_json else {}
    except json.JSONDecodeError:
        return {}


def get_tactical_map_from_encounter(encounter) -> dict:
    """Extract tactical map data from encounter's JSON data."""
    try:
        return json.loads(encounter.tactical_map_json) if encounter.tactical_map_json else {}
    except json.JSONDecodeError:
        return {}


# Terrain types that block visibility
VISIBILITY_BLOCKING_TERRAIN = ["dust_cloud", "dense_nebula"]


def get_terrain_at_position(tactical_map: dict, q: int, r: int) -> str:
    """Get the terrain type at a given hex position."""
    tiles = tactical_map.get("tiles", [])
    for tile in tiles:
        coord = tile.get("coord", {})
        if coord.get("q") == q and coord.get("r") == r:
            return tile.get("terrain", "open")
    return "open"


def is_ship_visible_to_player(
    player_pos: dict,
    enemy_pos: dict,
    tactical_map: dict,
    detected_positions: list = None
) -> bool:
    """
    Determine if an enemy ship is visible to the player.

    Visibility rules:
    - Ships in visibility-blocked terrain (dust_cloud, dense_nebula) are hidden
    - UNLESS the player is in the same hex
    - OR the position has been detected via Sensor Sweep

    Args:
        player_pos: Player ship position {"q": int, "r": int}
        enemy_pos: Enemy ship position {"q": int, "r": int}
        tactical_map: Tactical map data with tiles
        detected_positions: List of positions that have been scanned/detected

    Returns:
        True if the enemy ship is visible to the player
    """
    if detected_positions is None:
        detected_positions = []

    player_q = player_pos.get("q", 0)
    player_r = player_pos.get("r", 0)
    enemy_q = enemy_pos.get("q", 0)
    enemy_r = enemy_pos.get("r", 0)

    # Get terrain at enemy position
    enemy_terrain = get_terrain_at_position(tactical_map, enemy_q, enemy_r)

    # If enemy is not in visibility-blocked terrain, they're visible
    if enemy_terrain not in VISIBILITY_BLOCKING_TERRAIN:
        return True

    # Enemy is in visibility-blocked terrain

    # Check if player is in the same hex (Close range)
    if player_q == enemy_q and player_r == enemy_r:
        return True

    # Check if position has been detected via Sensor Sweep
    for detected in detected_positions:
        if detected.get("q") == enemy_q and detected.get("r") == enemy_r:
            return True

    # Ship is hidden
    return False


def get_detected_positions_from_effects(active_effects: list) -> list:
    """
    Extract detected positions from active effects.

    Sensor Sweep creates effects with detected_position data.
    """
    detected = []
    for effect in active_effects:
        if hasattr(effect, 'detected_position') and effect.detected_position:
            detected.append(effect.detected_position)
        elif isinstance(effect, dict) and effect.get('detected_position'):
            detected.append(effect['detected_position'])
    return detected



@api_bp.route("/roll", methods=["POST"])
def roll_dice():
    """Perform a task roll."""
    data = request.json
    attribute = data.get("attribute", 7)
    discipline = data.get("discipline", 1)
    difficulty = data.get("difficulty", 1)
    focus = data.get("focus", False)
    bonus_dice = data.get("bonus_dice", 0)

    result = task_roll(
        attribute=attribute,
        discipline=discipline,
        difficulty=difficulty,
        focus=focus,
        bonus_dice=bonus_dice
    )

    return jsonify({
        "rolls": result.rolls,
        "target_number": result.target_number,
        "successes": result.successes,
        "complications": result.complications,
        "difficulty": result.difficulty,
        "succeeded": result.succeeded,
        "momentum_generated": result.momentum_generated,
    })


@api_bp.route("/roll-assisted", methods=["POST"])
def roll_assisted_dice():
    """Perform an assisted task roll (character + ship assist die)."""
    data = request.json
    attribute = data.get("attribute", 7)
    discipline = data.get("discipline", 1)
    system = data.get("system", 7)
    department = data.get("department", 1)
    difficulty = data.get("difficulty", 1)
    focus = data.get("focus", False)
    bonus_dice = data.get("bonus_dice", 0)

    result = assisted_task_roll(
        attribute=attribute,
        discipline=discipline,
        system=system,
        department=department,
        difficulty=difficulty,
        focus=focus,
        bonus_dice=bonus_dice
    )

    return jsonify({
        "rolls": result.rolls,
        "target_number": result.target_number,
        "successes": result.successes,
        "complications": result.complications,
        "difficulty": result.difficulty,
        "succeeded": result.succeeded,
        "momentum_generated": result.momentum_generated,
    })


@api_bp.route("/action-config/<action_name>", methods=["GET"])
def get_action_config_endpoint(action_name: str):
    """Get the configuration for an action, including roll requirements."""
    config = get_action_config(action_name)
    if not config:
        return jsonify({"error": f"Unknown action: {action_name}"}), 404

    # Return just the relevant info for the frontend
    result = {
        "name": action_name,
        "type": config.get("type"),
    }

    if is_task_roll_action(action_name):
        roll_config = config.get("roll", {})
        result["roll"] = {
            "attribute": roll_config.get("attribute"),
            "discipline": roll_config.get("discipline"),
            "difficulty": roll_config.get("difficulty", 1),
            "focus_eligible": roll_config.get("focus_eligible", True),
            "ship_assist_system": roll_config.get("ship_assist_system"),
            "ship_assist_department": roll_config.get("ship_assist_department"),
        }

    return jsonify(result)


@api_bp.route("/encounter/<encounter_id>/action-availability", methods=["GET"])
def get_action_availability(encounter_id: str):
    """Get availability of all actions based on ship breach status.

    Returns a dict mapping action names to their availability info:
    - available: bool - whether the action can be used
    - reason: str or null - reason if unavailable (e.g., "WEAPONS DESTROYED")
    - breach_modifier: int - difficulty modifier from breaches
    - required_system: str or null - the system this action requires
    """
    session = get_session()
    try:
        # Load encounter
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Load player ship
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter.player_ship_id
        ).first()
        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404
        player_ship = player_ship_record.to_model()

        # Get availability for all actions
        availability = get_all_actions_availability(player_ship)

        return jsonify(availability)
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/momentum", methods=["POST"])
def update_momentum(encounter_id: str):
    """Update encounter momentum."""
    data = request.json
    change = data.get("change", 0)

    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        encounter.momentum = max(0, min(6, encounter.momentum + change))
        session.commit()

        return jsonify({"momentum": encounter.momentum})
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/threat", methods=["POST"])
def update_threat(encounter_id: str):
    """Update encounter threat."""
    data = request.json
    change = data.get("change", 0)

    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        encounter.threat = max(0, encounter.threat + change)
        session.commit()

        return jsonify({"threat": encounter.threat})
    finally:
        session.close()


@api_bp.route("/ship/<int:ship_id>/damage", methods=["POST"])
def apply_damage(ship_id: int):
    """Apply damage to a ship."""
    data = request.json
    damage = data.get("damage", 0)

    session = get_session()
    try:
        ship_record = session.query(StarshipRecord).filter_by(id=ship_id).first()
        if not ship_record:
            return jsonify({"error": "Ship not found"}), 404

        ship = ship_record.to_model()
        result = ship.take_damage(damage)

        # Update the record
        ship_record.shields = ship.shields
        session.commit()

        return jsonify({
            "total_damage": result["total_damage"],
            "shield_damage": result["shield_damage"],
            "hull_damage": result["hull_damage"],
            "shields_remaining": result["shields_remaining"],
            "breaches_caused": result["breaches_caused"],
        })
    finally:
        session.close()


@api_bp.route("/ship/<int:ship_id>/breach", methods=["POST"])
def add_breach(ship_id: int):
    """Add a breach to a ship system."""
    data = request.json
    system = data.get("system", "structure")

    session = get_session()
    try:
        ship_record = session.query(StarshipRecord).filter_by(id=ship_id).first()
        if not ship_record:
            return jsonify({"error": "Ship not found"}), 404

        ship = ship_record.to_model()
        system_type = SystemType(system)
        ship.add_breach(system_type)

        # Update breaches in record
        breaches_data = [
            {"system": b.system.value, "potency": b.potency}
            for b in ship.breaches
        ]
        ship_record.breaches_json = json.dumps(breaches_data)
        session.commit()

        return jsonify({
            "breaches": breaches_data,
            "system_disabled": ship.is_system_disabled(system_type),
        })
    finally:
        session.close()


def get_enemy_turn_info(session, encounter):
    """Calculate enemy turn economy info.

    Returns dict with:
        - total_turns: sum of all enemy ship Scales
        - turns_used: total turns used this round
        - ships_info: list of {ship_id, name, scale, turns_used, turns_remaining}
    """
    enemy_ids = json.loads(encounter.enemy_ship_ids_json)
    ships_turns_used = json.loads(encounter.ships_turns_used_json)

    ships_info = []
    total_turns = 0
    total_used = 0

    for ship_id in enemy_ids:
        ship = session.query(StarshipRecord).filter_by(id=ship_id).first()
        if ship:
            turns_used = ships_turns_used.get(str(ship_id), 0)
            ships_info.append({
                "ship_id": ship_id,
                "name": ship.name,
                "scale": ship.scale,
                "turns_used": turns_used,
                "turns_remaining": ship.scale - turns_used,
                "can_act": turns_used < ship.scale,
            })
            total_turns += ship.scale
            total_used += turns_used

    return {
        "total_turns": total_turns,
        "turns_used": total_used,
        "turns_remaining": total_turns - total_used,
        "ships_info": ships_info,
    }


def get_player_turn_info(session, encounter):
    """Calculate player turn economy info (legacy single-player mode).

    Player turns = player ship's Scale.
    """
    player_ship = session.query(StarshipRecord).filter_by(
        id=encounter.player_ship_id
    ).first()

    if player_ship:
        total_turns = player_ship.scale
    else:
        total_turns = 1  # Fallback

    return {
        "total_turns": total_turns,
        "turns_used": encounter.player_turns_used,
        "turns_remaining": total_turns - encounter.player_turns_used,
    }


def get_multiplayer_turn_info(session, encounter):
    """Calculate player turn economy info for multi-player mode.

    Each player character gets ONE turn per round.
    Returns info about all players and who has/hasn't acted.
    """
    from sta.database import CampaignPlayerRecord

    # Get all active players in this campaign (not GMs)
    if encounter.campaign_id:
        campaign_players = session.query(CampaignPlayerRecord).filter_by(
            campaign_id=encounter.campaign_id,
            is_active=True,
            is_gm=False
        ).all()
    else:
        campaign_players = []

    # Load turn usage data
    players_turns_used = json.loads(encounter.players_turns_used_json or "{}")

    players_info = []
    total_turns = len(campaign_players) if campaign_players else 1
    total_used = 0

    for player in campaign_players:
        player_data = players_turns_used.get(str(player.id), {})
        has_acted = player_data.get("acted", False)
        is_current = encounter.current_player_id == player.id

        players_info.append({
            "player_id": player.id,
            "name": player.player_name,
            "position": player.position,
            "character_id": player.character_id,
            "has_acted": has_acted,
            "acted_at": player_data.get("acted_at"),
            "is_current": is_current,
            "can_claim": not has_acted and encounter.current_player_id is None,
        })

        if has_acted:
            total_used += 1

    # If no campaign players, fall back to legacy single-player info
    if not campaign_players:
        return {
            "total_turns": 1,
            "turns_used": encounter.player_turns_used,
            "turns_remaining": 1 - min(encounter.player_turns_used, 1),
            "players_info": [],
            "current_player_id": encounter.current_player_id,
            "current_player_name": None,
            "is_multiplayer": False,
        }

    # Get current claiming player's name
    current_player_name = None
    if encounter.current_player_id:
        current_player = next(
            (p for p in players_info if p["player_id"] == encounter.current_player_id),
            None
        )
        if current_player:
            current_player_name = current_player["name"]

    return {
        "total_turns": total_turns,
        "turns_used": total_used,
        "turns_remaining": total_turns - total_used,
        "players_info": players_info,
        "current_player_id": encounter.current_player_id,
        "current_player_name": current_player_name,
        "turn_claimed_at": encounter.turn_claimed_at.isoformat() if encounter.turn_claimed_at else None,
        "is_multiplayer": True,
    }


def alternate_turn_after_action(session, encounter, player_id: int = None):
    """Handle turn alternation after a major action.

    STA 2e initiative alternates between sides after each turn.
    After current side takes a turn:
    1. Check if OTHER side has turns remaining - if yes, switch to them
    2. If other side has no turns, stay on current side
    3. If BOTH sides exhausted, advance round and reset

    Args:
        session: Database session
        encounter: EncounterRecord
        player_id: If provided, marks this player as having acted (multi-player mode)

    Returns dict with turn state info.
    """
    # If a player_id was provided, mark them as acted in multi-player mode
    if player_id is not None:
        players_turns_used = json.loads(encounter.players_turns_used_json or "{}")
        players_turns_used[str(player_id)] = {
            "acted": True,
            "acted_at": datetime.now().isoformat(),
        }
        encounter.players_turns_used_json = json.dumps(players_turns_used)

    # Clear any turn claim (player finished their action)
    encounter.current_player_id = None
    encounter.turn_claimed_at = None

    enemy_info = get_enemy_turn_info(session, encounter)
    player_info = get_player_turn_info(session, encounter)
    multiplayer_info = get_multiplayer_turn_info(session, encounter)

    enemy_has_turns = enemy_info["turns_remaining"] > 0

    # For multi-player, check if any player hasn't acted yet
    if multiplayer_info["is_multiplayer"]:
        player_has_turns = multiplayer_info["turns_remaining"] > 0
    else:
        player_has_turns = player_info["turns_remaining"] > 0

    round_advanced = False

    if not enemy_has_turns and not player_has_turns:
        # Both sides exhausted - advance round
        encounter.round += 1
        encounter.player_turns_used = 0
        encounter.ships_turns_used_json = "{}"
        encounter.players_turns_used_json = "{}"  # Reset multi-player tracking too
        # New round starts with player (or could alternate who starts)
        encounter.current_turn = "player"
        round_advanced = True
        # Recalculate after reset
        enemy_info = get_enemy_turn_info(session, encounter)
        player_info = get_player_turn_info(session, encounter)
        multiplayer_info = get_multiplayer_turn_info(session, encounter)
    elif encounter.current_turn == "enemy":
        # Enemy just acted - switch to player if they have turns
        if player_has_turns:
            encounter.current_turn = "player"
        # else stay on enemy (they get consecutive turns)
    else:
        # Player just acted - switch to enemy if they have turns
        if enemy_has_turns:
            encounter.current_turn = "enemy"
        # else stay on player (they get consecutive turns)

    return {
        "current_turn": encounter.current_turn,
        "round": encounter.round,
        "round_advanced": round_advanced,
        "enemy_turns_used": enemy_info["turns_used"],
        "enemy_turns_total": enemy_info["total_turns"],
        "enemy_turns_remaining": enemy_info["turns_remaining"],
        "player_turns_used": encounter.player_turns_used,
        "player_turns_total": player_info["total_turns"],
        "player_turns_remaining": player_info["turns_remaining"],
        "ships_info": enemy_info["ships_info"],
        # Multi-player info
        "is_multiplayer": multiplayer_info["is_multiplayer"],
        "current_player_id": multiplayer_info["current_player_id"],
        "players_info": multiplayer_info["players_info"],
    }


def log_combat_action(
    session,
    encounter_record,
    actor_name: str,
    actor_type: str,  # "player" or "enemy"
    ship_name: str,
    action_name: str,
    action_type: str,  # "minor" or "major"
    description: str,
    task_result: dict = None,
    damage_dealt: int = 0,
    momentum_spent: int = 0,
    threat_spent: int = 0,
):
    """Log a combat action to the database.

    Args:
        session: Database session
        encounter_record: The EncounterRecord for this encounter
        actor_name: Name of the character/crew taking the action
        actor_type: "player" or "enemy"
        ship_name: Name of the ship performing the action
        action_name: Name of the action (e.g., "Fire Phasers", "Evasive Action")
        action_type: "minor" or "major"
        description: Human-readable description of what happened
        task_result: Optional dict with roll results (rolls, successes, etc.)
        damage_dealt: Amount of damage dealt (if any)
        momentum_spent: Momentum spent on this action
        threat_spent: Threat spent on this action
    """
    log_entry = CombatLogRecord(
        encounter_id=encounter_record.id,  # Use the primary key, not the UUID
        round=encounter_record.round,
        actor_name=actor_name,
        actor_type=actor_type,
        ship_name=ship_name,
        action_name=action_name,
        action_type=action_type,
        description=description,
        task_result_json=json.dumps(task_result) if task_result else None,
        damage_dealt=damage_dealt,
        momentum_spent=momentum_spent,
        threat_spent=threat_spent,
    )
    session.add(log_entry)


@api_bp.route("/encounter/<encounter_id>/next-turn", methods=["POST"])
def next_turn(encounter_id: str):
    """Manually end the current side's remaining turns and switch to other side.

    This is used when a side wants to pass/end their turn early.
    The other side then gets to take turns until they pass or exhaust turns.
    """
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        enemy_info = get_enemy_turn_info(session, encounter)
        player_info = get_player_turn_info(session, encounter)

        # Mark current side as having used all their turns
        if encounter.current_turn == "player":
            # Player passes - mark all their turns as used
            encounter.player_turns_used = player_info["total_turns"]
        else:
            # Enemy passes - mark all enemy turns as used
            ships_turns_used = json.loads(encounter.ships_turns_used_json)
            for ship_info in enemy_info["ships_info"]:
                ships_turns_used[str(ship_info["ship_id"])] = ship_info["scale"]
            encounter.ships_turns_used_json = json.dumps(ships_turns_used)

        # Now alternate to determine next turn owner
        turn_result = alternate_turn_after_action(session, encounter)

        session.commit()

        return jsonify({
            "current_turn": turn_result["current_turn"],
            "round": turn_result["round"],
            "round_advanced": turn_result["round_advanced"],
            "player_turns_used": turn_result["player_turns_used"],
            "player_turns_total": turn_result["player_turns_total"],
            "enemy_turns_used": turn_result["enemy_turns_used"],
            "enemy_turns_total": turn_result["enemy_turns_total"],
            "ships_info": turn_result["ships_info"],
        })
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/status", methods=["GET"])
def get_encounter_status(encounter_id: str):
    """Get current encounter status (for polling)."""
    role = request.args.get("role", "player")

    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Get turn info for both sides
        enemy_turn_info = get_enemy_turn_info(session, encounter)
        player_turn_info = get_player_turn_info(session, encounter)
        multiplayer_info = get_multiplayer_turn_info(session, encounter)

        # Check for pending attack that needs player defensive roll
        pending_attack = None
        if encounter.pending_attack_json:
            pending_attack = json.loads(encounter.pending_attack_json)

        # Get player ship's reserve power status
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter.player_ship_id
        ).first()
        has_reserve_power = player_ship_record.has_reserve_power if player_ship_record else True

        # Filter ships_info by visibility for player role
        ships_info = enemy_turn_info["ships_info"]
        if role == "player":
            # Load visibility data
            tactical_map = json.loads(encounter.tactical_map_json or "{}")
            ship_positions = json.loads(encounter.ship_positions_json or "{}")
            player_pos = ship_positions.get("player", {"q": 0, "r": 0})

            # Load active effects for detection
            active_effects_data = json.loads(encounter.active_effects_json)
            active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]
            detected_positions = get_detected_positions_from_effects(active_effects)

            # Filter ships to only visible ones
            visible_ships = []
            for i, ship_info in enumerate(ships_info):
                enemy_pos = ship_positions.get(f"enemy_{i}", {"q": 0, "r": 0})
                if is_ship_visible_to_player(player_pos, enemy_pos, tactical_map, detected_positions):
                    visible_ships.append(ship_info)
            ships_info = visible_ships

        return jsonify({
            "current_turn": encounter.current_turn,
            "round": encounter.round,
            "momentum": encounter.momentum,
            "threat": encounter.threat,
            "player_turns_used": player_turn_info["turns_used"],
            "player_turns_total": player_turn_info["total_turns"],
            "player_turns_remaining": player_turn_info["turns_remaining"],
            "enemy_turns_used": enemy_turn_info["turns_used"],
            "enemy_turns_total": enemy_turn_info["total_turns"],
            "enemy_turns_remaining": enemy_turn_info["turns_remaining"],
            "ships_info": ships_info,
            "pending_attack": pending_attack,
            "has_reserve_power": has_reserve_power,
            # Multi-player turn info
            "is_multiplayer": multiplayer_info["is_multiplayer"],
            "current_player_id": multiplayer_info["current_player_id"],
            "current_player_name": multiplayer_info["current_player_name"],
            "players_info": multiplayer_info["players_info"],
        })
    finally:
        session.close()


# ========== MULTI-PLAYER TURN CLAIMING ENDPOINTS ==========

@api_bp.route("/encounter/<encounter_id>/claim-turn", methods=["POST"])
def claim_turn(encounter_id: str):
    """Claim the turn for a player in multi-player mode.

    Request body:
    - player_id: ID of the player claiming the turn

    Returns success/failure and who has the turn claimed.
    Uses timestamp-based conflict resolution for race conditions.
    """
    from sta.database import CampaignPlayerRecord

    session = get_session()
    try:
        data = request.json or {}
        player_id = data.get("player_id")

        if not player_id:
            return jsonify({"error": "player_id is required"}), 400

        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Check it's the player side's turn
        if encounter.current_turn != "player":
            return jsonify({
                "success": False,
                "error": "It's not the player side's turn",
                "current_turn": encounter.current_turn,
            }), 400

        # Check player hasn't already acted this round
        players_turns_used = json.loads(encounter.players_turns_used_json or "{}")
        player_data = players_turns_used.get(str(player_id), {})
        if player_data.get("acted", False):
            return jsonify({
                "success": False,
                "error": "You have already acted this round",
            }), 400

        # Check if turn is already claimed by someone else
        if encounter.current_player_id is not None and encounter.current_player_id != player_id:
            # Get the claiming player's name
            claiming_player = session.query(CampaignPlayerRecord).filter_by(
                id=encounter.current_player_id
            ).first()
            claiming_name = claiming_player.player_name if claiming_player else "Another player"

            return jsonify({
                "success": False,
                "confirmed": False,
                "claimed_by": claiming_name,
                "claimed_by_id": encounter.current_player_id,
            })

        # Claim the turn
        encounter.current_player_id = player_id
        encounter.turn_claimed_at = datetime.now()
        session.commit()

        # Get player info for confirmation
        player = session.query(CampaignPlayerRecord).filter_by(id=player_id).first()
        player_name = player.player_name if player else "Unknown"

        return jsonify({
            "success": True,
            "confirmed": True,
            "player_id": player_id,
            "player_name": player_name,
            "message": f"{player_name} has claimed the turn",
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/release-turn", methods=["POST"])
def release_turn(encounter_id: str):
    """Release a claimed turn without acting.

    Can be called by:
    - The player who claimed the turn (to change their mind)
    - The GM (with force=true) to release an AFK player's turn

    Request body (optional):
    - player_id: ID of the player (for GM force release)
    - force: true to force release (GM only)
    """
    session = get_session()
    try:
        data = request.json or {}
        force = data.get("force", False)

        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        if encounter.current_player_id is None:
            return jsonify({
                "success": True,
                "message": "No turn was claimed",
            })

        # Store who had the turn for the response
        released_player_id = encounter.current_player_id

        # Clear the turn claim
        encounter.current_player_id = None
        encounter.turn_claimed_at = None
        session.commit()

        return jsonify({
            "success": True,
            "message": "Turn released",
            "released_player_id": released_player_id,
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/reserve-power", methods=["POST"])
def toggle_reserve_power(encounter_id: str):
    """Toggle the player ship's reserve power status (GM override)."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter.player_ship_id
        ).first()

        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404

        # Toggle reserve power
        player_ship_record.has_reserve_power = not player_ship_record.has_reserve_power
        session.commit()

        return jsonify({
            "success": True,
            "has_reserve_power": player_ship_record.has_reserve_power,
            "message": f"Reserve Power {'restored' if player_ship_record.has_reserve_power else 'depleted'}!"
        })
    finally:
        session.close()


@api_bp.route("/fire", methods=["POST"])
def fire_weapon():
    """Execute a Fire action with full damage resolution.

    Fire action uses Control + Security, assisted by ship's Weapons + Security.
    This means the character rolls 2d20 (plus bonus dice) and the ship provides
    an additional assistance die with its own target number.
    """
    import random

    data = request.json
    encounter_id = data.get("encounter_id")
    weapon_index = data.get("weapon_index", 0)
    target_index = data.get("target_index", 0)
    attribute = data.get("attribute", 9)  # Character's Control
    discipline = data.get("discipline", 3)  # Character's Security
    difficulty = data.get("difficulty", 2)
    focus = data.get("focus", False)
    bonus_dice = data.get("bonus_dice", 0)
    reroll_die_index = data.get("reroll_die_index")  # Index of die to re-roll (if any)
    previous_rolls = data.get("previous_rolls")  # Previous roll results (for re-roll)
    role = data.get("role", "player")  # Default to player
    character_id = data.get("character_id")  # Optional: override acting character for logging

    # Check turn ownership for player fire actions
    if role == "player":
        session = get_session()
        try:
            enc = session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()
            if enc and enc.current_turn != "player":
                return jsonify({"error": "It's not the player's turn!"}), 403
        finally:
            session.close()

    session = get_session()
    try:
        # Load encounter
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Load player ship
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter.player_ship_id
        ).first()
        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404
        player_ship = player_ship_record.to_model()

        # Check if weapons are armed
        if not player_ship.weapons_armed:
            return jsonify({"error": "Weapons are not armed! Use Arm Weapons first."}), 400

        # Check if weapons system is destroyed (breaches >= half Scale)
        available, reason = is_action_available("Fire", player_ship)
        if not available:
            return jsonify({"error": f"Cannot fire: {reason}"}), 400

        # Apply breach modifier to difficulty
        breach_modifier = get_breach_difficulty_modifier("Fire", player_ship)
        if breach_modifier > 0:
            difficulty = difficulty + breach_modifier

        # Load target ship
        enemy_ids = json.loads(encounter.enemy_ship_ids_json)
        if target_index >= len(enemy_ids):
            return jsonify({"error": "Invalid target"}), 400

        target_id = enemy_ids[target_index]
        target_record = session.query(StarshipRecord).filter_by(id=target_id).first()
        if not target_record:
            return jsonify({"error": "Target ship not found"}), 404
        target_ship = target_record.to_model()

        # Get weapon
        if weapon_index >= len(player_ship.weapons):
            return jsonify({"error": "Invalid weapon"}), 400
        weapon = player_ship.weapons[weapon_index]

        # Check weapon range vs target distance
        ship_positions = get_ship_positions_from_encounter(encounter)
        player_pos = ship_positions.get("player", {"q": 0, "r": 0})
        target_pos = ship_positions.get(f"enemy_{target_index}", {"q": 0, "r": 0})
        player_coord = HexCoord(q=player_pos.get("q", 0), r=player_pos.get("r", 0))
        target_coord = HexCoord(q=target_pos.get("q", 0), r=target_pos.get("r", 0))
        hex_distance = player_coord.distance_to(target_coord)
        max_weapon_range = get_max_range_distance(weapon.range)

        if hex_distance > max_weapon_range:
            current_range = get_range_name_for_distance(hex_distance)
            weapon_range_name = weapon.range.value.title()
            return jsonify({
                "error": f"Target is out of range! {weapon.name} has {weapon_range_name} range ({max_weapon_range} hex{'es' if max_weapon_range != 1 else ''}), but target is at {current_range} range ({hex_distance} hex{'es' if hex_distance != 1 else ''})."
            }), 400

        # Load active effects to check for can_reroll
        active_effects_data = json.loads(encounter.active_effects_json)
        active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]
        from sta.models.combat import Encounter as EncounterModel
        encounter_model = EncounterModel(
            id=encounter.encounter_id,
            active_effects=active_effects,
            momentum=encounter.momentum,
        )

        # Validate and deduct momentum for bonus dice (escalating: 1st=1, 2nd=2, 3rd=3)
        if role == "player" and bonus_dice > 0:
            bonus_dice = min(bonus_dice, 3)  # Cap at 3 per STA rules
            cost = get_bonus_dice_cost(bonus_dice)
            if cost > encounter.momentum:
                return jsonify({"error": f"Not enough Momentum! Need {cost} for {bonus_dice} dice, have {encounter.momentum}"}), 400
            encounter.momentum -= cost
            encounter_model.momentum = encounter.momentum

        # Check for Reroute Power effect on weapons system
        reroute_bonus, reroute_effect = get_reroute_power_bonus(encounter_model, "weapons")
        if reroute_bonus != 0:
            difficulty = max(0, difficulty + reroute_bonus)  # Apply modifier (negative = easier)

        # Check for Attack Pattern effect (-1 difficulty for ship's attacks)
        attack_pattern_modifier = 0
        for effect in encounter_model.get_effects("attack") + encounter_model.get_effects("all"):
            if effect.source_action == "Attack Pattern" and effect.difficulty_modifier != 0:
                attack_pattern_modifier = effect.difficulty_modifier
                break
        if attack_pattern_modifier != 0:
            difficulty = max(0, difficulty + attack_pattern_modifier)

        # Check for Evasive Action effect (+1 difficulty for ship's own attacks)
        evasive_action_modifier = 0
        for effect in encounter_model.get_effects("defense"):
            if effect.source_action == "Evasive Action":
                evasive_action_modifier = 1  # +1 difficulty penalty for attacking while evasive
                break
        if evasive_action_modifier != 0:
            difficulty = difficulty + evasive_action_modifier

        # Check Targeting Solution effects
        attack_effects = encounter_model.get_effects("attack")
        has_targeting_solution = any(e.can_reroll or e.can_choose_system for e in attack_effects)

        # Targeting Solution allows: re-roll OR choose system (not both)
        # Check if this is a re-roll request
        is_reroll_request = reroll_die_index is not None and previous_rolls is not None

        # Handle re-roll if requested
        rerolled = False
        if is_reroll_request and has_targeting_solution:
            # Re-roll the specified die
            if 0 <= reroll_die_index < len(previous_rolls):
                result = assisted_task_roll(
                    attribute=attribute,
                    discipline=discipline,
                    system=player_ship.systems.weapons,
                    department=player_ship.departments.security,
                    difficulty=difficulty,
                    focus=focus,
                    bonus_dice=bonus_dice
                )
                # Use previous rolls but replace one die
                result.rolls = previous_rolls.copy()
                result.rolls[reroll_die_index] = random.randint(1, 20)

                # Recalculate successes with the new roll
                successes = 0
                complications = 0
                for roll in result.rolls:
                    if roll == 1:
                        successes += 2  # Critical success
                    elif roll <= result.target_number:
                        successes += 1
                    elif focus and roll <= discipline:
                        successes += 1  # Focus applies
                    if roll == 20:
                        complications += 1

                # Ship assist die is not re-rolled
                if result.ship_successes:
                    successes += result.ship_successes

                result.successes = successes
                result.complications = complications
                result.succeeded = successes >= difficulty
                result.momentum_generated = max(0, successes - difficulty) if result.succeeded else 0

                # Consume the can_reroll effect
                encounter_model.clear_effects(applies_to="attack", duration="next_action")
                rerolled = True
            else:
                return jsonify({"error": "Invalid reroll_die_index"}), 400
        else:
            # Normal roll (no re-roll)
            result = assisted_task_roll(
                attribute=attribute,
                discipline=discipline,
                system=player_ship.systems.weapons,
                department=player_ship.departments.security,
                difficulty=difficulty,
                focus=focus,
                bonus_dice=bonus_dice
            )

        # Targeting Solution: can re-roll OR choose system, but not both
        # - First roll: can_reroll=True, can_choose_system=True (both available)
        # - After re-roll: can_reroll=False, can_choose_system=False (TS consumed for re-roll)
        can_reroll = has_targeting_solution and not rerolled
        can_choose_system = has_targeting_solution and not rerolled  # Available until re-roll is used

        # Consume Reroute Power effect if it was used (it's a "next action" effect)
        reroute_consumed = None
        if reroute_effect:
            reroute_consumed = consume_reroute_power_effect(encounter_model, "weapons")

        response = {
            "rolls": result.rolls,
            "target_number": result.target_number,
            "successes": result.successes,
            "complications": result.complications,
            "difficulty": difficulty,
            "succeeded": result.succeeded,
            "momentum_generated": result.momentum_generated,
            # Ship assistance info for display
            "ship_target_number": result.ship_target_number,
            "ship_roll": result.ship_roll,
            "ship_successes": result.ship_successes,
            # Targeting Solution support
            "can_reroll": can_reroll,
            "can_choose_system": can_choose_system,
            "rerolled": rerolled,
            # Reroute Power info
            "reroute_power_bonus": reroute_bonus if reroute_effect else 0,
        }

        if result.succeeded:
            # Calculate damage per STA 2e rules:
            # 1. Determine base damage
            # 2. Apply active effects (buffs)
            # 3. Apply Resistance (minimum 1 damage)
            # 4. Complications reduce damage by 1 each
            # 5. Apply to shields, then hull

            base_damage_raw = weapon.damage + player_ship.weapons_damage_bonus()

            # Apply active effects to attack
            base_damage, cleared_effects, effect_details = apply_effects_to_attack(
                encounter_model, base_damage_raw, target_ship.resistance
            )

            # Apply defensive effects to target's resistance
            effective_resistance, _, defense_details = apply_effects_to_defense(
                encounter_model, target_ship.resistance
            )

            # Save cleared effects back to database
            encounter.active_effects_json = json.dumps([e.to_dict() for e in encounter_model.active_effects])

            # Apply resistance (minimum 1 damage remains)
            damage_after_resistance = max(1, base_damage - effective_resistance)

            # Complications reduce damage by 1 each
            complication_reduction = result.complications
            total_damage = max(0, damage_after_resistance - complication_reduction)

            # Apply to target - shields absorb first (only if raised)
            old_shields = target_ship.shields
            if target_ship.shields_raised and target_ship.shields > 0:
                shield_damage = min(target_ship.shields, total_damage)
                target_ship.shields -= shield_damage
                remaining_damage = total_damage - shield_damage
            else:
                # Shields are down - damage goes straight to hull
                shield_damage = 0
                remaining_damage = total_damage

            # Remaining damage is hull damage (resistance already applied)
            hull_damage = remaining_damage
            breaches_caused = 0
            systems_hit = []

            if hull_damage > 0:
                # Calculate number of breaches: every 5 points of hull damage causes a breach
                if hull_damage >= 5:
                    breaches_caused = hull_damage // 5
                else:
                    # Any hull damage that gets through causes at least 1 breach
                    breaches_caused = 1

                # Roll for each breach - which system is hit
                # Systems are randomly determined; player can change via Targeting Solution after seeing results
                for i in range(breaches_caused):
                    system_roll = random.randint(1, 20)
                    if system_roll == 1:
                        system_hit = "comms"
                    elif system_roll == 2:
                        system_hit = "computers"
                    elif system_roll <= 6:
                        system_hit = "engines"
                    elif system_roll <= 9:
                        system_hit = "sensors"
                    elif system_roll <= 17:
                        system_hit = "structure"
                    else:
                        system_hit = "weapons"

                    # Add breach to target
                    target_ship.add_breach(SystemType(system_hit))
                    systems_hit.append(system_hit)

            # Update target ship in database
            target_record.shields = target_ship.shields
            breaches_data = [
                {"system": b.system.value, "potency": b.potency}
                for b in target_ship.breaches
            ]
            target_record.breaches_json = json.dumps(breaches_data)

            # Update momentum in encounter
            if result.momentum_generated > 0:
                momentum_to_add = min(result.momentum_generated, 6 - encounter.momentum)
                encounter.momentum += momentum_to_add

            session.commit()

            # Get target ship status after damage
            target_status = target_ship.get_status()

            response.update({
                "base_damage": base_damage,
                "damage_bonus": effect_details.get("total_damage_bonus", 0),
                "effects_applied": effect_details.get("effects_applied", []),
                "resistance_reduction": base_damage - damage_after_resistance,
                "complication_reduction": min(complication_reduction, damage_after_resistance),
                "total_damage": total_damage,
                "shield_damage": shield_damage,
                "hull_damage": hull_damage,
                "target_shields_remaining": target_ship.shields,
                "target_resistance": target_ship.resistance,
                "target_resistance_bonus": defense_details.get("total_resistance_bonus", 0),
                "effective_resistance": effective_resistance,
                "defense_effects_applied": defense_details.get("effects_applied", []),
                "breaches_caused": breaches_caused,
                "systems_hit": systems_hit,
                "new_momentum": encounter.momentum,
                # Return updated breach state for the target
                "target_breaches": breaches_data,
                # Ship status
                "target_status": target_status,
            })
        else:
            # Miss - no damage
            response.update({
                "total_damage": 0,
                "shield_damage": 0,
                "hull_damage": 0,
                "target_shields_remaining": target_ship.shields,
                "breaches_caused": 0,
                "systems_hit": [],
                "new_momentum": encounter.momentum,  # Include even on miss (bonus dice may have been spent)
            })

            # Save cleared effects (Reroute Power consumed even on miss)
            encounter.active_effects_json = json.dumps([e.to_dict() for e in encounter_model.active_effects])

        # Get player character for logging (use provided character_id or fall back to encounter default)
        char_id = character_id if character_id else encounter.player_character_id
        player_char = session.query(CharacterRecord).filter_by(id=char_id).first() if char_id else None
        actor_name = player_char.name if player_char else "Tactical Officer"

        # Build description for log
        if result.succeeded:
            damage = response.get("total_damage", 0)
            description = f"Fired {weapon.name} at {target_ship.name}: {result.successes} successes vs difficulty {difficulty}. Hit for {damage} damage."
            if response.get("breaches_caused", 0) > 0:
                description += f" Caused {response['breaches_caused']} breach(es) to {', '.join(response.get('systems_hit', []))}."
        else:
            description = f"Fired {weapon.name} at {target_ship.name}: {result.successes} successes vs difficulty {difficulty}. Missed!"

        # Use ActionCompletionManager for consistent logging and turn handling
        manager = ActionCompletionManager(
            session, encounter,
            alternate_turn_after_action, log_combat_action
        )

        turn_state = manager.complete_player_major(
            actor_name=actor_name,
            ship_name=player_ship.name,
            action_name=f"Fire {weapon.name}",
            description=description,
            task_result={
                "rolls": result.rolls,
                "target_number": result.target_number,
                "successes": result.successes,
                "complications": result.complications,
                "succeeded": result.succeeded,
            },
            damage_dealt=response.get("total_damage", 0),
        )
        response.update(turn_state)

        session.commit()

        return jsonify(response)
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/ram", methods=["POST"])
def ram_action(encounter_id: str):
    """Execute a Ram action - deliberately collide with an enemy ship.

    Ram uses Daring + Conn, assisted by Engines + Conn.
    On success, both ships take collision damage.

    Collision Damage = Ship's Scale + (zones moved ÷ 2)
    - Has Piercing quality (ignores resistance)
    - Has Devastating quality (can cause multiple breaches)
    - Ramming adds Intense quality (re-roll blanks - not applicable for flat damage)
    """
    import random

    data = request.json
    target_index = data.get("target_index", 0)
    attribute = data.get("attribute", 9)  # Character's Daring
    discipline = data.get("discipline", 3)  # Character's Conn
    difficulty = data.get("difficulty", 2)
    focus = data.get("focus", False)
    bonus_dice = data.get("bonus_dice", 0)
    character_id = data.get("character_id")  # Optional: override acting character for logging

    session = get_session()
    try:
        # Load encounter
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Check turn ownership
        if encounter.current_turn != "player":
            return jsonify({"error": "It's not the player's turn!"}), 403

        # Validate and deduct momentum for bonus dice (escalating: 1st=1, 2nd=2, 3rd=3)
        if bonus_dice > 0:
            bonus_dice = min(bonus_dice, 3)  # Cap at 3 per STA rules
            cost = get_bonus_dice_cost(bonus_dice)
            if cost > encounter.momentum:
                return jsonify({"error": f"Not enough Momentum! Need {cost} for {bonus_dice} dice, have {encounter.momentum}"}), 400
            encounter.momentum -= cost

        # Load player ship
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter.player_ship_id
        ).first()
        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404
        player_ship = player_ship_record.to_model()

        # Check if engines system is destroyed (breaches >= half Scale)
        available, reason = is_action_available("Ram", player_ship)
        if not available:
            return jsonify({"error": f"Cannot ram: {reason}"}), 400

        # Apply breach modifier to difficulty
        breach_modifier = get_breach_difficulty_modifier("Ram", player_ship)
        if breach_modifier > 0:
            difficulty = difficulty + breach_modifier

        # Load target ship
        enemy_ids = json.loads(encounter.enemy_ship_ids_json)
        if target_index >= len(enemy_ids):
            return jsonify({"error": "Invalid target"}), 400

        target_id = enemy_ids[target_index]
        target_record = session.query(StarshipRecord).filter_by(id=target_id).first()
        if not target_record:
            return jsonify({"error": "Target ship not found"}), 404
        target_ship = target_record.to_model()

        # TODO: Check range - Ram requires Close range (same zone or adjacent)
        # Zone tracking not fully implemented, so we allow Ram for now

        # Perform task roll: Daring + Conn, assisted by Engines + Conn
        result = assisted_task_roll(
            attribute=attribute,
            discipline=discipline,
            system=player_ship.systems.engines,
            department=player_ship.departments.conn,
            difficulty=difficulty,
            focus=focus,
            bonus_dice=bonus_dice
        )

        response = {
            "rolls": result.rolls,
            "target_number": result.target_number,
            "successes": result.successes,
            "complications": result.complications,
            "difficulty": difficulty,
            "succeeded": result.succeeded,
            "momentum_generated": result.momentum_generated,
            "ship_target_number": result.ship_target_number,
            "ship_roll": result.ship_roll,
            "ship_successes": result.ship_successes,
        }

        if result.succeeded:
            # Calculate collision damage for both ships
            # Collision Damage = Scale + (zones moved ÷ 2)
            # Since zone tracking isn't implemented, assume 1 zone moved (Close -> Contact)
            zones_moved = 1
            player_collision_damage = player_ship.scale + (zones_moved // 2)
            target_collision_damage = target_ship.scale  # Target doesn't move, so +0

            # Piercing quality: ignore resistance for both
            # Just apply raw damage

            # === Apply damage to TARGET ship (from player ramming) ===
            target_damage = player_collision_damage
            target_shield_damage = 0
            target_hull_damage = 0
            target_breaches_caused = 0
            target_systems_hit = []

            # Shields absorb first (if raised)
            if target_ship.shields_raised and target_ship.shields > 0:
                target_shield_damage = min(target_ship.shields, target_damage)
                target_ship.shields -= target_shield_damage
                target_hull_damage = target_damage - target_shield_damage
            else:
                target_hull_damage = target_damage

            # Hull damage causes breaches (1 per 5 damage, or 1 if any hull damage)
            if target_hull_damage > 0:
                if target_hull_damage >= 5:
                    target_breaches_caused = target_hull_damage // 5
                else:
                    target_breaches_caused = 1

                for _ in range(target_breaches_caused):
                    system_roll = random.randint(1, 20)
                    if system_roll == 1:
                        system_hit = "comms"
                    elif system_roll == 2:
                        system_hit = "computers"
                    elif system_roll <= 6:
                        system_hit = "engines"
                    elif system_roll <= 9:
                        system_hit = "sensors"
                    elif system_roll <= 17:
                        system_hit = "structure"
                    else:
                        system_hit = "weapons"
                    target_ship.add_breach(SystemType(system_hit))
                    target_systems_hit.append(system_hit)

            # Update target ship in database
            target_record.shields = target_ship.shields
            target_breaches_data = [
                {"system": b.system.value, "potency": b.potency}
                for b in target_ship.breaches
            ]
            target_record.breaches_json = json.dumps(target_breaches_data)

            # === Apply damage to PLAYER ship (from target's collision) ===
            player_damage = target_collision_damage
            player_shield_damage = 0
            player_hull_damage = 0
            player_breaches_caused = 0
            player_systems_hit = []

            if player_ship.shields_raised and player_ship.shields > 0:
                player_shield_damage = min(player_ship.shields, player_damage)
                player_ship.shields -= player_shield_damage
                player_hull_damage = player_damage - player_shield_damage
            else:
                player_hull_damage = player_damage

            if player_hull_damage > 0:
                if player_hull_damage >= 5:
                    player_breaches_caused = player_hull_damage // 5
                else:
                    player_breaches_caused = 1

                for _ in range(player_breaches_caused):
                    system_roll = random.randint(1, 20)
                    if system_roll == 1:
                        system_hit = "comms"
                    elif system_roll == 2:
                        system_hit = "computers"
                    elif system_roll <= 6:
                        system_hit = "engines"
                    elif system_roll <= 9:
                        system_hit = "sensors"
                    elif system_roll <= 17:
                        system_hit = "structure"
                    else:
                        system_hit = "weapons"
                    player_ship.add_breach(SystemType(system_hit))
                    player_systems_hit.append(system_hit)

            # Update player ship in database
            player_ship_record.shields = player_ship.shields
            player_breaches_data = [
                {"system": b.system.value, "potency": b.potency}
                for b in player_ship.breaches
            ]
            player_ship_record.breaches_json = json.dumps(player_breaches_data)

            # Update momentum
            if result.momentum_generated > 0:
                momentum_to_add = min(result.momentum_generated, 6 - encounter.momentum)
                encounter.momentum += momentum_to_add

            session.commit()

            response.update({
                # Damage dealt to target
                "target_collision_damage": player_collision_damage,
                "target_shield_damage": target_shield_damage,
                "target_hull_damage": target_hull_damage,
                "target_shields_remaining": target_ship.shields,
                "target_breaches_caused": target_breaches_caused,
                "target_systems_hit": target_systems_hit,
                "target_breaches": target_breaches_data,
                "target_status": target_ship.get_status(),
                # Damage received by player
                "player_collision_damage": target_collision_damage,
                "player_shield_damage": player_shield_damage,
                "player_hull_damage": player_hull_damage,
                "player_shields_remaining": player_ship.shields,
                "player_breaches_caused": player_breaches_caused,
                "player_systems_hit": player_systems_hit,
                "player_breaches": player_breaches_data,
                "player_status": player_ship.get_status(),
                # Momentum
                "new_momentum": encounter.momentum,
            })
        else:
            # Ram failed - no damage to either ship
            response.update({
                "target_collision_damage": 0,
                "player_collision_damage": 0,
                "new_momentum": encounter.momentum,  # Include even on miss (bonus dice may have been spent)
            })

        # Get player character for logging (use provided character_id or fall back to encounter default)
        char_id = character_id if character_id else encounter.player_character_id
        player_char = session.query(CharacterRecord).filter_by(id=char_id).first() if char_id else None
        actor_name = player_char.name if player_char else "Helm Officer"

        # Build description for log
        if result.succeeded:
            description = f"Rammed {target_ship.name}: {result.successes} successes vs difficulty {difficulty}. "
            description += f"Dealt {player_collision_damage} collision damage to {target_ship.name}. "
            description += f"Suffered {target_collision_damage} collision damage in return."
            if target_breaches_caused > 0:
                description += f" Target breaches: {', '.join(target_systems_hit)}."
            if player_breaches_caused > 0:
                description += f" Own breaches: {', '.join(player_systems_hit)}."
        else:
            description = f"Attempted to ram {target_ship.name}: {result.successes} successes vs difficulty {difficulty}. Failed to connect!"

        # Use ActionCompletionManager for consistent logging and turn handling
        manager = ActionCompletionManager(
            session, encounter,
            alternate_turn_after_action, log_combat_action
        )

        turn_state = manager.complete_player_major(
            actor_name=actor_name,
            ship_name=player_ship.name,
            action_name="Ram",
            description=description,
            task_result={
                "rolls": result.rolls,
                "target_number": result.target_number,
                "successes": result.successes,
                "complications": result.complications,
                "succeeded": result.succeeded,
            },
            damage_dealt=player_collision_damage if result.succeeded else 0,
        )
        response.update(turn_state)

        session.commit()

        return jsonify(response)
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/change-breach-system", methods=["POST"])
def change_breach_system(encounter_id: str):
    """
    Change which system a breach affects (Targeting Solution ability).

    This allows a player who used Targeting Solution to change
    the randomly-rolled system to one of their choice.
    """
    data = request.json
    target_index = data.get("target_index", 0)
    breach_index = data.get("breach_index", 0)
    new_system = data.get("new_system")

    if not new_system:
        return jsonify({"error": "new_system required"}), 400

    # Validate system name
    valid_systems = ["comms", "computers", "engines", "sensors", "structure", "weapons"]
    if new_system not in valid_systems:
        return jsonify({"error": f"Invalid system: {new_system}"}), 400

    session = get_session()
    try:
        # Load encounter
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Load target ship
        enemy_ids = json.loads(encounter.enemy_ship_ids_json)
        if target_index >= len(enemy_ids):
            return jsonify({"error": "Invalid target"}), 400

        target_id = enemy_ids[target_index]
        target_record = session.query(StarshipRecord).filter_by(id=target_id).first()
        if not target_record:
            return jsonify({"error": "Target ship not found"}), 404

        # Load breaches
        breaches_data = json.loads(target_record.breaches_json)
        if breach_index >= len(breaches_data):
            return jsonify({"error": "Invalid breach index"}), 400

        # Get the old system
        old_system = breaches_data[breach_index]["system"]

        # Change the system
        breaches_data[breach_index]["system"] = new_system

        # Save back to database
        target_record.breaches_json = json.dumps(breaches_data)

        # Clear the Targeting Solution effect (consumed)
        active_effects_data = json.loads(encounter.active_effects_json)
        # Remove attack effects with can_choose_system
        active_effects_data = [
            e for e in active_effects_data
            if not (e.get("applies_to") == "attack" and e.get("can_choose_system"))
        ]
        encounter.active_effects_json = json.dumps(active_effects_data)

        session.commit()

        return jsonify({
            "success": True,
            "old_system": old_system,
            "new_system": new_system,
            "message": f"Breach changed from {old_system.upper()} to {new_system.upper()}"
        })
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/execute-action", methods=["POST"])
def execute_action(encounter_id: str):
    """
    Generic action execution endpoint.

    Handles buff actions and task roll actions based on configuration.
    This replaces individual endpoints for each action.

    Request JSON:
        action_name: str - Name of the action to execute
        attribute: int - (For task rolls) Attribute value
        discipline: int - (For task rolls) Discipline value
        difficulty: int - (Optional) Override difficulty
        focus: bool - (Optional) Whether focus applies
        bonus_dice: int - (Optional) Number of bonus dice
        role: str - (Optional) Role making the request (player/gm)

    Returns:
        JSON with success, message, and action results
    """
    data = request.json
    action_name = data.get("action_name")
    role = data.get("role", "player")  # Default to player for backward compatibility
    character_id = data.get("character_id")  # Optional: override acting character for logging

    # Check turn ownership for player actions
    if role == "player":
        session = get_session()
        try:
            enc = session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()
            if enc and enc.current_turn != "player":
                return jsonify({"error": "It's not the player's turn!"}), 403
        finally:
            session.close()

    if not action_name:
        return jsonify({"error": "action_name required"}), 400

    config = get_action_config(action_name)
    if not config:
        return jsonify({"error": f"Unknown action: {action_name}"}), 400

    session = get_session()
    try:
        # Load encounter
        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Load player ship
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter_record.player_ship_id
        ).first()
        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404
        player_ship = player_ship_record.to_model()

        # Load player character (if needed for task rolls)
        character = None
        if encounter_record.player_character_id:
            char_record = session.query(CharacterRecord).filter_by(
                id=encounter_record.player_character_id
            ).first()
            if char_record:
                character = char_record.to_model()

        # Load active effects from database
        active_effects_data = json.loads(encounter_record.active_effects_json)
        active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]

        # Create encounter model (simplified - we don't need full encounter state)
        from sta.models.combat import Encounter
        encounter = Encounter(
            id=encounter_record.encounter_id,
            momentum=encounter_record.momentum,
            threat=encounter_record.threat,
            round=encounter_record.round,
            active_effects=active_effects,
        )

        # Check requirements
        can_execute, error_msg = check_action_requirements(action_name, encounter, player_ship, config)
        if not can_execute:
            return jsonify({"error": error_msg}), 400

        # Check range requirements for actions that target enemies
        target_index = data.get("target_index", 0)  # Default to first enemy
        hex_distance = 0
        if config.get("max_range") is not None or config.get("difficulty_per_range"):
            # This action has range requirements - calculate distance to target
            ship_positions = get_ship_positions_from_encounter(encounter_record)
            player_pos = ship_positions.get("player", {"q": 0, "r": 0})
            target_pos = ship_positions.get(f"enemy_{target_index}", {"q": 0, "r": 0})
            player_coord = HexCoord(q=player_pos.get("q", 0), r=player_pos.get("r", 0))
            target_coord = HexCoord(q=target_pos.get("q", 0), r=target_pos.get("r", 0))
            hex_distance = player_coord.distance_to(target_coord)

            # Check max range
            range_valid, range_error = check_action_range(action_name, hex_distance)
            if not range_valid:
                return jsonify({"error": range_error}), 400

        # Execute action based on type
        if is_buff_action(action_name):
            result = execute_buff_action(action_name, encounter, player_ship, config)

        elif is_task_roll_action(action_name):
            # Validate and deduct momentum for bonus dice (escalating: 1st=1, 2nd=2, 3rd=3)
            # This applies whether roll was done frontend-side or will be done now
            bonus_dice = data.get("bonus_dice", 0)
            if role == "player" and bonus_dice > 0:
                bonus_dice = min(bonus_dice, 3)  # Cap at 3 per STA rules
                cost = get_bonus_dice_cost(bonus_dice)
                if cost > encounter_record.momentum:
                    return jsonify({"error": f"Not enough Momentum! Need {cost} for {bonus_dice} dice, have {encounter_record.momentum}"}), 400
                encounter_record.momentum -= cost
                encounter.momentum = encounter_record.momentum

            # Check if roll was already done by the frontend
            if "roll_succeeded" in data:
                # Frontend already did the roll - handle success or failure
                if data.get("roll_succeeded"):
                    # Apply success effects without re-rolling
                    momentum_generated = data.get("roll_momentum", 0)
                    result = apply_task_roll_success(
                        action_name,
                        encounter,
                        player_ship,
                        momentum_generated,
                        config
                    )

                    # Special handling for Damage Control - actually patch the breach
                    if action_name == "Damage Control":
                        target_system = data.get("target_system")
                        if not target_system:
                            return jsonify({"error": "target_system required for Damage Control"}), 400

                        try:
                            system_type = SystemType(target_system.lower())
                        except ValueError:
                            return jsonify({"error": f"Invalid system: {target_system}"}), 400

                        # Check if there's actually a breach on this system
                        breach_potency = player_ship.get_breach_potency(system_type)
                        if breach_potency == 0:
                            result.message += f" But {target_system} has no breach to repair!"
                        else:
                            # Patch the breach (reduces potency by 1)
                            patched = player_ship.patch_breach(system_type, 1)
                            result.message = f"Damage Control succeeded! Patched {target_system.upper()} breach."
                            result.data["system_patched"] = target_system
                            result.data["breach_patched"] = patched
                            result.data["remaining_breach_potency"] = player_ship.get_breach_potency(system_type)

                            # Save updated breaches to database
                            player_ship_record.breaches_json = json.dumps([
                                {"system": b.system.value, "potency": b.potency}
                                for b in player_ship.breaches
                            ])

                    # Special handling for Sensor Sweep - create detection effect if target is in fog
                    if action_name == "Sensor Sweep":
                        # Get the target position from the data
                        target_idx = data.get("target_index", 0)
                        ship_positions = get_ship_positions_from_encounter(encounter_record)
                        target_pos = ship_positions.get(f"enemy_{target_idx}", {"q": 0, "r": 0})

                        # Get tactical map and check if target is in visibility-blocked terrain
                        tactical_map = json.loads(encounter_record.tactical_map_json or "{}")
                        target_terrain = get_terrain_at_position(tactical_map, target_pos.get("q", 0), target_pos.get("r", 0))

                        if target_terrain in VISIBILITY_BLOCKING_TERRAIN:
                            # Create a detection effect for this position
                            detection_effect = ActiveEffect(
                                source_action="Sensor Sweep Detection",
                                applies_to="sensor",
                                duration="end_of_round",
                                detected_position={"q": target_pos.get("q", 0), "r": target_pos.get("r", 0)}
                            )
                            encounter.add_effect(detection_effect)
                            result.message += f" Detected ship at ({target_pos.get('q', 0)}, {target_pos.get('r', 0)}) through {target_terrain.replace('_', ' ')}!"
                            result.data["detected_position"] = detection_effect.detected_position
                else:
                    # Roll failed - create a failure result (no effects applied)
                    from sta.mechanics.action_handlers import ActionExecutionResult
                    roll_successes = data.get("roll_successes", 0)
                    roll_complications = data.get("roll_complications", 0)
                    result = ActionExecutionResult(
                        False,
                        f"{action_name} failed! ({roll_successes} successes)"
                    )
                    if roll_complications > 0:
                        result.message += f" {roll_complications} complication(s)!"

                    # Store roll info for logging
                    result.roll_result = {
                        "rolls": data.get("roll_dice", []),
                        "target_number": data.get("roll_target", 0),
                        "successes": roll_successes,
                        "complications": roll_complications,
                        "succeeded": False,
                    }

            else:
                # No roll info provided - do the full roll on backend
                if not character:
                    return jsonify({"error": "Character required for task roll"}), 400

                attribute_value = data.get("attribute", 9)
                discipline_value = data.get("discipline", 2)
                focus = data.get("focus", False)

                result = execute_task_roll_action(
                    action_name,
                    encounter,
                    character,
                    player_ship,
                    attribute_value,
                    discipline_value,
                    focus,
                    bonus_dice,
                    config
                )

                # Special handling for Damage Control - actually patch the breach
                if action_name == "Damage Control" and result.success:
                    target_system = data.get("target_system")
                    if not target_system:
                        return jsonify({"error": "target_system required for Damage Control"}), 400

                    try:
                        system_type = SystemType(target_system.lower())
                    except ValueError:
                        return jsonify({"error": f"Invalid system: {target_system}"}), 400

                    # Check if there's actually a breach on this system
                    breach_potency = player_ship.get_breach_potency(system_type)
                    if breach_potency == 0:
                        result.message += f" But {target_system} has no breach to repair!"
                    else:
                        # Patch the breach (reduces potency by 1)
                        patched = player_ship.patch_breach(system_type, 1)
                        result.message = f"Damage Control succeeded! Patched {target_system.upper()} breach."
                        result.data["system_patched"] = target_system
                        result.data["breach_patched"] = patched
                        result.data["remaining_breach_potency"] = player_ship.get_breach_potency(system_type)

                        # Save updated breaches to database
                        player_ship_record.breaches_json = json.dumps([
                            {"system": b.system.value, "potency": b.potency}
                            for b in player_ship.breaches
                        ])

                # Special handling for Sensor Sweep - create detection effect if target is in fog
                if action_name == "Sensor Sweep" and result.success:
                    # Get the target position from the data
                    target_idx = data.get("target_index", 0)
                    ship_positions = get_ship_positions_from_encounter(encounter_record)
                    target_pos = ship_positions.get(f"enemy_{target_idx}", {"q": 0, "r": 0})

                    # Get tactical map and check if target is in visibility-blocked terrain
                    tactical_map = json.loads(encounter_record.tactical_map_json or "{}")
                    target_terrain = get_terrain_at_position(tactical_map, target_pos.get("q", 0), target_pos.get("r", 0))

                    if target_terrain in VISIBILITY_BLOCKING_TERRAIN:
                        # Create a detection effect for this position
                        detection_effect = ActiveEffect(
                            source_action="Sensor Sweep Detection",
                            applies_to="sensor",
                            duration="end_of_round",
                            detected_position={"q": target_pos.get("q", 0), "r": target_pos.get("r", 0)}
                        )
                        encounter.add_effect(detection_effect)
                        result.message += f" Detected ship at ({target_pos.get('q', 0)}, {target_pos.get('r', 0)}) through {target_terrain.replace('_', ' ')}!"
                        result.data["detected_position"] = detection_effect.detected_position

        elif is_toggle_action(action_name):
            # Toggle action - update ship state
            toggle_property = config.get("toggles")
            from sta.mechanics.action_handlers import ActionExecutionResult

            if toggle_property == "shields_raised":
                # Toggle shields
                new_state = not player_ship.shields_raised
                player_ship_record.shields_raised = new_state

                # If raising shields, set to max; if lowering, set to 0
                if new_state:
                    player_ship_record.shields = player_ship_record.shields_max
                else:
                    player_ship_record.shields = 0

                result = ActionExecutionResult(
                    True,
                    f"Shields {'raised' if new_state else 'lowered'}!"
                )
                result.data["shields_raised"] = new_state
                result.data["shields"] = player_ship_record.shields
                result.data["shields_max"] = player_ship_record.shields_max

            elif toggle_property == "weapons_armed":
                # Toggle weapons
                new_state = not player_ship.weapons_armed
                player_ship_record.weapons_armed = new_state

                result = ActionExecutionResult(
                    True,
                    f"Weapons {'armed' if new_state else 'disarmed'}!"
                )
                result.data["weapons_armed"] = new_state

            else:
                return jsonify({"error": f"Unknown toggle property: {toggle_property}"}), 400

        elif config.get("type") == "special":
            # Special actions need custom handling
            from sta.mechanics.action_handlers import ActionExecutionResult

            if action_name == "Defensive Fire":
                weapon_index = data.get("weapon_index")
                if weapon_index is None:
                    return jsonify({"error": "weapon_index required for Defensive Fire"}), 400

                result = execute_defensive_fire(encounter, player_ship, weapon_index)

            elif action_name == "Reroute Power":
                target_system = data.get("target_system")
                if target_system is None:
                    return jsonify({"error": "target_system required for Reroute Power"}), 400

                result = execute_reroute_power(encounter, player_ship, target_system)

                # Update ship's reserve power status in database
                if result.success:
                    player_ship_record.has_reserve_power = player_ship.has_reserve_power

            else:
                return jsonify({"error": f"Special action not implemented: {action_name}"}), 400

        else:
            return jsonify({"error": f"Action type not implemented: {config.get('type')}"}), 400

        # Save updated state
        encounter_record.momentum = encounter.momentum
        encounter_record.active_effects_json = json.dumps([e.to_dict() for e in encounter.active_effects])

        # Save ship's reserve power status if it changed
        if result.data.get("reserve_power_consumed") or result.data.get("reserve_power_restored"):
            player_ship_record.has_reserve_power = player_ship.has_reserve_power

        # Determine if this is a major action (uses a turn)
        # buff and toggle actions are minor; task_roll and special are major
        action_type = config.get("type")
        is_major_action = action_type in ("task_roll", "special")

        response = result.to_dict()

        # Get player character for logging (use provided character_id or fall back to encounter default)
        char_id = character_id if character_id else encounter_record.player_character_id
        player_char = session.query(CharacterRecord).filter_by(id=char_id).first() if char_id else None
        actor_name = player_char.name if player_char else "Bridge Officer"

        # Build task result data for logging
        task_result_data = None
        if hasattr(result, 'roll_result') and result.roll_result:
            rr = result.roll_result
            task_result_data = {
                "rolls": rr.get("rolls", []),
                "target_number": rr.get("target_number", 0),
                "successes": rr.get("successes", 0),
                "complications": rr.get("complications", 0),
                "succeeded": rr.get("succeeded", True),
            }

        # Use ActionCompletionManager for consistent logging and turn handling
        manager = ActionCompletionManager(
            session, encounter_record,
            alternate_turn_after_action, log_combat_action
        )

        if is_major_action:
            turn_state = manager.complete_player_major(
                actor_name=actor_name,
                ship_name=player_ship.name,
                action_name=action_name,
                description=result.message,
                task_result=task_result_data,
            )
            response.update(turn_state)
        else:
            manager.complete_player_minor(
                actor_name=actor_name,
                ship_name=player_ship.name,
                action_name=action_name,
                description=result.message,
                task_result=task_result_data,
            )

        # Always include current momentum (may have been spent on bonus dice)
        response["momentum"] = encounter_record.momentum
        response["new_momentum"] = encounter_record.momentum

        session.commit()

        return jsonify(response)

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/npc-action", methods=["POST"])
def npc_action(encounter_id: str):
    """
    Execute an action for an NPC ship.

    NPC ships use their Crew Quality for rolls (attribute + department),
    and always have Focus (crits on 1s AND 2s).

    Request JSON:
        ship_index: int - Index of the enemy ship in the encounter
        ship_id: int - Database ID of the enemy ship
        action_name: str - Name of the action to execute
        action_type: str - Type of action (buff, task_roll, toggle, special)
        bonus_dice: int - (Optional) Number of bonus dice from Threat
        difficulty: int - (Optional) Override difficulty for task rolls
        attribute: int - NPC crew attribute value
        department: int - NPC crew department value
        focus: bool - Whether focus applies (always True for NPCs)

    Returns:
        JSON with success, message, roll_results (if task roll), and action effects
    """
    import random

    data = request.json
    ship_index = data.get("ship_index", 0)
    ship_id = data.get("ship_id")
    action_name = data.get("action_name")
    action_type = data.get("action_type")
    action_category = data.get("action_category", "")  # e.g., "tactical_major"
    bonus_dice = data.get("bonus_dice", 0)
    difficulty = data.get("difficulty", 2)
    attribute = data.get("attribute", 10)  # Crew quality attribute
    department = data.get("department", 3)  # Crew quality department
    focus = data.get("focus", True)  # NPCs always have focus

    # Determine if this is a major action (ends turn)
    is_major_action = action_category.endswith("_major")

    if not action_name:
        return jsonify({"error": "action_name required"}), 400

    # Validate this is an NPC-allowed action
    if not is_npc_action(action_name):
        return jsonify({"error": f"Action '{action_name}' is not available for NPC ships"}), 400

    session = get_session()
    try:
        # Load encounter
        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Check it's the enemy turn
        if encounter_record.current_turn != "enemy":
            return jsonify({"error": "It's not the enemy's turn!"}), 403

        # Check if this ship can still act (has turns remaining)
        ships_turns_used = json.loads(encounter_record.ships_turns_used_json)
        ship_turns_used = ships_turns_used.get(str(ship_id), 0)

        # Load NPC ship
        npc_ship_record = session.query(StarshipRecord).filter_by(id=ship_id).first()
        if not npc_ship_record:
            return jsonify({"error": "NPC ship not found"}), 404
        npc_ship = npc_ship_record.to_model()

        # Check if ship can act (for major actions, must have turns remaining)
        if is_major_action and ship_turns_used >= npc_ship_record.scale:
            return jsonify({
                "error": f"{npc_ship.name} has used all {npc_ship_record.scale} turns this round!"
            }), 400

        # Load active effects
        active_effects_data = json.loads(encounter_record.active_effects_json)
        active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]

        config = get_action_config(action_name)

        result = {
            "success": True,
            "message": "",
            "action_name": action_name,
            "ship_name": npc_ship.name,
        }

        # Handle different action types
        if action_type == "buff":
            # Create effect for the NPC ship
            if config and config.get("effect"):
                effect_config = config["effect"]
                new_effect = ActiveEffect(
                    source_action=action_name,
                    source_ship=npc_ship.name,
                    applies_to=effect_config.get("applies_to", "all"),
                    duration=effect_config.get("duration", "next_action"),
                    damage_bonus=effect_config.get("damage_bonus", 0),
                    resistance_bonus=effect_config.get("resistance_bonus", 0),
                    difficulty_modifier=effect_config.get("difficulty_modifier", 0),
                    can_reroll=effect_config.get("can_reroll", False),
                    can_choose_system=effect_config.get("can_choose_system", False),
                    piercing=effect_config.get("piercing", False),
                )
                active_effects.append(new_effect)
                result["message"] = f"{npc_ship.name}: {action_name} activated!"
            else:
                result["message"] = f"{npc_ship.name}: {action_name} (effect applied)"

        elif action_type == "toggle":
            # Handle toggle actions for NPC ships
            toggle_property = config.get("toggles") if config else None

            if toggle_property == "shields_raised":
                new_state = action_name == "Raise Shields"
                npc_ship_record.shields_raised = new_state
                if new_state:
                    npc_ship_record.shields = npc_ship_record.shields_max
                else:
                    npc_ship_record.shields = 0
                result["message"] = f"{npc_ship.name}: Shields {'raised' if new_state else 'lowered'}!"
                result["shields_raised"] = new_state
                result["shields"] = npc_ship_record.shields

            elif toggle_property == "weapons_armed":
                new_state = action_name == "Arm Weapons"
                npc_ship_record.weapons_armed = new_state
                result["message"] = f"{npc_ship.name}: Weapons {'armed' if new_state else 'disarmed'}!"
                result["weapons_armed"] = new_state

        elif action_type == "task_roll":
            # Perform the roll using NPC crew quality
            target_number = attribute + department
            num_dice = 2 + bonus_dice

            rolls = [random.randint(1, 20) for _ in range(num_dice)]
            successes = 0
            complications = 0

            for roll in rolls:
                if roll == 1:
                    successes += 2  # Critical success
                elif roll <= 2 and focus:
                    successes += 2  # Focus makes 2 also a crit
                elif roll <= target_number:
                    successes += 1
                if roll == 20:
                    complications += 1

            succeeded = successes >= difficulty
            momentum_generated = max(0, successes - difficulty) if succeeded else 0

            result["roll_results"] = {
                "rolls": rolls,
                "target": target_number,
                "successes": successes,
                "complications": complications,
                "difficulty": difficulty,
                "succeeded": succeeded,
                "momentum_generated": momentum_generated,
                "has_focus": focus,
            }

            if succeeded:
                result["message"] = f"{npc_ship.name}: {action_name} succeeded!"

                # Apply success effects
                if config and config.get("on_success"):
                    success_config = config["on_success"]

                    # Create effect if specified
                    if success_config.get("create_effect"):
                        effect_config = success_config["create_effect"]
                        new_effect = ActiveEffect(
                            source_action=action_name,
                            source_ship=npc_ship.name,
                            applies_to=effect_config.get("applies_to", "all"),
                            duration=effect_config.get("duration", "next_action"),
                            damage_bonus=effect_config.get("damage_bonus", 0),
                            resistance_bonus=effect_config.get("resistance_bonus", 0),
                            difficulty_modifier=effect_config.get("difficulty_modifier", 0),
                            can_reroll=effect_config.get("can_reroll", False),
                            can_choose_system=effect_config.get("can_choose_system", False),
                            piercing=effect_config.get("piercing", False),
                        )
                        active_effects.append(new_effect)

                    # Generate momentum (adds to threat pool for NPCs)
                    if success_config.get("generate_momentum") and momentum_generated > 0:
                        encounter_record.threat += momentum_generated
                        result["threat_generated"] = momentum_generated
                        result["message"] += f" (+{momentum_generated} Threat)"

            else:
                result["message"] = f"{npc_ship.name}: {action_name} failed."

        elif action_type == "special":
            # Handle special actions
            if action_name == "Ram":
                # NPC Ram action - rams the player ship
                player_ship_record = session.query(StarshipRecord).filter_by(
                    id=encounter_record.player_ship_id
                ).first()
                if not player_ship_record:
                    return jsonify({"error": "Player ship not found"}), 404
                player_ship = player_ship_record.to_model()

                # Perform task roll using NPC crew quality
                target_number = attribute + department
                num_dice = 2 + bonus_dice
                rolls = [random.randint(1, 20) for _ in range(num_dice)]
                successes = 0
                complications = 0

                for roll in rolls:
                    if roll == 1:
                        successes += 2
                    elif roll <= 2 and focus:
                        successes += 2
                    elif roll <= target_number:
                        successes += 1
                    if roll == 20:
                        complications += 1

                succeeded = successes >= difficulty
                momentum_generated = max(0, successes - difficulty) if succeeded else 0

                result["roll_results"] = {
                    "rolls": rolls,
                    "target": target_number,
                    "successes": successes,
                    "complications": complications,
                    "difficulty": difficulty,
                    "succeeded": succeeded,
                    "momentum_generated": momentum_generated,
                    "has_focus": focus,
                }

                if succeeded:
                    # Calculate collision damage (Piercing - ignores resistance)
                    zones_moved = 1
                    npc_collision_damage = npc_ship.scale + (zones_moved // 2)
                    player_collision_damage = player_ship.scale

                    # Apply damage to PLAYER ship
                    player_damage = npc_collision_damage
                    player_shield_damage = 0
                    player_hull_damage = 0
                    player_breaches_caused = 0
                    player_systems_hit = []

                    if player_ship.shields_raised and player_ship.shields > 0:
                        player_shield_damage = min(player_ship.shields, player_damage)
                        player_ship.shields -= player_shield_damage
                        player_hull_damage = player_damage - player_shield_damage
                    else:
                        player_hull_damage = player_damage

                    if player_hull_damage > 0:
                        player_breaches_caused = max(1, player_hull_damage // 5)
                        for _ in range(player_breaches_caused):
                            system_roll = random.randint(1, 20)
                            if system_roll == 1:
                                system_hit = "comms"
                            elif system_roll == 2:
                                system_hit = "computers"
                            elif system_roll <= 6:
                                system_hit = "engines"
                            elif system_roll <= 9:
                                system_hit = "sensors"
                            elif system_roll <= 17:
                                system_hit = "structure"
                            else:
                                system_hit = "weapons"
                            player_ship.add_breach(SystemType(system_hit))
                            player_systems_hit.append(system_hit)

                    player_ship_record.shields = player_ship.shields
                    player_ship_record.breaches_json = json.dumps([
                        {"system": b.system.value, "potency": b.potency}
                        for b in player_ship.breaches
                    ])

                    # Apply damage to NPC ship
                    npc_damage = player_collision_damage
                    npc_shield_damage = 0
                    npc_hull_damage = 0
                    npc_breaches_caused = 0
                    npc_systems_hit = []

                    if npc_ship.shields_raised and npc_ship.shields > 0:
                        npc_shield_damage = min(npc_ship.shields, npc_damage)
                        npc_ship.shields -= npc_shield_damage
                        npc_hull_damage = npc_damage - npc_shield_damage
                    else:
                        npc_hull_damage = npc_damage

                    if npc_hull_damage > 0:
                        npc_breaches_caused = max(1, npc_hull_damage // 5)
                        for _ in range(npc_breaches_caused):
                            system_roll = random.randint(1, 20)
                            if system_roll == 1:
                                system_hit = "comms"
                            elif system_roll == 2:
                                system_hit = "computers"
                            elif system_roll <= 6:
                                system_hit = "engines"
                            elif system_roll <= 9:
                                system_hit = "sensors"
                            elif system_roll <= 17:
                                system_hit = "structure"
                            else:
                                system_hit = "weapons"
                            npc_ship.add_breach(SystemType(system_hit))
                            npc_systems_hit.append(system_hit)

                    npc_ship_record.shields = npc_ship.shields
                    npc_ship_record.breaches_json = json.dumps([
                        {"system": b.system.value, "potency": b.potency}
                        for b in npc_ship.breaches
                    ])

                    if momentum_generated > 0:
                        encounter_record.threat += momentum_generated
                        result["threat_generated"] = momentum_generated

                    result["message"] = f"{npc_ship.name} rammed {player_ship.name}!"
                    result["ram_results"] = {
                        "player_collision_damage": npc_collision_damage,
                        "player_shield_damage": player_shield_damage,
                        "player_hull_damage": player_hull_damage,
                        "player_shields_remaining": player_ship.shields,
                        "player_breaches_caused": player_breaches_caused,
                        "player_systems_hit": player_systems_hit,
                        "npc_collision_damage": player_collision_damage,
                        "npc_shield_damage": npc_shield_damage,
                        "npc_hull_damage": npc_hull_damage,
                        "npc_shields_remaining": npc_ship.shields,
                        "npc_breaches_caused": npc_breaches_caused,
                        "npc_systems_hit": npc_systems_hit,
                    }
                else:
                    result["message"] = f"{npc_ship.name} failed to ram!"
            else:
                result["message"] = f"{npc_ship.name}: {action_name} - special action (not implemented)"

        # Save updated effects
        encounter_record.active_effects_json = json.dumps([e.to_dict() for e in active_effects])

        # Build task result data for logging
        crew_quality = npc_ship.crew_quality.value if npc_ship.crew_quality else "Talented"
        actor_name = f"{npc_ship.name} Crew ({crew_quality})"

        task_result_data = None
        if "roll_results" in result:
            rr = result["roll_results"]
            task_result_data = {
                "rolls": rr.get("rolls", []),
                "target_number": rr.get("target", 0),
                "successes": rr.get("successes", 0),
                "complications": rr.get("complications", 0),
                "succeeded": rr.get("succeeded", True),
            }

        # Use ActionCompletionManager for consistent logging and turn handling
        manager = ActionCompletionManager(
            session, encounter_record,
            alternate_turn_after_action, log_combat_action
        )

        if is_major_action:
            turn_state = manager.complete_enemy_major(
                enemy_id=ship_id,
                enemy_scale=npc_ship_record.scale,
                actor_name=actor_name,
                ship_name=npc_ship.name,
                action_name=action_name,
                description=result.get("message", f"{npc_ship.name} performed {action_name}"),
                task_result=task_result_data,
            )
            result.update(turn_state)
        else:
            manager.complete_enemy_minor(
                actor_name=actor_name,
                ship_name=npc_ship.name,
                action_name=action_name,
                description=result.get("message", f"{npc_ship.name} performed {action_name}"),
                task_result=task_result_data,
            )

        session.commit()

        return jsonify(result)

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/gm-attack", methods=["POST"])
def gm_attack(encounter_id: str):
    """Execute an enemy attack against the player ship.

    Checks for Defensive Fire / Evasive Action effects and handles opposed rolls.
    """
    import random

    data = request.json
    enemy_index = data.get("enemy_index", 0)
    weapon_index = data.get("weapon_index", 0)

    session = get_session()
    try:
        # Load encounter
        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Check it's the enemy turn
        if encounter_record.current_turn != "enemy":
            return jsonify({"error": "It's not the enemy's turn!"}), 403

        # Load player ship (target)
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter_record.player_ship_id
        ).first()
        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404
        player_ship = player_ship_record.to_model()

        # Load player character for opposed roll stats
        player_char_record = session.query(CharacterRecord).filter_by(
            id=encounter_record.player_character_id
        ).first()
        player_char = player_char_record.to_model() if player_char_record else None

        # Load attacking enemy ship
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json)
        if enemy_index >= len(enemy_ids):
            return jsonify({"error": "Invalid enemy ship"}), 400

        enemy_id = enemy_ids[enemy_index]
        enemy_record = session.query(StarshipRecord).filter_by(id=enemy_id).first()
        if not enemy_record:
            return jsonify({"error": "Enemy ship not found"}), 404
        enemy_ship = enemy_record.to_model()

        # Check if this ship can still act (has turns remaining)
        ships_turns_used = json.loads(encounter_record.ships_turns_used_json)
        ship_turns_used = ships_turns_used.get(str(enemy_id), 0)
        if ship_turns_used >= enemy_record.scale:
            return jsonify({
                "error": f"{enemy_ship.name} has used all {enemy_record.scale} turns this round!"
            }), 400

        # Get enemy weapon
        if weapon_index >= len(enemy_ship.weapons):
            return jsonify({"error": "Invalid weapon"}), 400
        weapon = enemy_ship.weapons[weapon_index]

        # Check weapon range vs target distance
        ship_positions = get_ship_positions_from_encounter(encounter_record)
        player_pos = ship_positions.get("player", {"q": 0, "r": 0})
        enemy_pos = ship_positions.get(f"enemy_{enemy_index}", {"q": 0, "r": 0})
        player_coord = HexCoord(q=player_pos.get("q", 0), r=player_pos.get("r", 0))
        enemy_coord = HexCoord(q=enemy_pos.get("q", 0), r=enemy_pos.get("r", 0))
        hex_distance = enemy_coord.distance_to(player_coord)
        max_weapon_range = get_max_range_distance(weapon.range)

        if hex_distance > max_weapon_range:
            current_range = get_range_name_for_distance(hex_distance)
            weapon_range_name = weapon.range.value.title()
            return jsonify({
                "error": f"Target is out of range! {weapon.name} has {weapon_range_name} range ({max_weapon_range} hex{'es' if max_weapon_range != 1 else ''}), but target is at {current_range} range ({hex_distance} hex{'es' if hex_distance != 1 else ''})."
            }), 400

        # Load active effects
        active_effects_data = json.loads(encounter_record.active_effects_json)
        active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]
        from sta.models.combat import Encounter as EncounterModel
        encounter_model = EncounterModel(
            id=encounter_record.encounter_id,
            momentum=encounter_record.momentum,
            active_effects=active_effects,
        )

        # Check for defensive effects (Defensive Fire or Evasive Action)
        defense_effects = encounter_model.get_effects("defense")
        defensive_fire_effect = None
        evasive_action_effect = None

        for effect in defense_effects:
            if effect.source_action == "Defensive Fire" and effect.is_opposed:
                defensive_fire_effect = effect
            elif effect.source_action == "Evasive Action":
                evasive_action_effect = effect

        has_defensive_effect = defensive_fire_effect or evasive_action_effect
        defense_effect_name = defensive_fire_effect.source_action if defensive_fire_effect else (
            evasive_action_effect.source_action if evasive_action_effect else None
        )

        response = {
            "attacker": enemy_ship.name,
            "attacker_weapon": weapon.name,
            "defender": player_ship.name,
            "has_defensive_effect": has_defensive_effect,
            "defense_effect_name": defense_effect_name,
        }

        # If Defensive Fire is active, create a pending attack for the player to roll
        if defensive_fire_effect:
            # Store the pending attack - player needs to make their defensive roll
            pending_attack = {
                "attacker_index": enemy_index,
                "attacker_name": enemy_ship.name,
                "weapon_index": weapon_index,
                "weapon_name": weapon.name,
                "bonus_dice": data.get("bonus_dice", 0),
                "timestamp": datetime.now().isoformat(),
                "defensive_fire_weapon_index": defensive_fire_effect.weapon_index,
            }
            encounter_record.pending_attack_json = json.dumps(pending_attack)
            session.commit()

            return jsonify({
                "status": "pending_defensive_roll",
                "message": f"{enemy_ship.name} is attacking with {weapon.name}! Waiting for defensive roll...",
                "attacker": enemy_ship.name,
                "attacker_weapon": weapon.name,
                "defender": player_ship.name,
                "pending_attack": pending_attack,
            })

        if has_defensive_effect:
            # OPPOSED ROLL
            # Defender rolls: Daring + Security, assisted by Weapons + Security
            # For simplicity, attacker's "roll" is simulated as their attack difficulty + random factor

            # Defender stats
            if player_char:
                defender_attr = player_char.attributes.daring
                defender_disc = player_char.disciplines.security
            else:
                defender_attr = 9
                defender_disc = 3

            defender_target = defender_attr + defender_disc
            ship_target = player_ship.systems.weapons + player_ship.departments.security

            # Defender rolls 2d20 + ship assist
            defender_rolls = [random.randint(1, 20), random.randint(1, 20)]
            ship_assist_roll = random.randint(1, 20)

            # Calculate defender successes
            defender_successes = 0
            defender_complications = 0

            for roll in defender_rolls:
                if roll == 1:
                    defender_successes += 2  # Critical
                elif roll <= defender_target:
                    defender_successes += 1
                if roll == 20:
                    defender_complications += 1

            # Ship assist
            if ship_assist_roll == 1:
                defender_successes += 2
            elif ship_assist_roll <= ship_target:
                defender_successes += 1
            if ship_assist_roll == 20:
                defender_complications += 1

            # Attacker "rolls" - enemy uses Control + Security, assisted by Weapons + Security
            attacker_attr = 9  # Default enemy Control
            attacker_disc = 3  # Default enemy Security
            attacker_target = attacker_attr + attacker_disc
            enemy_ship_target = enemy_ship.systems.weapons + enemy_ship.departments.security

            attacker_rolls = [random.randint(1, 20), random.randint(1, 20)]
            enemy_assist_roll = random.randint(1, 20)

            attacker_successes = 0
            attacker_complications = 0

            for roll in attacker_rolls:
                if roll == 1:
                    attacker_successes += 2
                elif roll <= attacker_target:
                    attacker_successes += 1
                if roll == 20:
                    attacker_complications += 1

            if enemy_assist_roll == 1:
                attacker_successes += 2
            elif enemy_assist_roll <= enemy_ship_target:
                attacker_successes += 1
            if enemy_assist_roll == 20:
                attacker_complications += 1

            # Check for Attack Pattern effect - gives enemies easier attacks (-1 Difficulty = +1 success in opposed roll)
            attack_pattern_active = False
            for effect in encounter_model.get_effects("all"):
                if effect.source_action == "Attack Pattern":
                    attack_pattern_active = True
                    attacker_successes += 1  # Simulates -1 Difficulty advantage
                    break

            # Opposed roll: defender wins if they have equal or more successes
            defender_wins = defender_successes >= attacker_successes

            response.update({
                "opposed_roll": True,
                "defender_rolls": defender_rolls,
                "defender_target": defender_target,
                "defender_ship_roll": ship_assist_roll,
                "defender_ship_target": ship_target,
                "defender_successes": defender_successes,
                "defender_complications": defender_complications,
                "attacker_rolls": attacker_rolls,
                "attacker_target": attacker_target,
                "attacker_ship_roll": enemy_assist_roll,
                "attacker_ship_target": enemy_ship_target,
                "attacker_successes": attacker_successes,
                "attacker_complications": attacker_complications,
                "defender_wins": defender_wins,
                "attack_pattern_active": attack_pattern_active,
            })

            if defender_wins:
                # Attack misses!
                response["attack_result"] = "missed"
                response["message"] = f"{player_ship.name} successfully defended! Attack misses."

                # Generate momentum from excess successes (defender's successes beyond attacker's)
                momentum_generated = max(0, defender_successes - attacker_successes)
                if momentum_generated > 0:
                    old_momentum = encounter_record.momentum
                    encounter_record.momentum = min(6, encounter_record.momentum + momentum_generated)
                    actual_momentum_added = encounter_record.momentum - old_momentum
                    if actual_momentum_added > 0:
                        response["momentum_generated"] = actual_momentum_added
                        response["new_momentum"] = encounter_record.momentum
                        response["message"] += f" +{actual_momentum_added} Momentum!"

                # Check for counterattack option (Defensive Fire only)
                can_counterattack = False
                if defensive_fire_effect and defensive_fire_effect.weapon_index is not None:
                    counterattack_weapon_index = defensive_fire_effect.weapon_index
                    if counterattack_weapon_index < len(player_ship.weapons):
                        counterattack_weapon = player_ship.weapons[counterattack_weapon_index]
                        can_counterattack = True
                        response["can_counterattack"] = True
                        response["counterattack_cost"] = 2  # 2 Momentum
                        response["counterattack_weapon"] = counterattack_weapon.name
                        response["counterattack_weapon_index"] = counterattack_weapon_index
                        response["current_momentum"] = encounter_record.momentum
                        response["message"] += f" May spend 2 Momentum to counterattack with {counterattack_weapon.name}."

                # Save state (no damage applied)
                encounter_record.active_effects_json = json.dumps([e.to_dict() for e in encounter_model.active_effects])

                # Use ActionCompletionManager for consistent logging and turn handling
                crew_quality = enemy_ship.crew_quality.value if enemy_ship.crew_quality else "Talented"
                manager = ActionCompletionManager(
                    session, encounter_record,
                    alternate_turn_after_action, log_combat_action
                )

                # Log the missed attack, skip turn advance if counterattack is available
                turn_state = manager.complete_enemy_major(
                    enemy_id=enemy_id,
                    enemy_scale=enemy_record.scale,
                    actor_name=f"{enemy_ship.name} Crew ({crew_quality})",
                    ship_name=enemy_ship.name,
                    action_name=f"Fire {weapon.name}",
                    description=f"Fired {weapon.name} at {player_ship.name}: Attack defended! ({attacker_successes} vs {defender_successes} successes)",
                    task_result={
                        "attacker_rolls": attacker_rolls,
                        "attacker_successes": attacker_successes,
                        "defender_rolls": defender_rolls,
                        "defender_successes": defender_successes,
                        "defender_wins": True,
                    },
                    damage_dealt=0,
                    skip_turn_advance=can_counterattack,
                )
                response.update(turn_state)

                session.commit()

                return jsonify(response)

        # Attack hits - either no defensive effect, or attacker won opposed roll
        response["attack_result"] = "hit"

        # Calculate damage
        base_damage = weapon.damage + enemy_ship.weapons_damage_bonus()

        # Apply defensive effects to target's resistance
        effective_resistance, _, defense_details = apply_effects_to_defense(
            encounter_model, player_ship.resistance
        )

        # Apply resistance (minimum 1 damage remains)
        damage_after_resistance = max(1, base_damage - effective_resistance)

        # Apply complications to reduce damage
        complication_reduction = response.get("attacker_complications", 0) if has_defensive_effect else 0
        total_damage = max(0, damage_after_resistance - complication_reduction)

        # Apply to target - shields absorb first (only if raised)
        if player_ship.shields_raised and player_ship.shields > 0:
            shield_damage = min(player_ship.shields, total_damage)
            player_ship.shields -= shield_damage
            remaining_damage = total_damage - shield_damage
        else:
            # Shields are down - damage goes straight to hull
            shield_damage = 0
            remaining_damage = total_damage
        hull_damage = remaining_damage

        breaches_caused = 0
        systems_hit = []

        if hull_damage > 0:
            if hull_damage >= 5:
                breaches_caused = hull_damage // 5
            else:
                breaches_caused = 1

            for i in range(breaches_caused):
                system_roll = random.randint(1, 20)
                if system_roll == 1:
                    system_hit = "comms"
                elif system_roll == 2:
                    system_hit = "computers"
                elif system_roll <= 6:
                    system_hit = "engines"
                elif system_roll <= 9:
                    system_hit = "sensors"
                elif system_roll <= 17:
                    system_hit = "structure"
                else:
                    system_hit = "weapons"

                player_ship.add_breach(SystemType(system_hit))
                systems_hit.append(system_hit)

        # Update player ship in database
        player_ship_record.shields = player_ship.shields
        breaches_data = [
            {"system": b.system.value, "potency": b.potency}
            for b in player_ship.breaches
        ]
        player_ship_record.breaches_json = json.dumps(breaches_data)

        # Save state
        encounter_record.active_effects_json = json.dumps([e.to_dict() for e in encounter_model.active_effects])
        session.commit()

        response.update({
            "base_damage": base_damage,
            "effective_resistance": effective_resistance,
            "damage_after_resistance": damage_after_resistance,
            "complication_reduction": complication_reduction,
            "total_damage": total_damage,
            "shield_damage": shield_damage,
            "hull_damage": hull_damage,
            "breaches_caused": breaches_caused,
            "systems_hit": systems_hit,
            "target_shields_remaining": player_ship.shields,
            "message": f"{enemy_ship.name} hit {player_ship.name} for {total_damage} damage!"
        })

        # Build description for log
        crew_quality = enemy_ship.crew_quality.value if enemy_ship.crew_quality else "Talented"
        description = f"Fired {weapon.name} at {player_ship.name}: Hit for {total_damage} damage!"
        if breaches_caused > 0:
            description += f" Caused {breaches_caused} breach(es) to {', '.join(systems_hit)}."

        # Use ActionCompletionManager for consistent logging and turn handling
        manager = ActionCompletionManager(
            session, encounter_record,
            alternate_turn_after_action, log_combat_action
        )

        turn_state = manager.complete_enemy_major(
            enemy_id=enemy_id,
            enemy_scale=enemy_record.scale,
            actor_name=f"{enemy_ship.name} Crew ({crew_quality})",
            ship_name=enemy_ship.name,
            action_name=f"Fire {weapon.name}",
            description=description,
            task_result={
                "attacker_rolls": response.get("attacker_rolls", []),
                "attacker_successes": response.get("attacker_successes", 0),
            } if has_defensive_effect else None,
            damage_dealt=total_damage,
        )
        response.update(turn_state)

        session.commit()

        return jsonify(response)

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/resolve-defensive-roll", methods=["POST"])
def resolve_defensive_roll(encounter_id: str):
    """Resolve the player's defensive roll for a pending attack.

    The player makes their opposed roll (Daring + Security, assisted by Weapons + Security),
    and this endpoint compares it to the attacker's roll and resolves the attack.
    """
    import random

    data = request.json
    defender_rolls = data.get("defender_rolls", [])  # Player's 2d20 rolls
    ship_assist_roll = data.get("ship_assist_roll")  # Ship's assist roll

    session = get_session()
    try:
        # Load encounter
        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Check for pending attack
        if not encounter_record.pending_attack_json:
            return jsonify({"error": "No pending attack to resolve"}), 400

        pending_attack = json.loads(encounter_record.pending_attack_json)

        # Load player ship (defender)
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter_record.player_ship_id
        ).first()
        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404
        player_ship = player_ship_record.to_model()

        # Load player character for stats
        player_char_record = session.query(CharacterRecord).filter_by(
            id=encounter_record.player_character_id
        ).first()
        player_char = player_char_record.to_model() if player_char_record else None

        # Load attacking enemy ship
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json)
        enemy_index = pending_attack["attacker_index"]
        if enemy_index >= len(enemy_ids):
            return jsonify({"error": "Invalid enemy ship"}), 400

        enemy_id = enemy_ids[enemy_index]
        enemy_record = session.query(StarshipRecord).filter_by(id=enemy_id).first()
        if not enemy_record:
            return jsonify({"error": "Enemy ship not found"}), 404
        enemy_ship = enemy_record.to_model()

        weapon_index = pending_attack["weapon_index"]
        if weapon_index >= len(enemy_ship.weapons):
            return jsonify({"error": "Invalid weapon"}), 400
        weapon = enemy_ship.weapons[weapon_index]

        # Load active effects for later
        active_effects_data = json.loads(encounter_record.active_effects_json)
        active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]
        from sta.models.combat import Encounter as EncounterModel
        encounter_model = EncounterModel(
            id=encounter_record.encounter_id,
            momentum=encounter_record.momentum,
            active_effects=active_effects,
        )

        # Defender stats
        if player_char:
            defender_attr = player_char.attributes.daring
            defender_disc = player_char.disciplines.security
        else:
            defender_attr = 9
            defender_disc = 3

        defender_target = defender_attr + defender_disc
        ship_target = player_ship.systems.weapons + player_ship.departments.security

        # Calculate defender successes from provided rolls
        defender_successes = 0
        defender_complications = 0

        for roll in defender_rolls:
            if roll == 1:
                defender_successes += 2  # Critical
            elif roll <= defender_target:
                defender_successes += 1
            if roll == 20:
                defender_complications += 1

        # Ship assist
        if ship_assist_roll == 1:
            defender_successes += 2
        elif ship_assist_roll <= ship_target:
            defender_successes += 1
        if ship_assist_roll == 20:
            defender_complications += 1

        # Attacker rolls - enemy uses Control + Security, assisted by Weapons + Security
        attacker_attr = 9  # Default enemy Control
        attacker_disc = 3  # Default enemy Security
        attacker_target = attacker_attr + attacker_disc
        enemy_ship_target = enemy_ship.systems.weapons + enemy_ship.departments.security

        attacker_rolls = [random.randint(1, 20), random.randint(1, 20)]
        enemy_assist_roll = random.randint(1, 20)

        attacker_successes = 0
        attacker_complications = 0

        for roll in attacker_rolls:
            if roll == 1:
                attacker_successes += 2
            elif roll <= attacker_target:
                attacker_successes += 1
            if roll == 20:
                attacker_complications += 1

        if enemy_assist_roll == 1:
            attacker_successes += 2
        elif enemy_assist_roll <= enemy_ship_target:
            attacker_successes += 1
        if enemy_assist_roll == 20:
            attacker_complications += 1

        # Opposed roll: defender wins if they have equal or more successes
        defender_wins = defender_successes >= attacker_successes

        response = {
            "attacker": enemy_ship.name,
            "attacker_weapon": weapon.name,
            "defender": player_ship.name,
            "opposed_roll": True,
            "defender_rolls": defender_rolls,
            "defender_target": defender_target,
            "defender_ship_roll": ship_assist_roll,
            "defender_ship_target": ship_target,
            "defender_successes": defender_successes,
            "defender_complications": defender_complications,
            "attacker_rolls": attacker_rolls,
            "attacker_target": attacker_target,
            "attacker_ship_roll": enemy_assist_roll,
            "attacker_ship_target": enemy_ship_target,
            "attacker_successes": attacker_successes,
            "attacker_complications": attacker_complications,
            "defender_wins": defender_wins,
        }

        # Clear pending attack
        encounter_record.pending_attack_json = None

        # Get turn tracking info
        ships_turns_used = json.loads(encounter_record.ships_turns_used_json)
        ship_turns_used = ships_turns_used.get(str(enemy_id), 0)

        if defender_wins:
            # Attack misses!
            response["attack_result"] = "missed"
            response["message"] = f"{player_ship.name} successfully defended! Attack misses."

            # Check for counterattack option
            defensive_fire_weapon_index = pending_attack.get("defensive_fire_weapon_index")
            can_counterattack = False
            if defensive_fire_weapon_index is not None and defensive_fire_weapon_index < len(player_ship.weapons):
                counterattack_weapon = player_ship.weapons[defensive_fire_weapon_index]
                can_counterattack = True
                response["can_counterattack"] = True
                response["counterattack_cost"] = 2
                response["counterattack_weapon"] = counterattack_weapon.name
                response["counterattack_weapon_index"] = defensive_fire_weapon_index
                response["counterattack_target_index"] = enemy_index
                response["current_momentum"] = encounter_record.momentum
                response["message"] += f" May spend 2 Momentum to counterattack with {counterattack_weapon.name}."

            # Use ActionCompletionManager for consistent logging and turn handling
            crew_quality = enemy_ship.crew_quality.value if enemy_ship.crew_quality else "Talented"
            manager = ActionCompletionManager(
                session, encounter_record,
                alternate_turn_after_action, log_combat_action
            )

            # Log the defended attack, skip turn advance if counterattack is available
            turn_state = manager.complete_enemy_major(
                enemy_id=enemy_id,
                enemy_scale=enemy_record.scale,
                actor_name=f"{enemy_ship.name} Crew ({crew_quality})",
                ship_name=enemy_ship.name,
                action_name=f"Fire {weapon.name}",
                description=f"Fired {weapon.name} at {player_ship.name}: Attack defended! ({attacker_successes} vs {defender_successes} successes)",
                task_result={
                    "attacker_rolls": attacker_rolls,
                    "attacker_successes": attacker_successes,
                    "defender_rolls": defender_rolls,
                    "defender_successes": defender_successes,
                    "defender_wins": True,
                },
                damage_dealt=0,
                skip_turn_advance=can_counterattack,
            )
            response.update(turn_state)

            session.commit()
            return jsonify(response)

        # Attack hits - attacker won the opposed roll
        response["attack_result"] = "hit"

        # Calculate damage
        base_damage = weapon.damage + enemy_ship.weapons_damage_bonus()

        # Apply defensive effects to target's resistance
        effective_resistance, _, defense_details = apply_effects_to_defense(
            encounter_model, player_ship.resistance
        )

        # Apply resistance
        damage_after_resistance = max(1, base_damage - effective_resistance)

        # Apply attacker complications to reduce damage
        complication_reduction = attacker_complications
        total_damage = max(0, damage_after_resistance - complication_reduction)

        # Apply to target - shields absorb first (only if raised)
        if player_ship.shields_raised and player_ship.shields > 0:
            shield_damage = min(player_ship.shields, total_damage)
            player_ship.shields -= shield_damage
            remaining_damage = total_damage - shield_damage
        else:
            shield_damage = 0
            remaining_damage = total_damage
        hull_damage = remaining_damage

        breaches_caused = 0
        systems_hit = []

        if hull_damage > 0:
            if hull_damage >= 5:
                breaches_caused = hull_damage // 5
            else:
                breaches_caused = 1

            for i in range(breaches_caused):
                system_roll = random.randint(1, 20)
                if system_roll == 1:
                    system_hit = "comms"
                elif system_roll == 2:
                    system_hit = "computers"
                elif system_roll <= 6:
                    system_hit = "engines"
                elif system_roll <= 9:
                    system_hit = "sensors"
                elif system_roll <= 17:
                    system_hit = "structure"
                else:
                    system_hit = "weapons"

                player_ship.add_breach(SystemType(system_hit))
                systems_hit.append(system_hit)

        # Update player ship in database
        player_ship_record.shields = player_ship.shields
        breaches_data = [
            {"system": b.system.value, "potency": b.potency}
            for b in player_ship.breaches
        ]
        player_ship_record.breaches_json = json.dumps(breaches_data)

        response.update({
            "base_damage": base_damage,
            "effective_resistance": effective_resistance,
            "damage_after_resistance": damage_after_resistance,
            "complication_reduction": complication_reduction,
            "total_damage": total_damage,
            "shield_damage": shield_damage,
            "hull_damage": hull_damage,
            "breaches_caused": breaches_caused,
            "systems_hit": systems_hit,
            "target_shields_remaining": player_ship.shields,
            "message": f"{enemy_ship.name} hit {player_ship.name} for {total_damage} damage!",
        })

        # Build description for log
        crew_quality = enemy_ship.crew_quality.value if enemy_ship.crew_quality else "Talented"
        description = f"Fired {weapon.name} at {player_ship.name}: Hit for {total_damage} damage!"
        if breaches_caused > 0:
            description += f" Caused {breaches_caused} breach(es) to {', '.join(systems_hit)}."

        # Use ActionCompletionManager for consistent logging and turn handling
        manager = ActionCompletionManager(
            session, encounter_record,
            alternate_turn_after_action, log_combat_action
        )

        turn_state = manager.complete_enemy_major(
            enemy_id=enemy_id,
            enemy_scale=enemy_record.scale,
            actor_name=f"{enemy_ship.name} Crew ({crew_quality})",
            ship_name=enemy_ship.name,
            action_name=f"Fire {weapon.name}",
            description=description,
            task_result={
                "attacker_rolls": attacker_rolls,
                "attacker_successes": attacker_successes,
                "defender_rolls": defender_rolls,
                "defender_successes": defender_successes,
                "defender_wins": False,
            },
            damage_dealt=total_damage,
        )
        response.update(turn_state)

        session.commit()
        return jsonify(response)

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/counterattack", methods=["POST"])
def counterattack(encounter_id: str):
    """Execute a counterattack after successful Defensive Fire.

    Costs 2 Momentum. Uses the weapon stored in the Defensive Fire effect.
    """
    import random

    data = request.json
    weapon_index = data.get("weapon_index", 0)
    target_index = data.get("target_index", 0)  # Which enemy to counterattack
    character_id = data.get("character_id")  # Optional: override acting character for logging

    session = get_session()
    try:
        # Load encounter
        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()
        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Check momentum
        if encounter_record.momentum < 2:
            return jsonify({"error": "Not enough Momentum! Counterattack costs 2 Momentum."}), 400

        # Load player ship
        player_ship_record = session.query(StarshipRecord).filter_by(
            id=encounter_record.player_ship_id
        ).first()
        if not player_ship_record:
            return jsonify({"error": "Player ship not found"}), 404
        player_ship = player_ship_record.to_model()

        # Load player character (use provided character_id or fall back to encounter default)
        char_id = character_id if character_id else encounter_record.player_character_id
        player_char_record = session.query(CharacterRecord).filter_by(id=char_id).first() if char_id else None
        player_char = player_char_record.to_model() if player_char_record else None

        # Load target enemy ship
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json)
        if target_index >= len(enemy_ids):
            return jsonify({"error": "Invalid target"}), 400

        target_id = enemy_ids[target_index]
        target_record = session.query(StarshipRecord).filter_by(id=target_id).first()
        if not target_record:
            return jsonify({"error": "Target ship not found"}), 404
        target_ship = target_record.to_model()

        # Get weapon
        if weapon_index >= len(player_ship.weapons):
            return jsonify({"error": "Invalid weapon"}), 400
        weapon = player_ship.weapons[weapon_index]

        # Spend 2 Momentum
        encounter_record.momentum -= 2

        # Roll the counterattack - same as normal Fire
        if player_char:
            attr = player_char.attributes.control
            disc = player_char.disciplines.security
        else:
            attr = 9
            disc = 3

        target_number = attr + disc
        ship_target = player_ship.systems.weapons + player_ship.departments.security

        rolls = [random.randint(1, 20), random.randint(1, 20)]
        ship_roll = random.randint(1, 20)

        successes = 0
        complications = 0

        for roll in rolls:
            if roll == 1:
                successes += 2
            elif roll <= target_number:
                successes += 1
            if roll == 20:
                complications += 1

        if ship_roll == 1:
            successes += 2
        elif ship_roll <= ship_target:
            successes += 1
        if ship_roll == 20:
            complications += 1

        difficulty = 2  # Standard Fire difficulty
        succeeded = successes >= difficulty
        momentum_generated = max(0, successes - difficulty) if succeeded else 0

        response = {
            "counterattack": True,
            "rolls": rolls,
            "target_number": target_number,
            "ship_roll": ship_roll,
            "ship_target": ship_target,
            "successes": successes,
            "complications": complications,
            "difficulty": difficulty,
            "succeeded": succeeded,
            "momentum_generated": momentum_generated,
            "momentum_spent": 2,
            "momentum_remaining": encounter_record.momentum,
        }

        if succeeded:
            # Calculate damage
            base_damage = weapon.damage + player_ship.weapons_damage_bonus()
            effective_resistance = target_ship.resistance

            damage_after_resistance = max(1, base_damage - effective_resistance)
            complication_reduction = complications
            total_damage = max(0, damage_after_resistance - complication_reduction)

            # Shields absorb first (only if raised)
            if target_ship.shields_raised and target_ship.shields > 0:
                shield_damage = min(target_ship.shields, total_damage)
                target_ship.shields -= shield_damage
                remaining_damage = total_damage - shield_damage
            else:
                shield_damage = 0
                remaining_damage = total_damage
            hull_damage = remaining_damage

            breaches_caused = 0
            systems_hit = []

            if hull_damage > 0:
                if hull_damage >= 5:
                    breaches_caused = hull_damage // 5
                else:
                    breaches_caused = 1

                for i in range(breaches_caused):
                    system_roll = random.randint(1, 20)
                    if system_roll == 1:
                        system_hit = "comms"
                    elif system_roll == 2:
                        system_hit = "computers"
                    elif system_roll <= 6:
                        system_hit = "engines"
                    elif system_roll <= 9:
                        system_hit = "sensors"
                    elif system_roll <= 17:
                        system_hit = "structure"
                    else:
                        system_hit = "weapons"

                    target_ship.add_breach(SystemType(system_hit))
                    systems_hit.append(system_hit)

            # Update target ship in database
            target_record.shields = target_ship.shields
            breaches_data = [
                {"system": b.system.value, "potency": b.potency}
                for b in target_ship.breaches
            ]
            target_record.breaches_json = json.dumps(breaches_data)

            # Add generated momentum
            if momentum_generated > 0:
                momentum_to_add = min(momentum_generated, 6 - encounter_record.momentum)
                encounter_record.momentum += momentum_to_add

            response.update({
                "base_damage": base_damage,
                "effective_resistance": effective_resistance,
                "damage_after_resistance": damage_after_resistance,
                "complication_reduction": complication_reduction,
                "total_damage": total_damage,
                "shield_damage": shield_damage,
                "hull_damage": hull_damage,
                "breaches_caused": breaches_caused,
                "systems_hit": systems_hit,
                "target_shields_remaining": target_ship.shields,
                "message": f"Counterattack hit {target_ship.name} for {total_damage} damage!"
            })
        else:
            response["message"] = "Counterattack missed!"

        # Build description for log
        actor_name = player_char.name if player_char else "Tactical Officer"
        if succeeded:
            damage = response.get("total_damage", 0)
            description = f"Counterattack with {weapon.name} at {target_ship.name}: {successes} successes vs difficulty {difficulty}. Hit for {damage} damage!"
            if response.get("breaches_caused", 0) > 0:
                description += f" Caused {response['breaches_caused']} breach(es) to {', '.join(response.get('systems_hit', []))}."
        else:
            description = f"Counterattack with {weapon.name} at {target_ship.name}: {successes} successes vs difficulty {difficulty}. Missed!"

        # Use ActionCompletionManager for consistent logging and turn handling
        # Counterattack is special: player action that ends the ENEMY's turn
        manager = ActionCompletionManager(
            session, encounter_record,
            alternate_turn_after_action, log_combat_action
        )

        turn_state = manager.complete_counterattack(
            enemy_id=target_id,
            enemy_scale=target_record.scale,
            actor_name=actor_name,
            player_ship_name=player_ship.name,
            action_name=f"Counterattack ({weapon.name})",
            description=description,
            task_result={
                "rolls": rolls,
                "target_number": target_number,
                "successes": successes,
                "complications": complications,
                "succeeded": succeeded,
            },
            damage_dealt=response.get("total_damage", 0),
            momentum_spent=2,
        )
        response.update(turn_state)

        session.commit()
        return jsonify(response)

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>", methods=["DELETE"])
def delete_encounter(encounter_id: str):
    """Delete an encounter and optionally its associated ships."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Delete enemy ships associated with this encounter
        enemy_ids = json.loads(encounter.enemy_ship_ids_json)
        for enemy_id in enemy_ids:
            enemy_ship = session.query(StarshipRecord).filter_by(id=enemy_id).first()
            if enemy_ship:
                session.delete(enemy_ship)

        # Delete the encounter
        session.delete(encounter)
        session.commit()

        return jsonify({"success": True, "message": "Encounter deleted"})
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/combat-log", methods=["GET"])
def get_combat_log(encounter_id: str):
    """Get the combat log for an encounter.

    Query params:
        since_id: int - Only return log entries after this ID (for polling)
        round: int - Only return log entries from this round
        limit: int - Maximum number of entries to return (default 50)

    Returns:
        JSON with log entries, newest first
    """
    since_id = request.args.get("since_id", type=int)
    round_filter = request.args.get("round", type=int)
    limit = request.args.get("limit", default=50, type=int)

    session = get_session()
    try:
        # Get the encounter to get its primary key ID
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Build query
        query = session.query(CombatLogRecord).filter_by(
            encounter_id=encounter.id
        )

        if since_id:
            query = query.filter(CombatLogRecord.id > since_id)

        if round_filter is not None:
            query = query.filter(CombatLogRecord.round == round_filter)

        # Order by ID descending (newest first) and limit
        log_entries = query.order_by(CombatLogRecord.id.desc()).limit(limit).all()

        # Convert to JSON-serializable format
        entries = []
        for entry in log_entries:
            entries.append({
                "id": entry.id,
                "round": entry.round,
                "actor_name": entry.actor_name,
                "actor_type": entry.actor_type,
                "ship_name": entry.ship_name,
                "action_name": entry.action_name,
                "action_type": entry.action_type,
                "description": entry.description,
                "task_result": json.loads(entry.task_result_json) if entry.task_result_json else None,
                "damage_dealt": entry.damage_dealt,
                "momentum_spent": entry.momentum_spent,
                "threat_spent": entry.threat_spent,
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            })

        # Reverse to get oldest-first order for display
        entries.reverse()

        return jsonify({
            "log": entries,
            "count": len(entries),
            "latest_id": log_entries[0].id if log_entries else None,
        })

    finally:
        session.close()


# ========== TACTICAL MAP ENDPOINTS ==========

@api_bp.route("/encounter/<encounter_id>/map", methods=["GET"])
def get_tactical_map(encounter_id: str):
    """Get the tactical map data for an encounter."""
    role = request.args.get("role", "player")

    session = get_session()
    try:
        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Parse tactical map data
        tactical_map_data = json.loads(encounter_record.tactical_map_json or "{}")
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")

        # Build ship positions list with names
        ship_positions = []

        # Player ship position
        player_pos = ship_positions_data.get("player", {"q": 0, "r": 0})
        if encounter_record.player_ship_id:
            player_ship = session.query(StarshipRecord).get(encounter_record.player_ship_id)
            ship_positions.append({
                "id": "player",
                "name": player_ship.name if player_ship else "Player Ship",
                "faction": "player",
                "position": player_pos
            })

        # Get detected positions for visibility filtering (player role only)
        detected_positions = []
        if role == "player":
            active_effects_data = json.loads(encounter_record.active_effects_json or "[]")
            active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]
            detected_positions = get_detected_positions_from_effects(active_effects)

        # Enemy ship positions
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json or "[]")
        for i, enemy_id in enumerate(enemy_ids):
            enemy_ship = session.query(StarshipRecord).get(enemy_id)
            enemy_pos = ship_positions_data.get(f"enemy_{i}", {"q": 2, "r": -1 + i})

            # For player role, filter by visibility
            if role == "player":
                if not is_ship_visible_to_player(player_pos, enemy_pos, tactical_map_data, detected_positions):
                    continue  # Skip hidden enemy

            ship_positions.append({
                "id": f"enemy_{i}",
                "name": enemy_ship.name if enemy_ship else f"Enemy {i+1}",
                "faction": "enemy",
                "position": enemy_pos
            })

        return jsonify({
            "tactical_map": tactical_map_data,
            "ship_positions": ship_positions
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/map/terrain", methods=["POST"])
def update_map_terrain(encounter_id: str):
    """Update terrain at a specific hex coordinate."""
    session = get_session()
    try:
        data = request.json
        q = data.get("q")
        r = data.get("r")
        terrain = data.get("terrain", "open")

        if q is None or r is None:
            return jsonify({"error": "Missing q or r coordinate"}), 400

        # Validate terrain type
        try:
            terrain_type = TerrainType(terrain)
        except ValueError:
            return jsonify({"error": f"Invalid terrain type: {terrain}"}), 400

        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Load current map data
        tactical_map_data = json.loads(encounter_record.tactical_map_json or "{}")

        # Initialize map if empty
        if not tactical_map_data or "radius" not in tactical_map_data:
            tactical_map_data = {"radius": 3, "tiles": []}

        # Update or add tile
        tiles = tactical_map_data.get("tiles", [])
        found = False
        for tile in tiles:
            if tile.get("coord", {}).get("q") == q and tile.get("coord", {}).get("r") == r:
                tile["terrain"] = terrain
                found = True
                break

        if not found and terrain != "open":
            # Only add non-open tiles (open is the default)
            tiles.append({
                "coord": {"q": q, "r": r},
                "terrain": terrain,
                "traits": []
            })
        elif found and terrain == "open":
            # Remove tile if set back to open (default)
            tiles = [t for t in tiles if not (t.get("coord", {}).get("q") == q and t.get("coord", {}).get("r") == r)]

        tactical_map_data["tiles"] = tiles

        # Save back to database
        encounter_record.tactical_map_json = json.dumps(tactical_map_data)
        session.commit()

        return jsonify({
            "success": True,
            "tactical_map": tactical_map_data,
            "message": f"Terrain at ({q}, {r}) set to {terrain}"
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/map/ship-position", methods=["POST"])
def update_ship_position(encounter_id: str):
    """Update a ship's position on the tactical map."""
    session = get_session()
    try:
        data = request.json
        ship_id = data.get("ship_id")  # "player" or "enemy_0", "enemy_1", etc.
        q = data.get("q")
        r = data.get("r")

        if not ship_id or q is None or r is None:
            return jsonify({"error": "Missing ship_id, q, or r"}), 400

        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Load current positions
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")

        # Update position
        ship_positions_data[ship_id] = {"q": q, "r": r}

        # Save back to database
        encounter_record.ship_positions_json = json.dumps(ship_positions_data)
        session.commit()

        # Build ship positions list with names for response
        ship_positions = []
        tactical_map_data = json.loads(encounter_record.tactical_map_json or "{}")

        # Player ship
        player_pos = ship_positions_data.get("player", {"q": 0, "r": 0})
        if encounter_record.player_ship_id:
            player_ship = session.query(StarshipRecord).get(encounter_record.player_ship_id)
            ship_positions.append({
                "id": "player",
                "name": player_ship.name if player_ship else "Player Ship",
                "faction": "player",
                "position": player_pos
            })

        # Enemy ships
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json or "[]")
        for i, enemy_id in enumerate(enemy_ids):
            enemy_ship = session.query(StarshipRecord).get(enemy_id)
            enemy_pos = ship_positions_data.get(f"enemy_{i}", {"q": 2, "r": -1 + i})
            ship_positions.append({
                "id": f"enemy_{i}",
                "name": enemy_ship.name if enemy_ship else f"Enemy {i+1}",
                "faction": "enemy",
                "position": enemy_pos
            })

        return jsonify({
            "success": True,
            "ship_positions": ship_positions,
            "message": f"Ship {ship_id} moved to ({q}, {r})"
        })

    finally:
        session.close()


# ========== ENEMY SHIP MANAGEMENT ENDPOINTS ==========

@api_bp.route("/encounter/<encounter_id>/enemy-ships", methods=["POST"])
def add_enemy_ship(encounter_id: str):
    """Add a new enemy ship to an existing encounter.

    Request body:
    - crew_quality: "basic", "proficient", "talented", or "exceptional" (default: "talented")
    - faction: "klingon" or "romulan" (optional, random if not specified)
    - difficulty: "easy", "standard", or "hard" (default: "standard")

    Returns the new enemy ship data and updated ship lists.
    """
    from sta.generators.starship import generate_enemy_ship
    from sta.models.enums import CrewQuality

    session = get_session()
    try:
        data = request.json or {}
        crew_quality_str = data.get("crew_quality", "talented")
        faction = data.get("faction")  # None = random
        difficulty = data.get("difficulty", "standard")

        # Parse crew quality
        try:
            crew_quality = CrewQuality(crew_quality_str)
        except ValueError:
            crew_quality = CrewQuality.TALENTED

        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Generate new enemy ship
        enemy = generate_enemy_ship(
            difficulty=difficulty,
            faction=faction,
            crew_quality=crew_quality
        )
        enemy_record = StarshipRecord.from_model(enemy)
        session.add(enemy_record)
        session.flush()

        # Add to encounter's enemy ship list
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json or "[]")
        enemy_ids.append(enemy_record.id)
        encounter_record.enemy_ship_ids_json = json.dumps(enemy_ids)

        # Set initial position for new enemy ship (offset from existing enemies)
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")
        enemy_index = len(enemy_ids) - 1
        # Place new enemy ship at offset position
        ship_positions_data[f"enemy_{enemy_index}"] = {"q": 2, "r": -1 + enemy_index}
        encounter_record.ship_positions_json = json.dumps(ship_positions_data)

        session.commit()

        # Build response with all enemy ship data
        all_enemies = []
        for i, eid in enumerate(enemy_ids):
            enemy_ship = session.query(StarshipRecord).get(eid)
            if enemy_ship:
                enemy_model = enemy_ship.to_model()
                all_enemies.append({
                    "id": eid,
                    "index": i,
                    "name": enemy_model.name,
                    "ship_class": enemy_model.ship_class,
                    "scale": enemy_model.scale,
                    "shields": enemy_model.shields,
                    "shields_max": enemy_model.shields_max,
                    "crew_quality": enemy_model.crew_quality.value if enemy_model.crew_quality else "talented",
                })

        return jsonify({
            "success": True,
            "message": f"Added {enemy.name} to encounter",
            "new_enemy": {
                "id": enemy_record.id,
                "index": enemy_index,
                "name": enemy.name,
                "ship_class": enemy.ship_class,
                "scale": enemy.scale,
                "shields": enemy.shields,
                "shields_max": enemy.shields_max,
                "crew_quality": crew_quality.value,
            },
            "all_enemies": all_enemies,
            "enemy_count": len(enemy_ids),
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/enemy-ships/<int:enemy_index>", methods=["DELETE"])
def remove_enemy_ship(encounter_id: str, enemy_index: int):
    """Remove an enemy ship from an encounter.

    Note: This removes the ship from the encounter but doesn't delete the ship record.
    """
    session = get_session()
    try:
        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json or "[]")

        if enemy_index < 0 or enemy_index >= len(enemy_ids):
            return jsonify({"error": "Invalid enemy index"}), 400

        # Get ship name before removing
        removed_id = enemy_ids[enemy_index]
        removed_ship = session.query(StarshipRecord).get(removed_id)
        removed_name = removed_ship.name if removed_ship else f"Enemy {enemy_index + 1}"

        # Remove from list
        enemy_ids.pop(enemy_index)
        encounter_record.enemy_ship_ids_json = json.dumps(enemy_ids)

        # Update ship positions (reindex remaining enemies)
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")
        new_positions = {}
        for key, value in ship_positions_data.items():
            if key == "player":
                new_positions[key] = value
            elif key.startswith("enemy_"):
                old_idx = int(key.split("_")[1])
                if old_idx < enemy_index:
                    new_positions[key] = value
                elif old_idx > enemy_index:
                    # Reindex to fill the gap
                    new_positions[f"enemy_{old_idx - 1}"] = value
                # Skip the removed enemy's position
        encounter_record.ship_positions_json = json.dumps(new_positions)

        # Update ships_turns_used_json (reindex remaining enemies)
        ships_turns_used = json.loads(encounter_record.ships_turns_used_json or "{}")
        new_turns_used = {}
        for ship_id_str, turns in ships_turns_used.items():
            ship_id = int(ship_id_str)
            if ship_id != removed_id:
                new_turns_used[ship_id_str] = turns
        encounter_record.ships_turns_used_json = json.dumps(new_turns_used)

        session.commit()

        return jsonify({
            "success": True,
            "message": f"Removed {removed_name} from encounter",
            "enemy_count": len(enemy_ids),
        })

    finally:
        session.close()


# ========== MOVEMENT ACTION ENDPOINTS ==========

@api_bp.route("/encounter/<encounter_id>/move/valid-destinations", methods=["GET"])
def get_valid_move_destinations(encounter_id: str):
    """Get valid movement destinations for Impulse action."""
    from sta.mechanics.movement import get_valid_impulse_moves
    from sta.models.combat import HexCoord, TacticalMap

    session = get_session()
    try:
        action = request.args.get("action", "impulse")
        ship_id = request.args.get("ship_id", "player")

        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Load map and positions
        tactical_map_data = json.loads(encounter_record.tactical_map_json or "{}")
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")

        # Create TacticalMap model
        tactical_map = TacticalMap.from_dict(tactical_map_data)

        # Get ship's current position
        if ship_id == "player":
            pos_data = ship_positions_data.get("player", {"q": 0, "r": 0})
        else:
            pos_data = ship_positions_data.get(ship_id, {"q": 2, "r": -1})

        start = HexCoord(q=pos_data.get("q", 0), r=pos_data.get("r", 0))

        # Get valid moves based on action type
        if action == "impulse":
            valid_moves = get_valid_impulse_moves(
                start=start,
                tactical_map=tactical_map,
                max_distance=2,
                momentum_available=encounter_record.momentum
            )
        else:
            # Thrusters doesn't move hexes - handled separately
            valid_moves = []

        return jsonify({
            "action": action,
            "current_position": {"q": start.q, "r": start.r},
            "valid_moves": [
                {
                    "q": m.coord.q,
                    "r": m.coord.r,
                    "cost": m.cost,
                    "terrain": m.terrain.value
                }
                for m in valid_moves
            ],
            "momentum_available": encounter_record.momentum
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/move/impulse", methods=["POST"])
def execute_impulse_move(encounter_id: str):
    """Execute an Impulse movement action."""
    from sta.mechanics.movement import execute_impulse_move as do_impulse
    from sta.models.combat import HexCoord, TacticalMap

    session = get_session()
    try:
        data = request.json
        q = data.get("q")
        r = data.get("r")
        use_threat = data.get("use_threat", False)
        ship_id = data.get("ship_id", "player")

        if q is None or r is None:
            return jsonify({"error": "Missing q or r coordinates"}), 400

        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Load map and positions
        tactical_map_data = json.loads(encounter_record.tactical_map_json or "{}")
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")

        # Create TacticalMap model
        tactical_map = TacticalMap.from_dict(tactical_map_data)

        # Get ship's current position
        if ship_id == "player":
            pos_data = ship_positions_data.get("player", {"q": 0, "r": 0})
        else:
            pos_data = ship_positions_data.get(ship_id, {"q": 2, "r": -1})

        start = HexCoord(q=pos_data.get("q", 0), r=pos_data.get("r", 0))
        destination = HexCoord(q=q, r=r)

        # Execute movement
        result = do_impulse(
            start=start,
            destination=destination,
            tactical_map=tactical_map,
            momentum_available=encounter_record.momentum,
            use_threat=use_threat
        )

        if not result.success:
            return jsonify({
                "success": False,
                "error": result.message
            }), 400

        # Update ship position in database
        ship_positions_data[ship_id] = {"q": q, "r": r}
        encounter_record.ship_positions_json = json.dumps(ship_positions_data)

        # Update momentum/threat
        if result.momentum_cost > 0:
            encounter_record.momentum = max(0, encounter_record.momentum - result.momentum_cost)
        if result.threat_added > 0:
            encounter_record.threat += result.threat_added

        session.commit()

        # Build response with updated ship positions
        ship_positions = []

        # Player ship
        player_pos = ship_positions_data.get("player", {"q": 0, "r": 0})
        if encounter_record.player_ship_id:
            player_ship = session.query(StarshipRecord).get(encounter_record.player_ship_id)
            ship_positions.append({
                "id": "player",
                "name": player_ship.name if player_ship else "Player Ship",
                "faction": "player",
                "position": player_pos
            })

        # Enemy ships
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json or "[]")
        for i, enemy_id in enumerate(enemy_ids):
            enemy_ship = session.query(StarshipRecord).get(enemy_id)
            enemy_pos = ship_positions_data.get(f"enemy_{i}", {"q": 2, "r": -1 + i})
            ship_positions.append({
                "id": f"enemy_{i}",
                "name": enemy_ship.name if enemy_ship else f"Enemy {i+1}",
                "faction": "enemy",
                "position": enemy_pos
            })

        return jsonify({
            "success": True,
            "message": result.message,
            "new_position": {"q": q, "r": r},
            "momentum_spent": result.momentum_cost,
            "threat_added": result.threat_added,
            "hazard_damage": result.hazard_damage,
            "path": [{"q": c.q, "r": c.r} for c in result.path],
            "ship_positions": ship_positions,
            "momentum": encounter_record.momentum,
            "threat": encounter_record.threat
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/move/thrusters", methods=["POST"])
def execute_thrusters_move(encounter_id: str):
    """Execute a Thrusters action (enter/exit contact)."""
    from sta.mechanics.movement import execute_thrusters_action

    session = get_session()
    try:
        data = request.json
        action_type = data.get("action_type")  # "enter_contact" or "exit_contact"
        target_ship = data.get("target_ship")  # Ship name
        ship_id = data.get("ship_id", "player")

        if not action_type or not target_ship:
            return jsonify({"error": "Missing action_type or target_ship"}), 400

        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # For now, track contact state in a simple JSON field
        # (Could be expanded to ship_positions_json or a separate field)
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")

        # Get current contact state
        contacts_data = ship_positions_data.get("contacts", {})
        currently_in_contact = contacts_data.get(ship_id)

        result = execute_thrusters_action(
            action_type=action_type,
            target_ship=target_ship,
            currently_in_contact=currently_in_contact
        )

        if not result.success:
            return jsonify({
                "success": False,
                "error": result.message
            }), 400

        # Update contact state
        if action_type == "enter_contact":
            contacts_data[ship_id] = target_ship
        elif action_type == "exit_contact":
            contacts_data.pop(ship_id, None)

        ship_positions_data["contacts"] = contacts_data
        encounter_record.ship_positions_json = json.dumps(ship_positions_data)
        session.commit()

        return jsonify({
            "success": True,
            "message": result.message,
            "contact_state": contacts_data.get(ship_id)
        })

    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/move/thrusters/valid-actions", methods=["GET"])
def get_valid_thrusters_actions(encounter_id: str):
    """Get valid Thrusters actions for a ship."""
    from sta.mechanics.movement import get_valid_thruster_moves

    session = get_session()
    try:
        ship_id = request.args.get("ship_id", "player")

        encounter_record = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter_record:
            return jsonify({"error": "Encounter not found"}), 404

        # Load ship positions
        ship_positions_data = json.loads(encounter_record.ship_positions_json or "{}")

        # Get player's current position
        player_pos = ship_positions_data.get("player", {"q": 0, "r": 0})
        player_q, player_r = player_pos.get("q", 0), player_pos.get("r", 0)

        # Get current contact state
        contacts_data = ship_positions_data.get("contacts", {})
        currently_in_contact = contacts_data.get(ship_id)

        # Find other ships in the same hex
        ships_in_hex = []
        enemy_ids = json.loads(encounter_record.enemy_ship_ids_json or "[]")

        for i, enemy_id in enumerate(enemy_ids):
            enemy_key = f"enemy_{i}"
            enemy_pos = ship_positions_data.get(enemy_key, {"q": 2, "r": -1 + i})
            enemy_q, enemy_r = enemy_pos.get("q", 0), enemy_pos.get("r", 0)

            # Check if in same hex
            if enemy_q == player_q and enemy_r == player_r:
                # Get ship name
                enemy_ship = session.query(StarshipRecord).get(enemy_id)
                ship_name = enemy_ship.name if enemy_ship else f"Enemy {i+1}"
                ships_in_hex.append({
                    "id": enemy_key,
                    "name": ship_name
                })

        # Get valid actions
        valid_actions = get_valid_thruster_moves(
            start=None,  # Not needed for contact checks
            ships_in_hex=[s["name"] for s in ships_in_hex],
            currently_in_contact=currently_in_contact
        )

        # Enhance actions with ship IDs
        for action in valid_actions:
            for ship in ships_in_hex:
                if ship["name"] == action["target"]:
                    action["target_id"] = ship["id"]
                    break

        return jsonify({
            "valid_actions": valid_actions,
            "currently_in_contact": currently_in_contact,
            "ships_in_hex": ships_in_hex
        })

    finally:
        session.close()
