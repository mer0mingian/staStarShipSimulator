"""Encounter routes for combat management."""

import json
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sta.database import (
    get_session, EncounterRecord, CharacterRecord, StarshipRecord,
    CampaignRecord, CampaignPlayerRecord
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

            # Generate enemy ships with selected crew quality
            crew_quality_str = request.form.get("crew_quality", "talented")
            try:
                crew_quality = CrewQuality(crew_quality_str)
            except ValueError:
                crew_quality = CrewQuality.TALENTED

            # Get enemy count from form (default 1)
            enemy_count = int(request.form.get("enemy_count", 1))
            enemy_count = max(1, min(4, enemy_count))  # Clamp to 1-4

            enemy_ids = []
            for _ in range(enemy_count):
                enemy = generate_enemy_ship(difficulty="standard", crew_quality=crew_quality)
                enemy_record = StarshipRecord.from_model(enemy)
                session.add(enemy_record)
                session.flush()
                enemy_ids.append(enemy_record.id)

            # Create encounter
            encounter_name = request.form.get("name", "New Encounter")
            encounter_description = request.form.get("description", "").strip() or None
            position = request.form.get("position", "captain")

            # Get tactical map and ship positions from form
            tactical_map_json = request.form.get("tactical_map_json", "{}")
            ship_positions_json = request.form.get("ship_positions_json", "{}")

            # Determine initial status (draft if in campaign, active otherwise)
            initial_status = "active"
            if campaign_db_id and request.form.get("status") == "draft":
                initial_status = "draft"

            encounter = EncounterRecord(
                encounter_id=str(uuid.uuid4()),
                name=encounter_name,
                description=encounter_description,
                campaign_id=campaign_db_id,
                status=initial_status,
                player_character_id=char_id,
                player_ship_id=ship_id,
                player_position=position,
                enemy_ship_ids_json=json.dumps(enemy_ids),
                tactical_map_json=tactical_map_json,
                ship_positions_json=ship_positions_json,
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


@encounters_bp.route("/<encounter_id>/edit", methods=["GET", "POST"])
def edit_encounter(encounter_id: str):
    """Edit an existing encounter."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            flash("Encounter not found")
            return redirect(url_for("campaigns.gm_home"))

        # Load campaign
        campaign = session.query(CampaignRecord).filter_by(
            id=encounter.campaign_id
        ).first()

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.gm_home"))

        if request.method == "POST":
            # Update basic fields
            encounter.name = request.form.get("name", encounter.name)
            encounter.description = request.form.get("description", "").strip() or None
            encounter.threat = int(request.form.get("threat", encounter.threat))

            # Update tactical map and ship positions
            tactical_map_json = request.form.get("tactical_map_json")
            if tactical_map_json:
                encounter.tactical_map_json = tactical_map_json

            ship_positions_json = request.form.get("ship_positions_json")
            if ship_positions_json:
                encounter.ship_positions_json = ship_positions_json

            session.commit()
            flash("Encounter updated successfully")
            return redirect(url_for("campaigns.campaign_dashboard", campaign_id=campaign.campaign_id))

        # GET - Load data for the form
        # Load player ship
        player_ship = None
        if encounter.player_ship_id:
            player_ship = session.query(StarshipRecord).filter_by(
                id=encounter.player_ship_id
            ).first()

        # Load enemy ships
        enemy_ship_ids = json.loads(encounter.enemy_ship_ids_json or "[]")
        enemy_ships = []
        for eid in enemy_ship_ids:
            enemy = session.query(StarshipRecord).filter_by(id=eid).first()
            if enemy:
                enemy_ships.append(enemy)

        # Parse tactical map and ship positions
        tactical_map = json.loads(encounter.tactical_map_json or "{}")
        if not tactical_map or "radius" not in tactical_map:
            tactical_map = {"radius": 3, "tiles": []}

        ship_positions = json.loads(encounter.ship_positions_json or "{}")

        return render_template(
            "edit_encounter.html",
            encounter=encounter,
            campaign=campaign,
            player_ship=player_ship,
            enemy_ships=enemy_ships,
            tactical_map=tactical_map,
            ship_positions=ship_positions,
            tactical_map_json=encounter.tactical_map_json or "{}",
            ship_positions_json=encounter.ship_positions_json or "{}",
        )
    finally:
        session.close()


@encounters_bp.route("/<encounter_id>")
def combat(encounter_id: str):
    """Main combat view."""
    # Get role from query parameter (default to player)
    role = request.args.get("role", "player")
    if role not in ("player", "gm", "viewscreen"):
        role = "player"

    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            flash("Encounter not found")
            return redirect(url_for("main.index"))

        # For GM role, verify they have a valid GM session for this campaign
        if role == "gm" and encounter.campaign_id:
            session_token = request.cookies.get("sta_session_token")
            gm_player = session.query(CampaignPlayerRecord).filter_by(
                campaign_id=encounter.campaign_id,
                is_gm=True
            ).first()

            if not gm_player or session_token != gm_player.session_token:
                # Not authenticated as GM - redirect to GM login
                campaign = session.query(CampaignRecord).filter_by(id=encounter.campaign_id).first()
                if campaign:
                    return redirect(url_for("campaigns.gm_login", campaign_id=campaign.campaign_id))
                else:
                    flash("Campaign not found")
                    return redirect(url_for("main.index"))

        # Load player character - from campaign membership if available, otherwise from encounter
        player_char = None
        player_char_db_id = None
        player_ship = None
        player_ship_db_id = None
        current_campaign_player = None  # Track this for position lookup later

        # Check if this is a campaign encounter and player has a campaign membership
        # Viewscreen doesn't require campaign membership - skip this check
        if encounter.campaign_id and role == "player":
            session_token = request.cookies.get("sta_session_token")
            if session_token:
                current_campaign_player = session.query(CampaignPlayerRecord).filter_by(
                    session_token=session_token,
                    campaign_id=encounter.campaign_id
                ).first()

            # If player role but no campaign membership, redirect to join the campaign
            if not current_campaign_player:
                # Get campaign_id string for redirect
                campaign = session.query(CampaignRecord).filter_by(id=encounter.campaign_id).first()
                if campaign:
                    flash("Please join the campaign first to access this encounter.")
                    return redirect(url_for("campaigns.join_campaign", campaign_id=campaign.campaign_id))

            if current_campaign_player and current_campaign_player.character_id:
                # Use player's own character from their campaign membership
                char_record = session.query(CharacterRecord).filter_by(
                    id=current_campaign_player.character_id
                ).first()
                if char_record:
                    player_char = char_record.to_model()
                    player_char_db_id = char_record.id

        # Fall back to encounter's player character if no campaign character found
        if not player_char and encounter.player_character_id:
            char_record = session.query(CharacterRecord).filter_by(
                id=encounter.player_character_id
            ).first()
            if char_record:
                player_char = char_record.to_model()
                player_char_db_id = char_record.id

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

        # Get player's position - from campaign membership if available, otherwise from encounter
        from sta.mechanics.actions import get_actions_for_position

        # Check for pending position change - apply it if it's the player's turn
        pending_position = None
        if current_campaign_player and current_campaign_player.pending_position:
            pending_position = current_campaign_player.pending_position
            # Apply the pending position if it's the player's turn
            if encounter.current_turn == "player":
                current_campaign_player.position = current_campaign_player.pending_position
                current_campaign_player.pending_position = None
                session.commit()
                pending_position = None  # Clear since we applied it

        # Use campaign position if available (from earlier lookup), otherwise fall back to encounter's position
        player_campaign_position = None
        if current_campaign_player and current_campaign_player.position and current_campaign_player.position != "unassigned":
            player_campaign_position = current_campaign_player.position

        position_value = player_campaign_position if player_campaign_position else encounter.player_position
        position = Position(position_value)
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

        # Load tactical map data
        tactical_map_data = json.loads(encounter.tactical_map_json or "{}")
        if not tactical_map_data or "radius" not in tactical_map_data:
            tactical_map_data = {"radius": 3, "tiles": []}

        # Visibility helper functions
        VISIBILITY_BLOCKING_TERRAIN = ["dust_cloud", "dense_nebula"]

        def get_terrain_at_position(tactical_map, q, r):
            """Get terrain type at a hex position."""
            tiles = tactical_map.get("tiles", [])
            for tile in tiles:
                coord = tile.get("coord", {})
                if coord.get("q") == q and coord.get("r") == r:
                    return tile.get("terrain", "open")
            return "open"

        def get_detected_positions(effects):
            """Get positions that have been detected via Sensor Sweep."""
            detected = []
            for effect in effects:
                if hasattr(effect, 'detected_position') and effect.detected_position:
                    detected.append(effect.detected_position)
            return detected

        def is_enemy_visible(player_pos, enemy_pos, tactical_map, detected_positions):
            """Check if an enemy ship is visible to the player."""
            enemy_q = enemy_pos.get("q", 0)
            enemy_r = enemy_pos.get("r", 0)
            player_q = player_pos.get("q", 0)
            player_r = player_pos.get("r", 0)

            # Get terrain at enemy position
            enemy_terrain = get_terrain_at_position(tactical_map, enemy_q, enemy_r)

            # If enemy is not in visibility-blocked terrain, they're visible
            if enemy_terrain not in VISIBILITY_BLOCKING_TERRAIN:
                return True

            # Enemy is in visibility-blocked terrain
            # Check if player is in the same hex
            if player_q == enemy_q and player_r == enemy_r:
                return True

            # Check if position has been detected via Sensor Sweep
            for detected in detected_positions:
                if detected.get("q") == enemy_q and detected.get("r") == enemy_r:
                    return True

            return False

        # Load ship positions and build list with ship info
        ship_positions_data = json.loads(encounter.ship_positions_json or "{}")
        ship_positions = []

        # Player ship position
        player_pos = ship_positions_data.get("player", {"q": 0, "r": 0})
        if player_ship:
            ship_positions.append({
                "id": "player",
                "name": player_ship.name,
                "faction": "player",
                "position": player_pos
            })

        # Get detected positions for visibility filtering (only applies to player role)
        # GM and viewscreen see all ships
        detected_positions = get_detected_positions(active_effects) if role == "player" else []

        # Enemy ship positions (filter by visibility for player role)
        for i, enemy in enumerate(enemy_ships):
            enemy_pos = ship_positions_data.get(f"enemy_{i}", {"q": 2, "r": -1 + i})

            # For player role, only show visible enemies
            if role == "player" and not is_enemy_visible(player_pos, enemy_pos, tactical_map_data, detected_positions):
                continue  # Skip hidden enemy

            ship_positions.append({
                "id": f"enemy_{i}",
                "name": enemy.name,
                "faction": "enemy",
                "position": enemy_pos
            })

        # Calculate GM visibility variables (for fog-of-war on GM side)
        player_in_fog = False
        player_detected_by_enemy = False

        # Helper to calculate hex distance
        def hex_distance(q1, r1, q2, r2):
            return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2

        if player_ship:
            # Check if player ship is in visibility-blocking terrain
            player_terrain = get_terrain_at_position(tactical_map_data, player_pos.get("q", 0), player_pos.get("r", 0))
            player_in_fog = player_terrain in VISIBILITY_BLOCKING_TERRAIN

            player_q = player_pos.get("q", 0)
            player_r = player_pos.get("r", 0)

            # Check if any enemy ship is in the same hex as player (always visible)
            for i, enemy in enumerate(enemy_ships):
                enemy_pos_data = ship_positions_data.get(f"enemy_{i}", {"q": 2, "r": -1 + i})
                enemy_q = enemy_pos_data.get("q", 0)
                enemy_r = enemy_pos_data.get("r", 0)
                if hex_distance(player_q, player_r, enemy_q, enemy_r) == 0:
                    player_detected_by_enemy = True
                    break

            # Check if enemy has detected the player via Sensor Sweep effects
            if not player_detected_by_enemy:
                for effect in active_effects:
                    # Check for sensor sweep detection zones from enemy sources
                    if effect.detected_position and effect.source_ship and effect.source_ship.startswith("enemy_"):
                        # detected_position is the SCANNER's position
                        # Player is visible if within 1 hex of the scanner's position
                        scanner_pos = effect.detected_position
                        scanner_q = scanner_pos.get("q", 0)
                        scanner_r = scanner_pos.get("r", 0)
                        distance = hex_distance(player_q, player_r, scanner_q, scanner_r)
                        if distance <= 1:  # Same hex or adjacent
                            player_detected_by_enemy = True
                            break

        # Select template based on role
        if role == "viewscreen":
            template = "combat_viewscreen.html"
        elif role == "gm":
            template = "combat_gm.html"
        else:
            template = "combat_player_new.html"

        # Multi-player info for player view
        my_player_id = None
        my_player_name = None
        campaign_players = []
        is_multiplayer = False

        if encounter.campaign_id:
            from sta.database import CampaignPlayerRecord
            campaign_players_query = session.query(CampaignPlayerRecord).filter_by(
                campaign_id=encounter.campaign_id,
                is_active=True,
                is_gm=False
            ).all()

            is_multiplayer = len(campaign_players_query) > 1

            # Build player list for template
            players_turns_used = json.loads(encounter.players_turns_used_json or "{}")
            for cp in campaign_players_query:
                player_data = players_turns_used.get(str(cp.id), {})
                campaign_players.append({
                    "id": cp.id,
                    "name": cp.player_name,
                    "position": cp.position,
                    "has_acted": player_data.get("acted", False),
                    "is_current": encounter.current_player_id == cp.id,
                })

            # Get current player's info
            if current_campaign_player:
                my_player_id = current_campaign_player.id
                my_player_name = current_campaign_player.player_name

        # Get current claiming player's name
        current_player_name = None
        if encounter.current_player_id:
            for cp in campaign_players:
                if cp["id"] == encounter.current_player_id:
                    current_player_name = cp["name"]
                    break

        return render_template(
            template,
            encounter=encounter,
            campaign=campaign,
            player_char=player_char,
            player_char_db_id=player_char_db_id,
            player_ship=player_ship,
            player_ship_db_id=player_ship_db_id,
            enemy_ships=enemy_ships,
            enemy_ship_db_ids=enemy_ship_db_ids,
            position=position,
            actions=actions,
            active_effects=active_effects,
            resistance_bonus=resistance_bonus,
            role=role,
            tactical_map=tactical_map_data,
            ship_positions=ship_positions,
            # Multi-player info
            is_multiplayer=is_multiplayer,
            my_player_id=my_player_id,
            my_player_name=my_player_name,
            campaign_players=campaign_players,
            current_player_name=current_player_name,
            # GM visibility (fog-of-war)
            player_in_fog=player_in_fog,
            player_detected_by_enemy=player_detected_by_enemy,
            # Pending position change
            pending_position=pending_position,
        )
    finally:
        session.close()
