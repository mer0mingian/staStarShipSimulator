"""Encounter routes for combat management."""

import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sta.database import (
    get_session, EncounterRecord, CharacterRecord, StarshipRecord
)
from sta.generators import generate_character, generate_starship
from sta.generators.starship import generate_enemy_ship
from sta.models.enums import Position

encounters_bp = Blueprint("encounters", __name__)


@encounters_bp.route("/new", methods=["GET", "POST"])
def new_encounter():
    """Create a new encounter."""
    if request.method == "POST":
        session = get_session()
        try:
            # Generate or use existing player character
            char_action = request.form.get("character_action", "generate")
            if char_action == "generate":
                char = generate_character()
                char_record = CharacterRecord.from_model(char)
                session.add(char_record)
                session.flush()
                char_id = char_record.id
            else:
                char_id = int(request.form.get("character_id", 0))

            # Generate or use existing player ship
            ship_action = request.form.get("ship_action", "generate")
            if ship_action == "generate":
                ship = generate_starship()
                ship_record = StarshipRecord.from_model(ship)
                session.add(ship_record)
                session.flush()
                ship_id = ship_record.id
            else:
                ship_id = int(request.form.get("ship_id", 0))

            # Generate enemy ship
            enemy = generate_enemy_ship(difficulty="standard")
            enemy_record = StarshipRecord.from_model(enemy)
            session.add(enemy_record)
            session.flush()

            # Create encounter
            encounter_name = request.form.get("name", "New Encounter")
            position = request.form.get("position", "captain")

            encounter = EncounterRecord(
                encounter_id=str(uuid.uuid4()),
                name=encounter_name,
                player_character_id=char_id,
                player_ship_id=ship_id,
                player_position=position,
                enemy_ship_ids_json=f"[{enemy_record.id}]",
                threat=2,  # Starting threat
            )
            session.add(encounter)
            session.commit()

            return redirect(url_for("encounters.combat", encounter_id=encounter.encounter_id))
        finally:
            session.close()

    # GET - show form
    session = get_session()
    try:
        characters = session.query(CharacterRecord).all()
        ships = session.query(StarshipRecord).all()
        positions = [p.value for p in Position]
        return render_template(
            "new_encounter.html",
            characters=characters,
            ships=ships,
            positions=positions
        )
    finally:
        session.close()


@encounters_bp.route("/<encounter_id>")
def combat(encounter_id: str):
    """Main combat view."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            flash("Encounter not found")
            return redirect(url_for("main.index"))

        # Load player character and ship
        player_char = None
        player_ship = None
        player_ship_db_id = None
        if encounter.player_character_id:
            char_record = session.query(CharacterRecord).filter_by(
                id=encounter.player_character_id
            ).first()
            if char_record:
                player_char = char_record.to_model()

        if encounter.player_ship_id:
            ship_record = session.query(StarshipRecord).filter_by(
                id=encounter.player_ship_id
            ).first()
            if ship_record:
                player_ship = ship_record.to_model()
                player_ship_db_id = ship_record.id

        # Load enemy ships
        import json
        enemy_ids = json.loads(encounter.enemy_ship_ids_json)
        enemy_ships = []
        enemy_ship_db_ids = []
        for eid in enemy_ids:
            enemy_record = session.query(StarshipRecord).filter_by(id=eid).first()
            if enemy_record:
                enemy_ships.append(enemy_record.to_model())
                enemy_ship_db_ids.append(eid)

        # Get available actions for player's position
        from sta.mechanics.actions import get_actions_for_position
        position = Position(encounter.player_position)
        actions = get_actions_for_position(position)

        return render_template(
            "combat.html",
            encounter=encounter,
            player_char=player_char,
            player_ship=player_ship,
            player_ship_db_id=player_ship_db_id,
            enemy_ships=enemy_ships,
            enemy_ship_db_ids=enemy_ship_db_ids,
            position=position,
            actions=actions,
        )
    finally:
        session.close()
