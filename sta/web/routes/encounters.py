"""Encounter routes for combat management."""

import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sta.database import (
    get_session, EncounterRecord, CharacterRecord, StarshipRecord,
    CampaignRecord
)
from sta.generators import generate_character, generate_starship
from sta.generators.starship import generate_enemy_ship
from sta.models.enums import Position, CrewQuality

encounters_bp = Blueprint("encounters", __name__)


@encounters_bp.route("/new", methods=["GET", "POST"])
def new_encounter():
    """Create a new encounter."""
    # Check for campaign context - REQUIRED
    campaign_id_param = request.args.get("campaign") or request.form.get("campaign_id")

    # If no campaign specified, redirect to GM home
    if not campaign_id_param:
        flash("Please select a campaign first")
        return redirect(url_for("campaigns.gm_home"))

    if request.method == "POST":
        session = get_session()
        try:
            # Load campaign
            campaign = session.query(CampaignRecord).filter_by(
                campaign_id=campaign_id_param
            ).first()

            if not campaign:
                flash("Campaign not found")
                return redirect(url_for("campaigns.gm_home"))

            campaign_db_id = campaign.id

            # Use campaign's active ship
            if not campaign.active_ship_id:
                flash("No ship assigned to campaign. Please add a ship first.")
                return redirect(url_for("campaigns.campaign_dashboard", campaign_id=campaign_id_param))

            ship_id = campaign.active_ship_id

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

            # Generate enemy ship with selected crew quality
            crew_quality_str = request.form.get("crew_quality", "talented")
            try:
                crew_quality = CrewQuality(crew_quality_str)
            except ValueError:
                crew_quality = CrewQuality.TALENTED

            enemy = generate_enemy_ship(difficulty="standard", crew_quality=crew_quality)
            enemy_record = StarshipRecord.from_model(enemy)
            session.add(enemy_record)
            session.flush()

            # Create encounter
            encounter_name = request.form.get("name", "New Encounter")
            position = request.form.get("position", "captain")

            # Determine initial status (draft if in campaign, active otherwise)
            initial_status = "active"
            if campaign_db_id and request.form.get("status") == "draft":
                initial_status = "draft"

            encounter = EncounterRecord(
                encounter_id=str(uuid.uuid4()),
                name=encounter_name,
                campaign_id=campaign_db_id,
                status=initial_status,
                player_character_id=char_id,
                player_ship_id=ship_id,
                player_position=position,
                enemy_ship_ids_json=f"[{enemy_record.id}]",
                threat=2,  # Starting threat
            )
            session.add(encounter)
            session.commit()

            # Redirect based on status
            if initial_status == "draft":
                return redirect(url_for("campaigns.campaign_dashboard", campaign_id=campaign.campaign_id))
            # Otherwise, go to combat view as GM
            return redirect(url_for("encounters.combat", encounter_id=encounter.encounter_id, role="gm"))
        finally:
            session.close()

    # GET - show form
    session = get_session()
    try:
        # Load campaign - required
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id_param
        ).first()

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.gm_home"))

        characters = session.query(CharacterRecord).all()
        positions = [p.value for p in Position]
        return render_template(
            "new_encounter.html",
            characters=characters,
            positions=positions,
            campaign=campaign,
        )
    finally:
        session.close()


@encounters_bp.route("/<encounter_id>")
def combat(encounter_id: str):
    """Main combat view."""
    # Get role from query parameter (default to player)
    role = request.args.get("role", "player")
    if role not in ("player", "gm"):
        role = "player"

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

        # Load active effects
        from sta.models.combat import ActiveEffect
        active_effects_data = json.loads(encounter.active_effects_json)
        active_effects = [ActiveEffect.from_dict(e) for e in active_effects_data]

        # Calculate resistance bonus from active effects
        resistance_bonus = sum(
            e.resistance_bonus for e in active_effects
            if e.applies_to in ("defense", "all") and e.resistance_bonus > 0
        )

        # Load campaign if encounter belongs to one
        campaign = None
        if encounter.campaign_id:
            campaign = session.query(CampaignRecord).filter_by(
                id=encounter.campaign_id
            ).first()

        # Select template based on role
        template = "combat_gm.html" if role == "gm" else "combat_player.html"

        return render_template(
            template,
            encounter=encounter,
            campaign=campaign,
            player_char=player_char,
            player_ship=player_ship,
            player_ship_db_id=player_ship_db_id,
            enemy_ships=enemy_ships,
            enemy_ship_db_ids=enemy_ship_db_ids,
            position=position,
            actions=actions,
            active_effects=active_effects,
            resistance_bonus=resistance_bonus,
            role=role,
        )
    finally:
        session.close()
