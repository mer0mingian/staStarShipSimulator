"""Campaign routes for campaign management."""

import json
import uuid
import secrets
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    make_response,
)
from werkzeug.security import generate_password_hash, check_password_hash

# Default GM password
DEFAULT_GM_PASSWORD = "ENGAGE1"
from sta.database import (
    get_session,
    EncounterRecord,
    CharacterRecord,
    StarshipRecord,
    CampaignRecord,
    CampaignPlayerRecord,
    CampaignShipRecord,
    CampaignNPCRecord,
    SceneRecord,
    NPCRecord,
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
            my_memberships = (
                session.query(CampaignPlayerRecord)
                .filter_by(session_token=session_token, is_active=True)
                .all()
            )
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
                gm_password_hash=generate_password_hash(DEFAULT_GM_PASSWORD),
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
            response = redirect(
                url_for(
                    "campaigns.campaign_dashboard", campaign_id=campaign.campaign_id
                )
            )
            response.set_cookie(
                "sta_session_token", gm_token, max_age=60 * 60 * 24 * 365
            )  # 1 year
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
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.campaign_list"))

        # Check if user wants GM access via ?role=gm
        gm_token_to_set = None
        if role == "gm":
            # Check if they already have a valid GM session
            session_token = request.cookies.get("sta_session_token")
            gm_player = (
                session.query(CampaignPlayerRecord)
                .filter_by(campaign_id=campaign.id, is_gm=True)
                .first()
            )

            if gm_player and session_token == gm_player.session_token:
                # Already authenticated as GM
                is_gm = True
                current_player = gm_player
            else:
                # Redirect to GM login page
                return redirect(url_for("campaigns.gm_login", campaign_id=campaign_id))
        else:
            # Get current user from session token
            session_token = request.cookies.get("sta_session_token")
            current_player = None
            is_gm = False
            if session_token:
                current_player = (
                    session.query(CampaignPlayerRecord)
                    .filter_by(session_token=session_token, campaign_id=campaign.id)
                    .first()
                )
                if current_player:
                    is_gm = current_player.is_gm

            # Route based on user's role:
            # - Not in campaign yet → join page
            # - Player (not GM) → player dashboard
            # - GM → full dashboard (continue below)
            if not current_player:
                return redirect(
                    url_for("campaigns.join_campaign", campaign_id=campaign_id)
                )
            if not is_gm:
                return redirect(
                    url_for("campaigns.player_dashboard", campaign_id=campaign_id)
                )

        # Load players with character data
        player_records = (
            session.query(CampaignPlayerRecord)
            .filter_by(campaign_id=campaign.id, is_active=True)
            .all()
        )

        players = []
        for p in player_records:
            player_data = {
                "id": p.id,
                "player_name": p.player_name,
                "position": p.position,
                "is_gm": p.is_gm,
                "character_id": p.character_id,
                "character": None,
                "is_claimed": not p.session_token.startswith("unclaimed_"),
            }
            if p.character_id:
                char_record = (
                    session.query(CharacterRecord).filter_by(id=p.character_id).first()
                )
                if char_record:
                    player_data["character"] = char_record.to_model()
            players.append(player_data)

        # Load ship pool
        campaign_ships = (
            session.query(CampaignShipRecord).filter_by(campaign_id=campaign.id).all()
        )
        ships = []
        for cs in campaign_ships:
            ship_record = session.query(StarshipRecord).filter_by(id=cs.ship_id).first()
            if ship_record:
                ships.append(
                    {
                        "id": cs.id,
                        "ship_id": ship_record.id,
                        "name": ship_record.name,
                        "ship_class": ship_record.ship_class,
                        "registry": ship_record.ship_registry or "N/A",
                        "scale": ship_record.scale,
                        "is_enemy": ship_record.crew_quality is not None,
                        "is_active": campaign.active_ship_id == ship_record.id,
                        "is_available": cs.is_available,
                    }
                )

        # Load active ship details
        active_ship = None
        if campaign.active_ship_id:
            ship_record = (
                session.query(StarshipRecord)
                .filter_by(id=campaign.active_ship_id)
                .first()
            )
            if ship_record:
                active_ship = ship_record.to_model()

        # Load encounters
        encounters = (
            session.query(EncounterRecord)
            .filter_by(campaign_id=campaign.id)
            .order_by(EncounterRecord.created_at.desc())
            .all()
        )

        # Split encounters by status
        active_encounter = next((e for e in encounters if e.status == "active"), None)
        draft_encounters = [e for e in encounters if e.status == "draft"]
        completed_encounters = [e for e in encounters if e.status == "completed"]

        # Load scenes (non-encounter scenes)
        scenes = (
            session.query(SceneRecord)
            .filter_by(campaign_id=campaign.id, encounter_id=None)
            .order_by(SceneRecord.created_at.desc())
            .all()
        )
        draft_scenes = [s for s in scenes if s.status == "draft"]
        active_scene = next((s for s in scenes if s.status == "active"), None)

        # Parse active scene data for template
        active_scene_data = None
        if active_scene:
            active_scene_data = {
                "id": active_scene.id,
                "name": active_scene.name,
                "scene_type": active_scene.scene_type,
                "status": active_scene.status,
                "stardate": active_scene.stardate,
                "scene_traits": json.loads(active_scene.scene_traits_json or "[]"),
            }

        positions = [p.value for p in Position]

        response = make_response(
            render_template(
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
                draft_scenes=draft_scenes,
                active_scene=active_scene,
                active_scene_data=active_scene_data,
                positions=positions,
            )
        )

        # Set GM cookie if accessing via ?role=gm
        if gm_token_to_set:
            response.set_cookie(
                "sta_session_token", gm_token_to_set, max_age=60 * 60 * 24 * 365
            )

        return response
    finally:
        session.close()


@campaigns_bp.route("/<campaign_id>/gm-login", methods=["GET", "POST"])
def gm_login(campaign_id: str):
    """GM login page - requires password to access GM controls."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.campaign_list"))

        error = None

        if request.method == "POST":
            password = request.form.get("password", "")

            # Check password - use default if no hash stored (legacy campaigns)
            password_hash = campaign.gm_password_hash
            if not password_hash:
                # Legacy campaign without password - set default and check
                password_hash = generate_password_hash(DEFAULT_GM_PASSWORD)
                campaign.gm_password_hash = password_hash
                session.commit()

            if check_password_hash(password_hash, password):
                # Password correct - find/create GM player and set cookie
                gm_player = (
                    session.query(CampaignPlayerRecord)
                    .filter_by(campaign_id=campaign.id, is_gm=True)
                    .first()
                )

                if gm_player:
                    response = redirect(
                        url_for("campaigns.campaign_dashboard", campaign_id=campaign_id)
                    )
                    response.set_cookie(
                        "sta_session_token",
                        gm_player.session_token,
                        max_age=60 * 60 * 24 * 365,
                    )
                    return response
                else:
                    # No GM player exists (shouldn't happen, but handle it)
                    error = "GM account not found for this campaign"
            else:
                error = "Incorrect password"

        return render_template("gm_login.html", campaign=campaign, error=error)
    finally:
        session.close()


@campaigns_bp.route("/<campaign_id>/join", methods=["GET", "POST"])
def join_campaign(campaign_id: str):
    """Join a campaign as a player - select an existing character."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.player_home"))

        # Check if already joined via cookie
        session_token = request.cookies.get("sta_session_token")
        if session_token:
            existing = (
                session.query(CampaignPlayerRecord)
                .filter_by(session_token=session_token, campaign_id=campaign.id)
                .first()
            )
            if existing:
                return redirect(
                    url_for("campaigns.player_dashboard", campaign_id=campaign_id)
                )

        if request.method == "POST":
            player_id = request.form.get("player_id")

            if player_id:
                # Claim existing character
                player = (
                    session.query(CampaignPlayerRecord)
                    .filter_by(id=int(player_id), campaign_id=campaign.id, is_gm=False)
                    .first()
                )

                if player:
                    # Check if already claimed by another player (unclaimed tokens start with "unclaimed_")
                    if not player.session_token.startswith("unclaimed_"):
                        flash(
                            "This character has already been claimed by another player"
                        )
                        return redirect(
                            url_for("campaigns.join_campaign", campaign_id=campaign_id)
                        )

                    # Generate new session token for this player
                    player_token = secrets.token_urlsafe(32)
                    player.session_token = player_token
                    session.commit()

                    response = redirect(
                        url_for("campaigns.player_dashboard", campaign_id=campaign_id)
                    )
                    response.set_cookie(
                        "sta_session_token", player_token, max_age=60 * 60 * 24 * 365
                    )
                    return response

            flash("Please select a character")
            return redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))

        # GET - show character selection
        # Get available characters (non-GM players that haven't been claimed yet)
        # Unclaimed players have tokens starting with "unclaimed_"
        available_players = (
            session.query(CampaignPlayerRecord)
            .filter(
                CampaignPlayerRecord.campaign_id == campaign.id,
                CampaignPlayerRecord.is_gm == False,
                CampaignPlayerRecord.is_active == True,
                CampaignPlayerRecord.session_token.like("unclaimed_%"),
            )
            .all()
        )

        # Load character data for each player
        players_with_chars = []
        for p in available_players:
            char = None
            if p.character_id:
                char_record = (
                    session.query(CharacterRecord).filter_by(id=p.character_id).first()
                )
                if char_record:
                    char = char_record.to_model()
            players_with_chars.append(
                {
                    "id": p.id,
                    "player_name": p.player_name,
                    "character": char,
                }
            )

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
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("campaigns.player_home"))

        # Get current player from session token
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))

        current_player = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id)
            .first()
        )

        if not current_player:
            return redirect(url_for("campaigns.join_campaign", campaign_id=campaign_id))

        # If this is the GM, redirect to the full dashboard
        if current_player.is_gm:
            return redirect(
                url_for("campaigns.campaign_dashboard", campaign_id=campaign_id)
            )

        # Load character data
        character = None
        if current_player.character_id:
            char_record = (
                session.query(CharacterRecord)
                .filter_by(id=current_player.character_id)
                .first()
            )
            if char_record:
                character = char_record.to_model()

        # Load active ship
        active_ship = None
        if campaign.active_ship_id:
            ship_record = (
                session.query(StarshipRecord)
                .filter_by(id=campaign.active_ship_id)
                .first()
            )
            if ship_record:
                active_ship = ship_record.to_model()

        # Load active encounter
        active_encounter = (
            session.query(EncounterRecord)
            .filter_by(campaign_id=campaign.id, status="active")
            .first()
        )

        # Get positions for selection with info about which are taken
        positions = [p.value for p in Position]

        # Get which positions are taken by other players
        taken_positions = {}
        other_players = (
            session.query(CampaignPlayerRecord)
            .filter(
                CampaignPlayerRecord.campaign_id == campaign.id,
                CampaignPlayerRecord.id != current_player.id,
                CampaignPlayerRecord.is_active == True,
                CampaignPlayerRecord.is_gm == False,
                CampaignPlayerRecord.position.isnot(None),
            )
            .all()
        )
        for other_player in other_players:
            if other_player.position and other_player.position not in [
                "gm",
                "unassigned",
            ]:
                taken_positions[other_player.position] = other_player.player_name

        return render_template(
            "player_dashboard.html",
            campaign=campaign,
            player=current_player,
            character=character,
            active_ship=active_ship,
            active_encounter=active_encounter,
            positions=positions,
            taken_positions=taken_positions,
        )
    finally:
        session.close()


