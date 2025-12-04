"""API routes for AJAX operations."""

import json
from flask import Blueprint, request, jsonify
from sta.database import get_session, EncounterRecord, StarshipRecord, CharacterRecord
from sta.mechanics import task_roll, assisted_task_roll
from sta.models.enums import SystemType
from sta.models.combat import ActiveEffect
from sta.mechanics.action_handlers import (
    execute_buff_action,
    execute_task_roll_action,
    apply_task_roll_success,
    check_action_requirements,
    apply_effects_to_attack,
    apply_effects_to_defense,
)
from sta.mechanics.action_config import get_action_config, is_buff_action, is_task_roll_action, is_toggle_action

api_bp = Blueprint("api", __name__)


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


@api_bp.route("/encounter/<encounter_id>/next-turn", methods=["POST"])
def next_turn(encounter_id: str):
    """Advance to next turn."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        if encounter.current_turn == "player":
            encounter.current_turn = "enemy"
        else:
            encounter.current_turn = "player"
            encounter.round += 1

        session.commit()

        return jsonify({
            "current_turn": encounter.current_turn,
            "round": encounter.round,
        })
    finally:
        session.close()


@api_bp.route("/encounter/<encounter_id>/status", methods=["GET"])
def get_encounter_status(encounter_id: str):
    """Get current encounter status (for polling)."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        return jsonify({
            "current_turn": encounter.current_turn,
            "round": encounter.round,
            "momentum": encounter.momentum,
            "threat": encounter.threat,
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

        # Load active effects to check for can_reroll
        active_effects_data = json.loads(encounter.active_effects_json)
        active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]
        from sta.models.combat import Encounter as EncounterModel
        encounter_model = EncounterModel(
            id=encounter.encounter_id,
            active_effects=active_effects,
        )

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

            # Apply to target - shields absorb first
            old_shields = target_ship.shields
            shield_damage = min(target_ship.shields, total_damage)
            target_ship.shields -= shield_damage
            remaining_damage = total_damage - shield_damage

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
            })

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

        # Execute action based on type
        if is_buff_action(action_name):
            result = execute_buff_action(action_name, encounter, config)

        elif is_task_roll_action(action_name):
            # Check if roll was already done by the frontend
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
            else:
                # Do the full roll
                if not character:
                    return jsonify({"error": "Character required for task roll"}), 400

                attribute_value = data.get("attribute", 9)
                discipline_value = data.get("discipline", 2)
                focus = data.get("focus", False)
                bonus_dice = data.get("bonus_dice", 0)

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

        else:
            return jsonify({"error": f"Action type not implemented: {config.get('type')}"}), 400

        # Save updated state
        encounter_record.momentum = encounter.momentum
        encounter_record.active_effects_json = json.dumps([e.to_dict() for e in encounter.active_effects])
        session.commit()

        return jsonify(result.to_dict())

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
