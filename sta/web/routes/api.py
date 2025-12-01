"""API routes for AJAX operations."""

import json
from flask import Blueprint, request, jsonify
from sta.database import get_session, EncounterRecord, StarshipRecord
from sta.mechanics import task_roll, assisted_task_roll
from sta.models.enums import SystemType

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

        # Perform the ship-assisted attack roll
        # Character uses Control + Security, ship assists with Weapons + Security
        result = assisted_task_roll(
            attribute=attribute,
            discipline=discipline,
            system=player_ship.systems.weapons,
            department=player_ship.departments.security,
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
            # Ship assistance info for display
            "ship_target_number": result.ship_target_number,
            "ship_roll": result.ship_roll,
            "ship_successes": result.ship_successes,
        }

        if result.succeeded:
            # Calculate damage per STA 2e rules:
            # 1. Determine base damage
            # 2. Apply Resistance (minimum 1 damage)
            # 3. Complications reduce damage by 1 each
            # 4. Apply to shields, then hull

            base_damage = weapon.damage + player_ship.weapons_damage_bonus()

            # Check for Calibrate Weapons bonus (+1 damage)
            calibrate_bonus = 0
            if encounter.calibrate_weapons_active:
                calibrate_bonus = 1
                base_damage += calibrate_bonus
                # Clear the flag after using it
                encounter.calibrate_weapons_active = False

            # Apply resistance (minimum 1 damage remains)
            damage_after_resistance = max(1, base_damage - target_ship.resistance)

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
                for _ in range(breaches_caused):
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
                "calibrate_bonus": calibrate_bonus,
                "resistance_reduction": base_damage - damage_after_resistance,
                "complication_reduction": min(complication_reduction, damage_after_resistance),
                "total_damage": total_damage,
                "shield_damage": shield_damage,
                "hull_damage": hull_damage,
                "target_shields_remaining": target_ship.shields,
                "target_resistance": target_ship.resistance,
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


@api_bp.route("/encounter/<encounter_id>/calibrate-weapons", methods=["POST"])
def calibrate_weapons(encounter_id: str):
    """Execute Calibrate Weapons minor action.

    Sets a flag that gives +1 damage to the next attack.
    """
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Set the calibrate weapons flag
        encounter.calibrate_weapons_active = True
        session.commit()

        return jsonify({
            "success": True,
            "message": "Weapons calibrated. Next attack: +1 damage.",
            "calibrate_weapons_active": True,
        })
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
