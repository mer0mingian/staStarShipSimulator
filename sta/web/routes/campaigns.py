"""Campaign routes for campaign management."""

import json
import uuid
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sta.database import (
    get_session, EncounterRecord, CharacterRecord, StarshipRecord,
    CampaignRecord, CampaignPlayerRecord, CampaignShipRecord
)
from sta.generators import generate_character, generate_starship
from sta.models.enums import Position
from sta.models.starship import Starship, Systems, Departments
from sta.models.character import Character, Attributes, Disciplines

campaigns_bp = Blueprint("campaigns", __name__)


# =============================================================================
# Role-Based Home Pages
# =============================================================================

@campaigns_bp.route("/player")
def player_home():
    """Player home - campaigns to join."""
    session = get_session()
    try:
        campaigns = session.query(CampaignRecord).filter_by(is_active=True).all()

        # Check if player has existing sessions
        session_token = request.cookies.get("sta_session_token")
        my_campaigns = []
        if session_token:
            my_memberships = session.query(CampaignPlayerRecord).filter_by(
                session_token=session_token,
                is_active=True
            ).all()
            my_campaign_ids = [m.campaign_id for m in my_memberships]
            my_campaigns = [c for c in campaigns if c.id in my_campaign_ids]

        return render_template(
            "player_home.html",
            campaigns=campaigns,
            my_campaigns=my_campaigns,
        )
    finally:
        session.close()


@campaigns_bp.route("/gm")
def gm_home():
    """GM home - campaigns to manage."""
    session = get_session()
    try:
        # Single-GM mode: all campaigns are accessible to the GM
        all_campaigns = session.query(CampaignRecord).filter_by(is_active=True).all()

        return render_template(
            "gm_home.html",
            my_campaigns=all_campaigns,
            other_campaigns=[],
        )
    finally:
        session.close()


@campaigns_bp.route("/")
def campaign_list():
    """Redirect to role selection."""
    return redirect(url_for("main.index"))


# =============================================================================
# Campaign CRUD
# =============================================================================


@campaigns_bp.route("/new", methods=["GET", "POST"])
def new_campaign():
    """Create a new campaign."""
    if request.method == "POST":
        session = get_session()
        try:
            name = request.form.get("name", "New Campaign")
            description = request.form.get("description", "")
            gm_name = request.form.get("gm_name", "Game Master")

            # Create campaign
            campaign = CampaignRecord(
                campaign_id=str(uuid.uuid4())[:8],  # Short ID for easy sharing
                name=name,
                description=description,
            )
            session.add(campaign)
            session.flush()

            # Create GM (called "Q" - no bridge position)
            gm_token = secrets.token_urlsafe(32)
            gm_player = CampaignPlayerRecord(
                campaign_id=campaign.id,
                player_name=gm_name,
                session_token=gm_token,
                is_gm=True,
                position="gm",  # GM has no bridge position
            )
            session.add(gm_player)
            session.commit()

            # Return token for GM to store in localStorage
            response = redirect(url_for("campaigns.campaign_dashboard", campaign_id=campaign.campaign_id))
            response.set_cookie("sta_session_token", gm_token, max_age=60*60*24*365)  # 1 year
            return response
        finally:
            session.close()

    # GET - show form
    return render_template("campaign_new.html")