@campaigns_bp.route("/<campaign_id>/switch-character")
def switch_character(campaign_id: str):
    """Clear player session to allow switching to a different character."""
    session = get_session()
    try:
        # Get current player from session token and release them
        session_token = request.cookies.get("sta_session_token")
        if session_token:
            campaign = (
                session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
            )
            if campaign:
                player = (
                    session.query(CampaignPlayerRecord)
                    .filter_by(
                        session_token=session_token,
                        campaign_id=campaign.id,
                        is_gm=False,
                    )
                    .first()
                )
                if player:
                    # Release the character by setting back to unclaimed token
                    player.session_token = f"unclaimed_{uuid.uuid4()}"
                    session.commit()
    finally:
        session.close()

    # Clear the session cookie
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
        return jsonify(
            [
                {
                    "id": c.id,
                    "campaign_id": c.campaign_id,
                    "name": c.name,
                    "description": c.description,
                    "has_active_ship": c.active_ship_id is not None,
                }
                for c in campaigns
            ]
        )
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>", methods=["GET"])
def api_get_campaign(campaign_id: str):
    """API: Get campaign details."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        return jsonify(
            {
                "id": campaign.id,
                "campaign_id": campaign.campaign_id,
                "name": campaign.name,
                "description": campaign.description,
                "active_ship_id": campaign.active_ship_id,
                "is_active": campaign.is_active,
            }
        )
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>", methods=["PUT"])
def api_update_campaign(campaign_id: str):
    """API: Update campaign details."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        data = request.get_json()
        if "name" in data:
            campaign.name = data["name"]
        if "description" in data:
            campaign.description = data["description"]

        # Combat settings (GM-only)
        if "enemy_turn_multiplier" in data:
            # Verify GM authentication for combat settings
            session_token = request.cookies.get("sta_session_token")
            if not session_token:
                return jsonify({"error": "Not authenticated"}), 401

            gm = (
                session.query(CampaignPlayerRecord)
                .filter_by(
                    session_token=session_token, campaign_id=campaign.id, is_gm=True
                )
                .first()
            )

            if not gm:
                return jsonify({"error": "Only the GM can change combat settings"}), 403

            multiplier = float(data["enemy_turn_multiplier"])
            # Validate range (0.1 to 2.0)
            if multiplier < 0.1 or multiplier > 2.0:
                return jsonify(
                    {"error": "Turn multiplier must be between 0.1 and 2.0"}
                ), 400
            campaign.enemy_turn_multiplier = multiplier

        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>", methods=["DELETE"])
def api_delete_campaign(campaign_id: str):
    """API: Delete (deactivate) campaign. Requires GM authentication."""
    session = get_session()
    try:
        # Verify GM authentication
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        # Verify the user is the GM of this campaign
        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only the GM can delete campaigns"}), 403

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
            "USS Enterprise",
            "USS Defiant",
            "USS Voyager",
            "USS Discovery",
            "USS Reliant",
            "USS Excelsior",
            "USS Prometheus",
            "USS Titan",
            "USS Cerritos",
            "USS Stargazer",
            "USS Hood",
            "USS Lexington",
        ]
        campaign_names = [
            "Shakedown Cruise",
            "Border Patrol",
            "Deep Space Exploration",
            "First Contact Mission",
            "Diplomatic Escort",
            "Scientific Survey",
            "Emergency Response",
            "Tactical Exercise",
            "Sector Defense",
        ]

        import random

        campaign_name = random.choice(campaign_names)

        # Create campaign
        campaign = CampaignRecord(
            campaign_id=str(uuid.uuid4())[:8],
            name=campaign_name,
            description="Quick-start campaign with ship and encounter ready",
            gm_password_hash=generate_password_hash(DEFAULT_GM_PASSWORD),
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
        enemy = generate_enemy_ship(
            difficulty="standard", crew_quality=CrewQuality.TALENTED
        )
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
        response = jsonify(
            {
                "success": True,
                "campaign_id": campaign.campaign_id,
                "campaign_name": campaign_name,
                "ship_name": ship.name,
            }
        )
        response.set_cookie("sta_session_token", gm_token, max_age=60 * 60 * 24 * 365)
        return response

    finally:
        session.close()


# =============================================================================
# Player Management API
# =============================================================================


@campaigns_bp.route("/api/campaign/<campaign_id>/players", methods=["GET", "POST"])
def api_list_players(campaign_id: str):
    """API: List players in campaign or create a new player."""
    import traceback

    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        if request.method == "GET":
            players = (
                session.query(CampaignPlayerRecord)
                .filter_by(campaign_id=campaign.id, is_active=True)
                .all()
            )

            return jsonify(
                [
                    {
                        "id": p.id,
                        "player_name": p.player_name,
                        "position": p.position,
                        "is_gm": p.is_gm,
                        "character_id": p.character_id,
                    }
                    for p in players
                ]
            )

        # POST - Create new player
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can create players"}), 403

        try:
            data = request.get_json()
        except Exception as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

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
        # Use a placeholder token prefixed with "unclaimed_" to mark as unclaimed
        # When a player claims this character, they get a new real token
        placeholder_token = f"unclaimed_{uuid.uuid4()}"
        new_player = CampaignPlayerRecord(
            campaign_id=campaign.id,
            character_id=character_id,
            player_name=player_name,
            session_token=placeholder_token,
            position="unassigned",  # Players will choose their position
            is_gm=False,
            is_active=True,
        )
        session.add(new_player)
        session.commit()

        return jsonify(
            {
                "success": True,
                "player": {
                    "id": new_player.id,
                    "player_name": new_player.player_name,
                    "character_id": new_player.character_id,
                },
            }
        )
    except Exception as e:
        print(f"ERROR in api_list_players: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/player/<int:player_id>/position", methods=["PUT"]
)
def api_update_player_position(campaign_id: str, player_id: int):
    """API: Update player's bridge position (player can update their own)."""
    session = get_session()
    try:
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        # Get current user
        current_user = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id)
            .first()
        )

        if not current_user:
            return jsonify({"error": "Not authenticated"}), 401

        # Players can only update their own position (or GM can update any)
        if not current_user.is_gm and current_user.id != player_id:
            return jsonify({"error": "Can only update your own position"}), 403

        # Get player record first
        player = (
            session.query(CampaignPlayerRecord)
            .filter_by(id=player_id, campaign_id=campaign.id)
            .first()
        )

        if not player:
            return jsonify({"error": "Player not found"}), 404

        # Check if there's an active encounter - if so, position is locked
        # BUT only if the player has already selected a position (not "unassigned")
        active_encounter = (
            session.query(EncounterRecord)
            .filter_by(campaign_id=campaign.id, status="active")
            .first()
        )

        if (
            active_encounter
            and not current_user.is_gm
            and player.position != "unassigned"
        ):
            return jsonify(
                {
                    "error": "Position locked during combat. Use Change Position action in combat."
                }
            ), 403

        data = request.get_json()
        new_position = data.get("position", player.position)

        # Check if position is already taken by another player
        if new_position and new_position != "gm" and new_position != "unassigned":
            existing_player = (
                session.query(CampaignPlayerRecord)
                .filter(
                    CampaignPlayerRecord.campaign_id == campaign.id,
                    CampaignPlayerRecord.id != player_id,
                    CampaignPlayerRecord.is_active == True,
                    CampaignPlayerRecord.is_gm == False,
                    CampaignPlayerRecord.position == new_position,
                )
                .first()
            )
            if existing_player:
                return jsonify(
                    {
                        "error": f"Position '{new_position}' is already taken by {existing_player.player_name}"
                    }
                ), 400

        player.position = new_position
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/player/<int:player_id>", methods=["DELETE"]
)
def api_remove_player(campaign_id: str, player_id: int):
    """API: Remove player from campaign (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can remove players"}), 403

        # Remove player (soft delete)
        player = (
            session.query(CampaignPlayerRecord)
            .filter_by(id=player_id, campaign_id=campaign.id)
            .first()
        )

        if not player:
            return jsonify({"error": "Player not found"}), 404

        if player.is_gm:
            return jsonify({"error": "Cannot remove GM"}), 400

        player.is_active = False
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/player/<int:player_id>/release", methods=["POST"]
)
def api_release_player(campaign_id: str, player_id: int):
    """API: Release a claimed character back to unclaimed state (GM only).

    This kicks the player who claimed the character but keeps the character
    available for someone else to claim.
    """
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can release players"}), 403

        player = (
            session.query(CampaignPlayerRecord)
            .filter_by(id=player_id, campaign_id=campaign.id)
            .first()
        )

        if not player:
            return jsonify({"error": "Player not found"}), 404

        if player.is_gm:
            return jsonify({"error": "Cannot release GM"}), 400

        # Check if already unclaimed
        if player.session_token.startswith("unclaimed_"):
            return jsonify({"error": "Character is not claimed by anyone"}), 400

        # Reset to unclaimed state
        player.session_token = f"unclaimed_{uuid.uuid4()}"
        session.commit()

        return jsonify(
            {"success": True, "message": f"{player.player_name} has been released"}
        )
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/player/<int:player_id>", methods=["GET"]
)
def api_get_player(campaign_id: str, player_id: int):
    """API: Get player details with character data."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        player = (
            session.query(CampaignPlayerRecord)
            .filter_by(id=player_id, campaign_id=campaign.id)
            .first()
        )

        if not player:
            return jsonify({"error": "Player not found"}), 404

        # Load character data
        character_data = None
        if player.character_id:
            char_record = (
                session.query(CharacterRecord).filter_by(id=player.character_id).first()
            )
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
                    },
                    "focuses": char.focuses or [],
                    "talents": char.talents or [],
                }

        return jsonify(
            {
                "id": player.id,
                "player_name": player.player_name,
                "position": player.position,
                "is_gm": player.is_gm,
                "character_id": player.character_id,
                "character": character_data,
            }
        )
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/player/<int:player_id>", methods=["PUT"]
)
def api_update_player(campaign_id: str, player_id: int):
    """API: Update player and character data (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can update players"}), 403

        player = (
            session.query(CampaignPlayerRecord)
            .filter_by(id=player_id, campaign_id=campaign.id)
            .first()
        )

        if not player:
            return jsonify({"error": "Player not found"}), 404

        data = request.get_json()

        # Update player name
        if "name" in data:
            player.player_name = data["name"]

        # Update character data
        if player.character_id:
            char_record = (
                session.query(CharacterRecord).filter_by(id=player.character_id).first()
            )
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

                # Update focuses JSON
                if "focuses" in data:
                    char_record.focuses_json = json.dumps(
                        data["focuses"] if isinstance(data["focuses"], list) else []
                    )

                # Update talents JSON
                if "talents" in data:
                    char_record.talents_json = json.dumps(
                        data["talents"] if isinstance(data["talents"], list) else []
                    )

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
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        campaign_ships = (
            session.query(CampaignShipRecord).filter_by(campaign_id=campaign.id).all()
        )

        ships = []
        for cs in campaign_ships:
            ship_record = session.query(StarshipRecord).filter_by(id=cs.ship_id).first()
            if ship_record:
                ships.append(
                    {
                        "id": cs.id,
                        "ship_id": ship_record.id,
                        "name": ship_record.name,
                        "ship_class": ship_record.ship_class,
                        "is_active": campaign.active_ship_id == ship_record.id,
                        "is_available": cs.is_available,
                    }
                )

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

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

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

        return jsonify(
            {
                "success": True,
                "ship_id": ship_id,
                "campaign_ship_id": campaign_ship.id,
            }
        )
    finally:
        session.close()


# =============================================================================
# NPC Pool Management API
# =============================================================================


@campaigns_bp.route("/api/campaign/<campaign_id>/npcs", methods=["GET"])
def api_list_npcs(campaign_id: str):
    """API: List NPCs in campaign pool."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        campaign_npcs = (
            session.query(CampaignNPCRecord).filter_by(campaign_id=campaign.id).all()
        )

        npcs = []
        for cn in campaign_npcs:
            npc_record = session.query(NPCRecord).filter_by(id=cn.npc_id).first()
            if npc_record:
                npcs.append(
                    {
                        "id": cn.id,
                        "npc_id": npc_record.id,
                        "name": npc_record.name,
                        "npc_type": npc_record.npc_type,
                        "affiliation": npc_record.affiliation,
                        "is_visible": cn.is_visible_to_players,
                    }
                )

        return jsonify(npcs)
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/npcs", methods=["POST"])
def api_add_npc(campaign_id: str):
    """API: Add NPC to campaign pool (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can add NPCs"}), 403

        data = request.get_json()
        action = data.get("action", "create")

        if action == "link":
            # Link existing global NPC to campaign
            npc_id = data.get("npc_id")
            if not npc_id:
                return jsonify({"error": "npc_id required for link action"}), 400

            # Check if already linked
            existing = (
                session.query(CampaignNPCRecord)
                .filter_by(campaign_id=campaign.id, npc_id=npc_id)
                .first()
            )
            if existing:
                return jsonify({"error": "NPC already in campaign"}), 400

        elif action == "create":
            # Create new NPC from provided data
            npc = NPCRecord(
                name=data.get("name", "New NPC"),
                npc_type=data.get("npc_type", "minor"),
                appearance=data.get("appearance"),
                motivation=data.get("motivation"),
                affiliation=data.get("affiliation"),
                location=data.get("location"),
                picture_url=data.get("picture_url"),
                notes=data.get("notes"),
            )
            session.add(npc)
            session.flush()
            npc_id = npc.id
        else:
            return jsonify({"error": "Invalid action. Use 'link' or 'create'"}), 400

        # Add to campaign pool
        campaign_npc = CampaignNPCRecord(
            campaign_id=campaign.id,
            npc_id=npc_id,
            is_visible_to_players=data.get("is_visible", False),
        )
        session.add(campaign_npc)
        session.commit()

        return jsonify(
            {
                "success": True,
                "npc_id": npc_id,
                "campaign_npc_id": campaign_npc.id,
            }
        )
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/npcs/<int:campaign_npc_id>", methods=["DELETE"]
)
def api_remove_npc(campaign_id: str, campaign_npc_id: int):
    """API: Remove NPC from campaign pool (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can remove NPCs"}), 403

        campaign_npc = (
            session.query(CampaignNPCRecord)
            .filter_by(id=campaign_npc_id, campaign_id=campaign.id)
            .first()
        )

        if not campaign_npc:
            return jsonify({"error": "NPC not in campaign"}), 404

        session.delete(campaign_npc)
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/npcs/<int:campaign_npc_id>/visibility", methods=["PUT"]
)
def api_toggle_npc_visibility(campaign_id: str, campaign_npc_id: int):
    """API: Toggle NPC visibility in campaign (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can toggle visibility"}), 403

        campaign_npc = (
            session.query(CampaignNPCRecord)
            .filter_by(id=campaign_npc_id, campaign_id=campaign.id)
            .first()
        )

        if not campaign_npc:
            return jsonify({"error": "NPC not in campaign"}), 404

        data = request.get_json()
        campaign_npc.is_visible_to_players = data.get(
            "is_visible", not campaign_npc.is_visible_to_players
        )
        session.commit()

        return jsonify(
            {"success": True, "is_visible": campaign_npc.is_visible_to_players}
        )
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

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can set active ship"}), 403

        data = request.get_json()
        ship_id = data.get("ship_id")

        # Verify ship is in campaign pool
        campaign_ship = (
            session.query(CampaignShipRecord)
            .filter_by(campaign_id=campaign.id, ship_id=ship_id)
            .first()
        )

        if not campaign_ship:
            return jsonify({"error": "Ship not in campaign pool"}), 400

        campaign.active_ship_id = ship_id
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route(
    "/api/campaign/<campaign_id>/ships/<int:campaign_ship_id>", methods=["DELETE"]
)
def api_remove_ship(campaign_id: str, campaign_ship_id: int):
    """API: Remove ship from campaign pool (GM only)."""
    session = get_session()
    try:
        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can remove ships"}), 403

        campaign_ship = (
            session.query(CampaignShipRecord)
            .filter_by(id=campaign_ship_id, campaign_id=campaign.id)
            .first()
        )

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
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        status_filter = request.args.get("status")  # Optional filter

        query = session.query(EncounterRecord).filter_by(campaign_id=campaign.id)
        if status_filter:
            query = query.filter_by(status=status_filter)

        encounters = query.order_by(EncounterRecord.created_at.desc()).all()

        return jsonify(
            [
                {
                    "id": e.id,
                    "encounter_id": e.encounter_id,
                    "name": e.name,
                    "status": e.status,
                    "round": e.round,
                    "momentum": e.momentum,
                    "threat": e.threat,
                }
                for e in encounters
            ]
        )
    finally:
        session.close()


@campaigns_bp.route("/api/encounter/<encounter_id>/status", methods=["PUT"])
def api_update_encounter_status(encounter_id: str):
    """API: Update encounter status (GM only)."""
    session = get_session()
    try:
        encounter = (
            session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()
        )

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        if not encounter.campaign_id:
            return jsonify({"error": "Encounter not part of a campaign"}), 400

        campaign = (
            session.query(CampaignRecord).filter_by(id=encounter.campaign_id).first()
        )

        # Verify GM
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can change encounter status"}), 403

        data = request.get_json()
        new_status = data.get("status")

        if new_status not in ("draft", "active", "completed"):
            return jsonify({"error": "Invalid status"}), 400

        # Enforce single active encounter
        if new_status == "active":
            existing_active = (
                session.query(EncounterRecord)
                .filter(
                    EncounterRecord.campaign_id == campaign.id,
                    EncounterRecord.status == "active",
                    EncounterRecord.id != encounter.id,
                )
                .first()
            )

            if existing_active:
                return jsonify(
                    {
                        "error": "Campaign already has an active encounter. Complete it first."
                    }
                ), 400

        encounter.status = new_status
        session.commit()

        return jsonify({"success": True, "status": new_status})
    finally:
        session.close()


@campaigns_bp.route("/api/campaign/<campaign_id>/change-gm-password", methods=["POST"])
def api_change_gm_password(campaign_id: str):
    """API: Change GM password (GM only)."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        # Verify GM session
        session_token = request.cookies.get("sta_session_token")
        if not session_token:
            return jsonify({"error": "Not authenticated"}), 401

        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(session_token=session_token, campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm:
            return jsonify({"error": "Only GM can change the password"}), 403

        data = request.get_json()
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        if len(new_password) < 4:
            return jsonify({"error": "Password must be at least 4 characters"}), 400

        # Verify current password
        password_hash = campaign.gm_password_hash
        if not password_hash:
            # Legacy campaign - use default
            password_hash = generate_password_hash(DEFAULT_GM_PASSWORD)

        if not check_password_hash(password_hash, current_password):
            return jsonify({"error": "Current password is incorrect"}), 403

        # Update password
        campaign.gm_password_hash = generate_password_hash(new_password)
        session.commit()

        return jsonify({"success": True, "message": "Password changed successfully"})
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
        return jsonify(
            {
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
                },
            }
        )
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

        # Update combat stats
        if "shields" in data:
            ship_record.shields = data["shields"]
        if "shields_max" in data:
            ship_record.shields_max = data["shields_max"]
        if "resistance" in data:
            ship_record.resistance = data["resistance"]
        if "crew_quality" in data:
            ship_record.crew_quality = data["crew_quality"]

        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/encounter/<encounter_id>", methods=["GET"])