@campaigns_bp.route("/<campaign_id>")
def campaign_dashboard(campaign_id: str):
    """Campaign dashboard - hub for players, ships, encounters."""
    # Check for role override (single-GM mode)
    role = request.args.get("role", "")

    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.campaign_list"))

        # Single-GM mode: if role=gm, skip membership checks
        if role == "gm":
            is_gm = True
            current_player = None
        else:
            # Get current user from session token
            session_token = request.cookies.get("sta_session_token")
            current_player = None
            is_gm = False
            if session_token:
                current_player = session.query(CampaignPlayerRecord).filter_by(
                    session_token=session_token,
                    campaign_id=campaign.id
                ).first()
                if current_player:
                    is_gm = current_player.is_gm

            # Route based on user's role:
            # - Not in campaign yet → join page
            # - Player (not GM) → player dashboard
            # - GM → full dashboard (continue below)
            if not current_player:
                return redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))
            if not is_gm:
                return redirect(url_for("campaigns.player_dashboard", campaign_id=campaign_id))

        # Load players with character data
        player_records = session.query(CampaignPlayerRecord).filter_by(
            campaign_id=campaign.id,
            is_active=True
        ).all()

        players = []
        for p in player_records:
            player_data = {
                "id": p.id,
                "player_name": p.player_name,
                "position": p.position,
                "is_gm": p.is_gm,
                "character_id": p.character_id,
                "character": None,
            }
            if p.character_id:
                char_record = session.query(CharacterRecord).filter_by(id=p.character_id).first()
                if char_record:
                    player_data["character"] = char_record.to_model()
            players.append(player_data)

        # Load ship pool
        campaign_ships = session.query(CampaignShipRecord).filter_by(
            campaign_id=campaign.id
        ).all()
        ships = []
        for cs in campaign_ships:
            ship_record = session.query(StarshipRecord).filter_by(id=cs.ship_id).first()
            if ship_record:
                ships.append({
                    "id": cs.id,
                    "ship_id": ship_record.id,
                    "name": ship_record.name,
                    "ship_class": ship_record.ship_class,
                    "is_active": campaign.active_ship_id == ship_record.id,
                    "is_available": cs.is_available,
                })

        # Load active ship details
        active_ship = None
        if campaign.active_ship_id:
            ship_record = session.query(StarshipRecord).filter_by(
                id=campaign.active_ship_id
            ).first()
            if ship_record:
                active_ship = ship_record.to_model()

        # Load encounters
        encounters = session.query(EncounterRecord).filter_by(
            campaign_id=campaign.id
        ).order_by(EncounterRecord.created_at.desc()).all()

        # Split encounters by status
        active_encounter = next((e for e in encounters if e.status == "active"), None)
        draft_encounters = [e for e in encounters if e.status == "draft"]
        completed_encounters = [e for e in encounters if e.status == "completed"]

        positions = [p.value for p in Position]

        return render_template(
            "campaign_dashboard.html",
            campaign=campaign,
            current_player=current_player,
            is_gm=is_gm,
            players=players,
            ships=ships,
            active_ship=active_ship,
            active_encounter=active_encounter,
            draft_encounters=draft_encounters,
            completed_encounters=completed_encounters,
            positions=positions,
        )
    finally:
        session.close()