def api_get_encounter(encounter_id: str):
    """API: Get encounter details."""
    session = get_session()
    try:
        encounter = (
            session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()
        )

        if not encounter:
            return jsonify({"error": "Encounter not found"}), 404

        return jsonify(
            {
                "encounter_id": encounter.encounter_id,
                "name": encounter.name,
                "description": encounter.description,
                "status": encounter.status,
                "round": encounter.round,
                "threat": encounter.threat,
            }
        )
    finally:
        session.close()


@campaigns_bp.route("/api/encounter/<encounter_id>", methods=["PUT"])
def api_update_encounter(encounter_id: str):
    """API: Update encounter details (GM only)."""
    session = get_session()
    try:
        encounter = (
            session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()
        )

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
        encounter = (
            session.query(EncounterRecord).filter_by(encounter_id=encounter_id).first()
        )

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


# ========== Scene API Endpoints ==========


@campaigns_bp.route("/api/campaign/<campaign_id>/scenes", methods=["POST"])
def api_create_scene(campaign_id: str):
    """API: Create a new scene (GM only)."""
    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )

        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        # Verify GM status
        session_token = request.cookies.get("sta_session_token")
        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(campaign_id=campaign.id, is_gm=True)
            .first()
        )

        if not gm or session_token != gm.session_token:
            return jsonify({"error": "Only GM can create scenes"}), 403

        data = request.get_json() or {}

        scene = SceneRecord(
            campaign_id=campaign.id,
            name=data.get("name", "New Scene"),
            scene_type=data.get("scene_type", "narrative"),
            status=data.get("status", "draft"),
            stardate=data.get("stardate"),
            scene_traits_json=json.dumps(data.get("scene_traits", [])),
            has_map=data.get("scene_type")
            in ["narrative", "starship_encounter", "personal_encounter"],
        )
        session.add(scene)
        session.commit()

        return jsonify(
            {
                "success": True,
                "id": scene.id,
                "name": scene.name,
                "scene_type": scene.scene_type,
            }
        )
    finally:
        session.close()