@campaigns_bp.route("/<campaign_id>/join", methods=["GET", "POST"])
def join_campaign(campaign_id: str):
    """Join a campaign as a player - select an existing character."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.player_home"))

        # Check if already joined via cookie
        session_token = request.cookies.get("sta_session_token")
        if session_token:
            existing = session.query(CampaignPlayerRecord).filter_by(
                session_token=session_token,
                campaign_id=campaign.id
            ).first()
            if existing:
                return redirect(url_for("campaigns.player_dashboard", campaign_id=campaign_id))

        if request.method == "POST":
            player_id = request.form.get("player_id")

            if player_id:
                # Claim existing character
                player = session.query(CampaignPlayerRecord).filter_by(
                    id=int(player_id),
                    campaign_id=campaign.id,
                    is_gm=False
                ).first()

                if player:
                    # Generate new session token for this player
                    player_token = secrets.token_urlsafe(32)
                    player.session_token = player_token
                    session.commit()

                    response = redirect(url_for("campaigns.player_dashboard", campaign_id=campaign_id))
                    response.set_cookie("sta_session_token", player_token, max_age=60*60*24*365)
                    return response

            flash("Please select a character")
            return redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))

        # GET - show character selection
        # Get available characters (non-GM players with characters)
        available_players = session.query(CampaignPlayerRecord).filter_by(
            campaign_id=campaign.id,
            is_gm=False,
            is_active=True
        ).all()

        # Load character data for each player
        players_with_chars = []
        for p in available_players:
            char = None
            if p.character_id:
                char_record = session.query(CharacterRecord).filter_by(id=p.character_id).first()
                if char_record:
                    char = char_record.to_model()
            players_with_chars.append({
                "id": p.id,
                "player_name": p.player_name,
                "character": char,
            })

        return render_template(
            "campaign_join.html",
            campaign=campaign,
            players=players_with_chars,
        )
    finally:
        session.close()


@campaigns_bp.route("/<campaign_id>/player")
def player_dashboard(campaign_id: str):
    """Player-specific dashboard - shows their character and active encounter."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.player_home"))

        # Get current player from session token
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))

        current_player = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id
        ).first()

        if not current_player:
            return redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))

        # If this is the GM, redirect to the full dashboard
        if current_player.is_gm:
            return redirect(url_for("campaigns.campaign_dashboard", campaign_id=campaign_id))

        # Load character data
        character = None
        if current_player.character_id:
            char_record = session.query(CharacterRecord).filter_by(
                id=current_player.character_id
            ).first()
            if char_record:
                character = char_record.to_model()

        # Load active ship
        active_ship = None
        if campaign.active_ship_id:
            ship_record = session.query(StarshipRecord).filter_by(
                id=campaign.active_ship_id
            ).first()
            if ship_record:
                active_ship = ship_record.to_model()

        # Load active encounter
        active_encounter = session.query(EncounterRecord).filter_by(
            campaign_id=campaign.id,
            status="active"
        ).first()

        # Get positions for selection
        positions = [p.value for p in Position]

        return render_template(
            "player_dashboard.html",
            campaign=campaign,
            player=current_player,
            character=character,
            active_ship=active_ship,
            active_encounter=active_encounter,
            positions=positions,
        )
    finally:
        session.close()


@campaigns_bp.route("/<campaign_id>/switch-character")
def switch_character(campaign_id: str):
    """Clear player session to allow switching to a different character."""
    # Clear the session cookie for this campaign
    response = redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))
    response.delete_cookie("sta_session_token")
    return response


# =============================================================================
# Campaign API Endpoints
# =============================================================================

@campaigns_bp.route("/api/campaigns", methods=["GET"])
def api_list_campaigns():
    """API: List all active campaigns."""
    session = get_session()
    try:
        campaigns = session.query(CampaignRecord).filter_by(is_active=True).all()
        return jsonify([{
            "id": c.id,
            "campaign_id": c.campaign_id,
            "name": c.name,
            "description": c.description,
            "has_active_ship": c.active_ship_id is not None,
        } for c in campaigns])
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>", methods=["GET"])
def api_get_campaign(campaign_id: str):
    """API: Get campaign details."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        return jsonify({
            "id": campaign.id,
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "description": campaign.description,
            "active_ship_id": campaign.active_ship_id,
            "is_active": campaign.is_active,
        })
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>", methods=["PUT"])
def api_update_campaign(campaign_id: str):
    """API: Update campaign details."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        data = request.get_json()
        if "name" in data:
            campaign.name = data["name"]
        if "description" in data:
            campaign.description = data["description"]

        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>", methods=["DELETE"])