@campaigns_bp.route("/api/scene/<int:scene_id>/status", methods=["PUT"])
def api_update_scene_status(scene_id: int):
    """API: Update scene status (GM only)."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        # Verify GM status
        session_token = request.cookies.get("sta_session_token")
        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(campaign_id=scene.campaign_id, is_gm=True)
            .first()
        )

        if not gm or session_token != gm.session_token:
            return jsonify({"error": "Only GM can change scene status"}), 403

        data = request.get_json()
        new_status = data.get("status")

        if new_status not in ("draft", "active", "completed"):
            return jsonify({"error": "Invalid status"}), 400

        # Enforce single active scene
        if new_status == "active":
            existing_active = (
                session.query(SceneRecord)
                .filter(
                    SceneRecord.campaign_id == scene.campaign_id,
                    SceneRecord.status == "active",
                    SceneRecord.id != scene.id,
                )
                .first()
            )

            if existing_active:
                existing_active.status = "draft"

        scene.status = new_status
        session.commit()
        return jsonify({"success": True, "status": scene.status})
    finally:
        session.close()


@campaigns_bp.route("/api/scene/<int:scene_id>", methods=["DELETE"])
def api_delete_scene(scene_id: int):
    """API: Delete scene (GM only)."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        # Verify GM status
        session_token = request.cookies.get("sta_session_token")
        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(campaign_id=scene.campaign_id, is_gm=True)
            .first()
        )

        if not gm or session_token != gm.session_token:
            return jsonify({"error": "Only GM can delete scenes"}), 403

        # Don't delete active scenes
        if scene.status == "active":
            return jsonify({"error": "Cannot delete active scenes"}), 400

        session.delete(scene)
        session.commit()
        return jsonify({"success": True})
    finally:
        session.close()


@campaigns_bp.route("/api/scene/<int:scene_id>/convert", methods=["PUT"])
def api_convert_scene(scene_id: int):
    """API: Convert scene to a different type (GM only)."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        # Verify GM status
        session_token = request.cookies.get("sta_session_token")
        gm = (
            session.query(CampaignPlayerRecord).filter_by(
                campaign_id=scene.campaign_id, is_gm=True
            )
        ).first()

        if not gm or session_token != gm.session_token:
            return jsonify({"error": "Only GM can convert scenes"}), 403

        data = request.get_json()
        new_type = data.get("scene_type")

        if new_type not in (
            "narrative",
            "starship_encounter",
            "personal_encounter",
            "social_encounter",
        ):
            return jsonify({"error": "Invalid scene type"}), 400

        # Validation for combat types
        if new_type == "starship_encounter":
            # Check for player ship
            campaign = (
                session.query(CampaignRecord).filter_by(id=scene.campaign_id).first()
            )
            if not campaign or not campaign.active_ship_id:
                return jsonify(
                    {
                        "error": "Cannot convert to Starship Combat: No player ship assigned to campaign"
                    }
                ), 400

            # Check for NPCs or NP ships
            from sta.database import SceneNPCRecord

            scene_npcs = (
                session.query(SceneNPCRecord).filter_by(scene_id=scene.id).count()
            )
            if scene_npcs == 0:
                return jsonify(
                    {
                        "error": "Cannot convert to Starship Combat: No NPC ships or characters in scene. Add NPCs first."
                    }
                ), 400

        if new_type == "personal_encounter":
            # Check for NPCs
            from sta.database import SceneNPCRecord

            scene_npcs = (
                session.query(SceneNPCRecord).filter_by(scene_id=scene.id).count()
            )
            if scene_npcs == 0:
                return jsonify(
                    {
                        "error": "Cannot convert to Personal Combat: No NPCs in scene. Add NPCs first."
                    }
                ), 400

        old_type = scene.scene_type
        scene.scene_type = new_type

        # Update has_map based on type (social encounters don't have maps)
        scene.has_map = new_type != "social_encounter"

        session.commit()

        return jsonify(
            {
                "success": True,
                "old_type": old_type,
                "new_type": new_type,
                "message": f"Scene converted from {old_type} to {new_type}",
            }
        )

        if not gm or session_token != gm.session_token:
            return jsonify({"error": "Only GM can convert scenes"}), 403

        data = request.get_json()
        new_type = data.get("scene_type")

        if new_type not in (
            "narrative",
            "starship_encounter",
            "personal_encounter",
            "social_encounter",
        ):
            return jsonify({"error": "Invalid scene type"}), 400

        old_type = scene.scene_type
        scene.scene_type = new_type

        # Update has_map based on type (social encounters don't have maps)
        scene.has_map = new_type != "social_encounter"

        session.commit()

        return jsonify(
            {
                "success": True,
                "old_type": old_type,
                "new_type": new_type,
                "message": f"Scene converted from {old_type} to {new_type}",
            }
        )
    finally:
        session.close()