def api_delete_campaign(campaign_id: str):
    """API: Delete (deactivate) campaign."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        campaign.is_active = False
        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/generate-random", methods=["POST"])
def api_generate_random_campaign():
    """API: Generate a random campaign with ship and encounter ready to go."""
    from sta.generators.starship import generate_enemy_ship
    from sta.models.enums import CrewQuality

    session = get_session()
    try:
        # Generate random ship names
        ship_names = [
            "USS Enterprise", "USS Defiant", "USS Voyager", "USS Discovery",
            "USS Reliant", "USS Excelsior", "USS Prometheus", "USS Titan",
            "USS Cerritos", "USS Stargazer", "USS Hood", "USS Lexington"
        ]
        campaign_names = [
            "Shakedown Cruise", "Border Patrol", "Deep Space Exploration",
            "First Contact Mission", "Diplomatic Escort", "Scientific Survey",
            "Emergency Response", "Tactical Exercise", "Sector Defense"
        ]

        import random
        campaign_name = random.choice(campaign_names)

        # Create campaign
        campaign = CampaignRecord(
            campaign_id=str(uuid.uuid4())[:8],
            name=campaign_name,
            description="Quick-start campaign with ship and encounter ready",
        )
        session.add(campaign)
        session.flush()

        # Generate GM token (GM is called "Q")
        gm_token = secrets.token_urlsafe(32)
        gm_player = CampaignPlayerRecord(
            campaign_id=campaign.id,
            player_name="Q",
            session_token=gm_token,
            is_gm=True,
            position="gm",  # GM has no bridge position
        )
        session.add(gm_player)

        # Generate a player ship
        ship = generate_starship()
        ship_record = StarshipRecord.from_model(ship)
        session.add(ship_record)
        session.flush()

        # Add ship to campaign pool and set as active
        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship_record.id,
        )
        session.add(campaign_ship)
        campaign.active_ship_id = ship_record.id

        # Generate a character for the GM to use
        char = generate_character()
        char_record = CharacterRecord.from_model(char)
        session.add(char_record)
        session.flush()

        # Generate enemy ship
        enemy = generate_enemy_ship(difficulty="standard", crew_quality=CrewQuality.TALENTED)
        enemy_record = StarshipRecord.from_model(enemy)
        session.add(enemy_record)
        session.flush()

        # Create a draft encounter
        encounter = EncounterRecord(
            encounter_id=str(uuid.uuid4()),
            name="First Engagement",
            campaign_id=campaign.id,
            status="draft",
            player_character_id=char_record.id,
            player_ship_id=ship_record.id,
            player_position="captain",
            enemy_ship_ids_json=f"[{enemy_record.id}]",
            threat=2,
        )
        session.add(encounter)
        session.commit()

        # Set cookie for GM token
        response = jsonify({
            "success": True,
            "campaign_id": campaign.campaign_id,
            "campaign_name": campaign_name,
            "ship_name": ship.name,
        })
        response.set_cookie("sta_session_token", gm_token, max_age=60*60*24*365)
        return response

    finally:
        session.close()


# =============================================================================
# Player Management API
# =============================================================================

@campaigns_bp.route("/api/campaign/<campaign_id>/players", methods=["GET", "POST"])
def api_list_players(campaign_id: str):
    """API: List players in campaign or create a new player."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        if request.method == "GET":
            players = session.query(CampaignPlayerRecord).filter_by(
                campaign_id=campaign.id,
                is_active=True
            ).all()

            return jsonify([{
                "id": p.id,
                "player_name": p.player_name,
                "position": p.position,
                "is_gm": p.is_gm,
                "character_id": p.character_id,
            } for p in players])

        # POST - Create new player
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        gm = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id,
            is_gm=True
        ).first()

        if not gm:
            return jsonify({"error": "Only GM can create players"}), 403

        data = request.get_json()
        action = data.get("action", "generate")

        character_id = None
        player_name = data.get("name", "New Player")

        if action == "generate":
            # Generate random character
            char = generate_character()
            char_record = CharacterRecord.from_model(char)
            session.add(char_record)
            session.flush()
            character_id = char_record.id
            player_name = char.name
        elif action == "create":
            # Create bespoke character from provided data
            attrs_data = data.get("attributes", {})
            discs_data = data.get("disciplines", {})

            char = Character(
                name=data.get("name", "New Character"),
                rank=data.get("rank"),
                species=data.get("species"),
                role=data.get("role"),
                attributes=Attributes(
                    control=attrs_data.get("control", 9),
                    daring=attrs_data.get("daring", 9),
                    fitness=attrs_data.get("fitness", 9),
                    insight=attrs_data.get("insight", 9),
                    presence=attrs_data.get("presence", 9),
                    reason=attrs_data.get("reason", 9),
                ),
                disciplines=Disciplines(
                    command=discs_data.get("command", 2),
                    conn=discs_data.get("conn", 2),
                    engineering=discs_data.get("engineering", 2),
                    medicine=discs_data.get("medicine", 2),
                    science=discs_data.get("science", 2),
                    security=discs_data.get("security", 2),
                ),
            )
            char_record = CharacterRecord.from_model(char)
            session.add(char_record)
            session.flush()
            character_id = char_record.id
            player_name = char.name

        # Create new player record (no position - players choose their own)
        new_player = CampaignPlayerRecord(
            campaign_id=campaign.id,
            character_id=character_id,
            player_name=player_name,
            session_token=str(uuid.uuid4()),  # Placeholder token until they join
            position="unassigned",  # Players will choose their position
            is_gm=False,
            is_active=True,
        )
        session.add(new_player)
        session.commit()

        return jsonify({
            "success": True,
            "player": {
                "id": new_player.id,
                "player_name": new_player.player_name,
                "character_id": new_player.character_id,
            }
        })
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/player/<int:player_id>/position", methods=["PUT"])
def api_update_player_position(campaign_id: str, player_id: int):
    """API: Update player's bridge position (player can update their own)."""
    session = get_session()
    try:
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        # Get current user
        current_user = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id
        ).first()

        if not current_user:
            return jsonify({"error": "Not authenticated"}), 401

        # Players can only update their own position (or GM can update any)
        if not current_user.is_gm and current_user.id != player_id:
            return jsonify({"error": "Can only update your own position"}), 403

        # Check if there's an active encounter - if so, position is locked
        active_encounter = session.query(EncounterRecord).filter_by(
            campaign_id=campaign.id,
            status="active"
        ).first()

        if active_encounter and not current_user.is_gm:
            return jsonify({"error": "Position locked during combat. Use Change Position action in combat."}), 403

        # Update player position
        player = session.query(CampaignPlayerRecord).filter_by(
            id=player_id,
            campaign_id=campaign.id
        ).first()

        if not player:
            return jsonify({"error": "Player not found"}), 404

        data = request.get_json()
        player.position = data.get("position", player.position)
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/player/<int:player_id>", methods=["DELETE"])
def api_remove_player(campaign_id: str, player_id: int):
    """API: Remove player from campaign (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id,
            is_gm=True
        ).first()

        if not gm:
            return jsonify({"error": "Only GM can remove players"}), 403

        # Remove player (soft delete)
        player = session.query(CampaignPlayerRecord).filter_by(
            id=player_id,
            campaign_id=campaign.id
        ).first()

        if not player:
            return jsonify({"error": "Player not found"}), 404

        if player.is_gm:
            return jsonify({"error": "Cannot remove GM"}), 400

        player.is_active = False
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/player/<int:player_id>", methods=["GET"])
def api_get_player(campaign_id: str, player_id: int):
    """API: Get player details with character data."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        player = session.query(CampaignPlayerRecord).filter_by(
            id=player_id,
            campaign_id=campaign.id
        ).first()

        if not player:
            return jsonify({"error": "Player not found"}), 404

        # Load character data
        character_data = None
        if player.character_id:
            char_record = session.query(CharacterRecord).filter_by(
                id=player.character_id
            ).first()
            if char_record:
                char = char_record.to_model()
                character_data = {
                    "name": char.name,
                    "rank": char.rank,
                    "species": char.species,
                    "role": char.role,
                    "attributes": {
                        "control": char.attributes.control,
                        "daring": char.attributes.daring,
                        "fitness": char.attributes.fitness,
                        "insight": char.attributes.insight,
                        "presence": char.attributes.presence,
                        "reason": char.attributes.reason,
                    },
                    "disciplines": {
                        "command": char.disciplines.command,
                        "conn": char.disciplines.conn,
                        "engineering": char.disciplines.engineering,
                        "medicine": char.disciplines.medicine,
                        "science": char.disciplines.science,
                        "security": char.disciplines.security,
                    }
                }

        return jsonify({
            "id": player.id,
            "player_name": player.player_name,
            "position": player.position,
            "is_gm": player.is_gm,
            "character_id": player.character_id,
            "character": character_data,
        })
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/player/<int:player_id>", methods=["PUT"])
def api_update_player(campaign_id: str, player_id: int):
    """API: Update player and character data (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id,
            is_gm=True
        ).first()

        if not gm:
            return jsonify({"error": "Only GM can update players"}), 403

        player = session.query(CampaignPlayerRecord).filter_by(
            id=player_id,
            campaign_id=campaign.id
        ).first()

        if not player:
            return jsonify({"error": "Player not found"}), 404

        data = request.get_json()

        # Update player name
        if "name" in data:
            player.player_name = data["name"]

        # Update character data
        if player.character_id:
            char_record = session.query(CharacterRecord).filter_by(
                id=player.character_id
            ).first()
            if char_record:
                # Update character fields directly on record
                char_record.name = data.get("name", char_record.name)
                char_record.rank = data.get("rank", char_record.rank)
                char_record.species = data.get("species", char_record.species)
                char_record.role = data.get("role", char_record.role)

                # Update attributes JSON
                if "attributes" in data:
                    current_attrs = json.loads(char_record.attributes_json)
                    current_attrs.update(data["attributes"])
                    char_record.attributes_json = json.dumps(current_attrs)

                # Update disciplines JSON
                if "disciplines" in data:
                    current_discs = json.loads(char_record.disciplines_json)
                    current_discs.update(data["disciplines"])
                    char_record.disciplines_json = json.dumps(current_discs)

        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


# =============================================================================
# Ship Pool Management API
# =============================================================================

@campaigns_bp.route("/api/campaign/<campaign_id>/ships", methods=["GET"])
def api_list_ships(campaign_id: str):
    """API: List ships in campaign pool."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        campaign_ships = session.query(CampaignShipRecord).filter_by(
            campaign_id=campaign.id
        ).all()

        ships = []
        for cs in campaign_ships:
            ship_record = session.query(StarshipRecord).filter_by(id=cs.ship_id).first()
            if ship_record:
                ships.append({
                    "id": cs.id,
                    "ship_id": ship_record.id,
                    "name": ship_record.name,
                    "ship_class": ship_record.ship_class,
                    "is_active": campaign.active_ship_id == ship_record.id,
                    "is_available": cs.is_available,
                })

        return jsonify(ships)
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/ships", methods=["POST"])
def api_add_ship(campaign_id: str):
    """API: Add ship to campaign pool (GM only)."""
    from sta.models.starship import Starship, Systems, Departments

    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id,
            is_gm=True
        ).first()

        if not gm:
            return jsonify({"error": "Only GM can add ships"}), 403

        data = request.get_json()
        action = data.get("action", "generate")

        if action == "generate":
            # Generate new ship
            ship = generate_starship()
            ship_record = StarshipRecord.from_model(ship)
            session.add(ship_record)
            session.flush()
            ship_id = ship_record.id
        elif action == "create":
            # Create bespoke ship from provided data
            systems_data = data.get("systems", {})
            departments_data = data.get("departments", {})
            scale = data.get("scale", 4)

            ship = Starship(
                name=data.get("name", "New Ship"),
                ship_class=data.get("ship_class", "Unknown"),
                registry=data.get("registry"),
                scale=scale,
                systems=Systems(
                    comms=systems_data.get("comms", 9),
                    computers=systems_data.get("computers", 9),
                    engines=systems_data.get("engines", 9),
                    sensors=systems_data.get("sensors", 9),
                    structure=systems_data.get("structure", 9),
                    weapons=systems_data.get("weapons", 9),
                ),
                departments=Departments(
                    command=departments_data.get("command", 2),
                    conn=departments_data.get("conn", 2),
                    engineering=departments_data.get("engineering", 2),
                    medicine=departments_data.get("medicine", 2),
                    science=departments_data.get("science", 2),
                    security=departments_data.get("security", 2),
                ),
                weapons=[],  # Add default weapons based on scale
                talents=[],
                traits=[],
            )
            # Calculate shields based on structure + security
            ship.shields_max = ship.systems.structure + ship.departments.security
            ship.shields = ship.shields_max
            ship.resistance = scale

            ship_record = StarshipRecord.from_model(ship)
            session.add(ship_record)
            session.flush()
            ship_id = ship_record.id
        else:
            # Use existing ship
            ship_id = data.get("ship_id")
            if not ship_id:
                return jsonify({"error": "ship_id required"}), 400

        # Add to campaign pool
        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship_id,
        )
        session.add(campaign_ship)

        # If this is the first ship, set as active
        if not campaign.active_ship_id:
            campaign.active_ship_id = ship_id

        session.commit()

        return jsonify({
            "success": True,
            "ship_id": ship_id,
            "campaign_ship_id": campaign_ship.id,
        })
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/active-ship", methods=["PUT"])
def api_set_active_ship(campaign_id: str):
    """API: Set active ship for campaign (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id,
            is_gm=True
        ).first()

        if not gm:
            return jsonify({"error": "Only GM can set active ship"}), 403

        data = request.get_json()
        ship_id = data.get("ship_id")

        # Verify ship is in campaign pool
        campaign_ship = session.query(CampaignShipRecord).filter_by(
            campaign_id=campaign.id,
            ship_id=ship_id
        ).first()

        if not campaign_ship:
            return jsonify({"error": "Ship not in campaign pool"}), 400

        campaign.active_ship_id = ship_id
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/ships/<int:campaign_ship_id>", methods=["DELETE"])
def api_remove_ship(campaign_id: str, campaign_ship_id: int):
    """API: Remove ship from campaign pool (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id,
            is_gm=True
        ).first()

        if not gm:
            return jsonify({"error": "Only GM can remove ships"}), 403

        campaign_ship = session.query(CampaignShipRecord).filter_by(
            id=campaign_ship_id,
            campaign_id=campaign.id
        ).first()

        if not campaign_ship:
            return jsonify({"error": "Ship not found in campaign"}), 404

        # If this is the active ship, unset it
        if campaign.active_ship_id == campaign_ship.ship_id:
            campaign.active_ship_id = None

        session.delete(campaign_ship)
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


# =============================================================================
# Encounter Lifecycle API
# =============================================================================

@campaigns_bp.route("/api/campaign/<campaign_id>/encounters", methods=["GET"])
def api_list_encounters(campaign_id: str):
    """API: List encounters in campaign."""
    session = get_session()
    try:
        campaign = session.query(CampaignRecord).filter_by(
            campaign_id=campaign_id
        ).first()

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        status_filter = request.args.get("status")  # Optional filter

        query = session.query(EncounterRecord).filter_by(campaign_id=campaign.id)
        if status_filter:
            query = query.filter_by(status=status_filter)

        encounters = query.order_by(EncounterRecord.created_at.desc()).all()

        return jsonify([{
            "id": e.id,
            "encounter_id": e.encounter_id,
            "name": e.name,
            "status": e.status,
            "round": e.round,
            "momentum": e.momentum,
            "threat": e.threat,
        } for e in encounters])
    finally:
        session.close()


@campaigns_bp.route("/api/encounter/<encounter_id>/status", methods=["PUT"])
def api_update_encounter_status(encounter_id: str):
    """API: Update encounter status (GM only)."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        if not encounter.campaign_id:
            return jsonify({"error": "Encounter not part of a campaign"}), 400

        campaign = session.query(CampaignRecord).filter_by(
            id=encounter.campaign_id
        ).first()

        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        gm = session.query(CampaignPlayerRecord).filter_by(
            session_token=session_token,
            campaign_id=campaign.id,
            is_gm=True
        ).first()

        if not gm:
            return jsonify({"error": "Only GM can change encounter status"}), 403

        data = request.get_json()
        new_status = data.get("status")

        if new_status not in ("draft", "active", "completed"):
            return jsonify({"error": "Invalid status"}), 400

        # Enforce single active encounter
        if new_status == "active":
            existing_active = session.query(EncounterRecord).filter(
                EncounterRecord.campaign_id == campaign.id,
                EncounterRecord.status == "active",
                EncounterRecord.id != encounter.id
            ).first()

            if existing_active:
                return jsonify({
                    "error": "Campaign already has an active encounter. Complete it first."
                }), 400

        encounter.status = new_status
        session.commit()

        return jsonify({"success": True, "status": new_status})
    finally:
        session.close()


@campaigns_bp.route("/api/ship/<int:ship_id>", methods=["GET"])
def api_get_ship(ship_id: int):
    """API: Get ship details."""
    session = get_session()
    try:
        ship_record = session.query(StarshipRecord).filter_by(id=ship_id).first()

        if not ship_record:
            return jsonify({"error": "Ship not found"}), 404

        ship = ship_record.to_model()
        return jsonify({
            "id": ship_record.id,
            "name": ship.name,
            "ship_class": ship.ship_class,
            "registry": ship.registry,
            "scale": ship.scale,
            "systems": {
                "comms": ship.systems.comms,
                "computers": ship.systems.computers,
                "engines": ship.systems.engines,
                "sensors": ship.systems.sensors,
                "structure": ship.systems.structure,
                "weapons": ship.systems.weapons,
            },
            "departments": {
                "command": ship.departments.command,
                "conn": ship.departments.conn,
                "engineering": ship.departments.engineering,
                "medicine": ship.departments.medicine,
                "science": ship.departments.science,
                "security": ship.departments.security,
            }
        })
    finally:
        session.close()


@campaigns_bp.route("/api/ship/<int:ship_id>", methods=["PUT"])
def api_update_ship(ship_id: int):
    """API: Update ship details (GM only)."""
    session = get_session()
    try:
        ship_record = session.query(StarshipRecord).filter_by(id=ship_id).first()

        if not ship_record:
            return jsonify({"error": "Ship not found"}), 404

        data = request.get_json()

        # Update basic fields
        if "name" in data:
            ship_record.name = data["name"]
        if "ship_class" in data:
            ship_record.ship_class = data["ship_class"]
        if "registry" in data:
            ship_record.registry = data["registry"]
        if "scale" in data:
            ship_record.scale = data["scale"]

        # Update systems JSON
        if "systems" in data:
            current_systems = json.loads(ship_record.systems_json)
            current_systems.update(data["systems"])
            ship_record.systems_json = json.dumps(current_systems)

        # Update departments JSON
        if "departments" in data:
            current_depts = json.loads(ship_record.departments_json)
            current_depts.update(data["departments"])
            ship_record.departments_json = json.dumps(current_depts)

        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/encounter/<encounter_id>", methods=["GET"])
def api_get_encounter(encounter_id: str):
    """API: Get encounter details."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        return jsonify({
            "encounter_id": encounter.encounter_id,
            "name": encounter.name,
            "description": encounter.description,
            "status": encounter.status,
            "round": encounter.round,
            "threat": encounter.threat,
        })
    finally:
        session.close()


@campaigns_bp.route("/api/encounter/<encounter_id>", methods=["PUT"])
def api_update_encounter(encounter_id: str):
    """API: Update encounter details (GM only)."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        data = request.get_json()

        # Update fields
        if "name" in data:
            encounter.name = data["name"]
        if "description" in data:
            encounter.description = data["description"] if data["description"] else None
        if "threat" in data:
            encounter.threat = data["threat"]

        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/encounter/<encounter_id>", methods=["DELETE"])
def api_delete_encounter(encounter_id: str):
    """API: Delete encounter (GM only)."""
    session = get_session()
    try:
        encounter = session.query(EncounterRecord).filter_by(
            encounter_id=encounter_id
        ).first()

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        # Completed encounters cannot be deleted (historical record)
        if encounter.status == "completed":
            return jsonify({"error": "Cannot delete completed encounters"}), 400

        session.delete(encounter)
        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()
