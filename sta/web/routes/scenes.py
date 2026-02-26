"""Scene routes for scene management."""

import json
import os
import uuid
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from sta.database import (
    get_session,
    SceneRecord,
    CampaignRecord,
    CampaignPlayerRecord,
    SceneNPCRecord,
    NPCRecord,
    CampaignNPCRecord,
    StarshipRecord,
    CampaignShipRecord,
)
from sta.models.enums import Position


scenes_bp = Blueprint("scenes", __name__)


@scenes_bp.route("/new", methods=["GET", "POST"])
def new_scene():
    """Create a new scene (narrative or starship encounter)."""
    campaign_id = request.args.get("campaign_id")
    if not campaign_id:
        flash("Campaign ID required")
        return redirect(url_for("main.index"))

    session = get_session()
    try:
        campaign = (
            session.query(CampaignRecord).filter_by(campaign_id=campaign_id).first()
        )
        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("main.index"))

        # Get available ships for the campaign
        campaign_ships = (
            session.query(CampaignShipRecord).filter_by(campaign_id=campaign.id).all()
        )
        available_ships = []
        for cs in campaign_ships:
            ship = session.query(StarshipRecord).filter_by(id=cs.ship_id).first()
            if ship:
                available_ships.append(ship)

        if request.method == "POST":
            name = request.form.get("name", "New Scene")
            scene_type = request.form.get("scene_type", "narrative")
            description = request.form.get("description", "")
            stardate = request.form.get("stardate", "")
            position = request.form.get("position", "captain")
            status = request.form.get("status", "draft")

            player_ship_id = request.form.get("player_ship_id")
            if player_ship_id:
                player_ship_id = int(player_ship_id)
            elif campaign.active_ship_id:
                player_ship_id = campaign.active_ship_id

            enemy_ships_json = request.form.get("enemy_ships_json", "[]")
            tactical_map_json = request.form.get("tactical_map_json", "{}")
            ship_positions_json = request.form.get("ship_positions_json", "{}")

            enemy_count = int(request.form.get("enemy_count", "1"))
            crew_quality = request.form.get("crew_quality", "talented")

            scene = SceneRecord(
                campaign_id=campaign.id,
                name=name,
                description=description,
                scene_type=scene_type,
                stardate=stardate or None,
                status=status,
                player_ship_id=player_ship_id,
                scene_position=position,
                enemy_ships_json=enemy_ships_json,
                tactical_map_json=tactical_map_json,
                has_map=bool(tactical_map_json and tactical_map_json != "{}"),
            )
            session.add(scene)
            session.flush()

            enemy_ships = (
                json.loads(enemy_ships_json) if enemy_ships_json != "[]" else []
            )

            active_ship = None
            if campaign.active_ship_id:
                active_ship = (
                    session.query(StarshipRecord)
                    .filter_by(id=campaign.active_ship_id)
                    .first()
                )
            player_scale = active_ship.scale if active_ship else 4

            if scene_type == "starship_encounter" and enemy_count > 0:
                if not enemy_ships:
                    ship_positions = (
                        json.loads(ship_positions_json)
                        if ship_positions_json and ship_positions_json != "{}"
                        else {}
                    )
                    for i in range(enemy_count):
                        enemy_ships.append(
                            {
                                "id": f"enemy_{i}",
                                "name": f"Enemy Ship {i + 1}",
                                "ship_class": "Generic Fighter",
                                "scale": max(1, player_scale - 1),
                                "crew_quality": crew_quality,
                                "systems": {
                                    "comms": 8,
                                    "computers": 8,
                                    "engines": 8,
                                    "sensors": 8,
                                    "structure": 8,
                                    "weapons": 8,
                                },
                                "departments": {
                                    "command": 1,
                                    "conn": 1,
                                    "engineering": 1,
                                    "medicine": 1,
                                    "science": 1,
                                    "security": 1,
                                },
                                "weapons": [
                                    {
                                        "name": "Phaser Array",
                                        "weapon_type": "phaser",
                                        "damage": 2,
                                        "range": "medium",
                                        "qualities": [],
                                    }
                                ],
                                "shields": 8,
                                "shields_max": 8,
                                "position": ship_positions.get(
                                    f"enemy_{i}", {"q": 2, "r": -1}
                                )
                                if ship_positions_json
                                else {"q": 2, "r": -1},
                            }
                        )

                    scene.enemy_ships_json = json.dumps(enemy_ships)

                if tactical_map_json == "{}" and ship_positions_json:
                    scene.tactical_map_json = json.dumps(
                        {
                            "radius": 3,
                            "tiles": [],
                            "positions": json.loads(ship_positions_json),
                        }
                    )

            session.commit()

            # For starship_encounter, redirect to edit page where combat can be started
            if scene_type == "starship_encounter":
                return redirect(url_for("scenes.edit_scene", scene_id=scene.id))

            return redirect(url_for("scenes.edit_scene", scene_id=scene.id))

        positions = [p.value for p in Position]

        # Get scene_type from query param or default to starship_encounter
        default_scene_type = request.args.get("scene_type", "starship_encounter")
        if default_scene_type not in (
            "narrative",
            "starship_encounter",
            "personal_encounter",
            "social_encounter",
        ):
            default_scene_type = "starship_encounter"

        return render_template(
            "new_scene.html",
            campaign=campaign,
            available_ships=available_ships,
            positions=positions,
            default_scene_type=default_scene_type,
        )
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>")
def view_scene(scene_id: int):
    """View a scene (GM, player, or viewscreen)."""
    role = request.args.get("role", "player")
    if role not in ("player", "gm", "viewscreen"):
        role = "player"

    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            flash("Scene not found")
            return redirect(url_for("main.index"))

        campaign = session.query(CampaignRecord).filter_by(id=scene.campaign_id).first()

        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("main.index"))

        # For GM role, verify they have a valid GM session
        if role == "gm":
            session_token = request.cookies.get("sta_session_token")
            gm_player = (
                session.query(CampaignPlayerRecord)
                .filter_by(campaign_id=scene.campaign_id, is_gm=True)
                .first()
            )

            if not gm_player or session_token != gm_player.session_token:
                return redirect(
                    url_for("campaigns.gm_login", campaign_id=campaign.campaign_id)
                )

        # Parse scene data
        scene_traits = json.loads(scene.scene_traits_json or "[]")

        scene_data = {
            "id": scene.id,
            "name": scene.name,
            "description": scene.description,
            "scene_type": scene.scene_type,
            "status": scene.status,
            "stardate": scene.stardate,
            "scene_traits": scene_traits,
            "challenges": json.loads(scene.challenges_json or "[]"),
            "characters_present": json.loads(scene.characters_present_json or "[]"),
            "has_map": scene.has_map,
            "tactical_map": json.loads(scene.tactical_map_json or "{}"),
        }

        # Load NPCs for this scene
        scene_npcs = (
            session.query(SceneNPCRecord)
            .filter_by(scene_id=scene.id)
            .order_by(SceneNPCRecord.order_index)
            .all()
        )
        npcs_data = []
        for sn in scene_npcs:
            if sn.npc_id:
                npc = session.query(NPCRecord).filter_by(id=sn.npc_id).first()
                if npc:
                    npcs_data.append(
                        {
                            "id": sn.id,
                            "npc_id": npc.id,
                            "name": npc.name,
                            "npc_type": npc.npc_type,
                            "is_visible": sn.is_visible_to_players,
                        }
                    )
            elif sn.quick_name:
                npcs_data.append(
                    {
                        "id": sn.id,
                        "npc_id": None,
                        "name": sn.quick_name,
                        "npc_type": "quick",
                        "is_visible": sn.is_visible_to_players,
                    }
                )

        # For combat scenes with encounter, redirect to combat view
        if scene.encounter_id:
            from sta.database import EncounterRecord

            encounter = (
                session.query(EncounterRecord).filter_by(id=scene.encounter_id).first()
            )
            if encounter:
                return redirect(
                    url_for(
                        "encounters.combat",
                        encounter_id=encounter.encounter_id,
                        role=role,
                    )
                )

        # Use combat templates for narrative scenes
        if role == "viewscreen":
            template = "combat_viewscreen.html"
        elif role == "gm":
            template = "combat_gm.html"
        else:
            template = "combat.html"

        # Load player ship for the campaign
        player_ship = None
        if campaign.active_ship_id:
            ship_record = (
                session.query(StarshipRecord)
                .filter_by(id=campaign.active_ship_id)
                .first()
            )
            if ship_record:
                player_ship = ship_record.to_model()

        return render_template(
            template,
            scene=scene_data,
            scene_record=scene,
            campaign=campaign,
            role=role,
            is_narrative=True,
            npcs=npcs_data,
            player_ship=player_ship,
            player_char=None,
            position=None,
            actions={
                "position_minor": [],
                "position_major": [],
                "standard_minor": [],
                "standard_major": [],
            },
            enemy_ships=[],
            resistance_bonus=0,
            encounter=None,
        )
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/edit")
def edit_scene(scene_id: int):
    """Edit a scene - show dedicated edit page for narrative scenes."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            flash("Scene not found")
            return redirect(url_for("main.index"))

        campaign = session.query(CampaignRecord).filter_by(id=scene.campaign_id).first()
        if not campaign:
            flash("Campaign not found")
            return redirect(url_for("main.index"))

        # Parse scene data
        scene_traits = json.loads(scene.scene_traits_json or "[]")
        challenges = json.loads(scene.challenges_json or "[]")
        characters_present = json.loads(scene.characters_present_json or "[]")
        enemy_ships = json.loads(scene.enemy_ships_json or "[]")
        tactical_map = json.loads(scene.tactical_map_json or "{}")

        scene_data = {
            "id": scene.id,
            "name": scene.name,
            "description": scene.description,
            "scene_type": scene.scene_type,
            "status": scene.status,
            "stardate": scene.stardate,
            "scene_traits": scene_traits,
            "challenges": challenges,
            "characters_present": characters_present,
            "player_ship_id": scene.player_ship_id,
            "scene_position": scene.scene_position,
            "enemy_ships": enemy_ships,
            "tactical_map": tactical_map,
        }

        # Load NPCs for this scene
        scene_npcs = (
            session.query(SceneNPCRecord)
            .filter_by(scene_id=scene.id)
            .order_by(SceneNPCRecord.order_index)
            .all()
        )
        npcs_data = []
        for sn in scene_npcs:
            if sn.npc_id:
                npc = session.query(NPCRecord).filter_by(id=sn.npc_id).first()
                if npc:
                    npcs_data.append(
                        {
                            "id": sn.id,
                            "npc_id": npc.id,
                            "name": npc.name,
                            "npc_type": npc.npc_type,
                            "is_visible": sn.is_visible_to_players,
                        }
                    )
            elif sn.quick_name:
                npcs_data.append(
                    {
                        "id": sn.id,
                        "npc_id": None,
                        "name": sn.quick_name,
                        "npc_type": "quick",
                        "is_visible": sn.is_visible_to_players,
                    }
                )

        # Load available ships for this campaign
        campaign_ships = (
            session.query(CampaignShipRecord).filter_by(campaign_id=campaign.id).all()
        )
        available_ships = []
        for cs in campaign_ships:
            ship = session.query(StarshipRecord).filter_by(id=cs.ship_id).first()
            if ship:
                available_ships.append(ship)

        # Get positions list
        positions = [p.value for p in Position]

        return render_template(
            "edit_scene.html",
            scene=scene_data,
            scene_record=scene,
            campaign=campaign,
            npcs=npcs_data,
            available_ships=available_ships,
            positions=positions,
        )
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/npcs", methods=["GET"])
def get_scene_npcs(scene_id: int):
    """Get NPCs for a scene."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        scene_npcs = (
            session.query(SceneNPCRecord)
            .filter_by(scene_id=scene_id)
            .order_by(SceneNPCRecord.order_index)
            .all()
        )

        npcs = []
        for sn in scene_npcs:
            npc_data = {
                "id": sn.id,
                "is_visible": sn.is_visible_to_players,
            }
            if sn.npc_id:
                npc = session.query(NPCRecord).filter_by(id=sn.npc_id).first()
                if npc:
                    npc_data["name"] = npc.name
                    npc_data["npc_type"] = npc.npc_type
                    npc_data["npc_id"] = npc.id
            elif sn.quick_name:
                npc_data["name"] = sn.quick_name
                npc_data["npc_type"] = "quick"
            npcs.append(npc_data)

        return jsonify({"npcs": npcs})
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/npcs/<int:npc_id>/visibility", methods=["PUT"])
def toggle_npc_visibility(scene_id: int, npc_id: int):
    """Toggle NPC visibility."""
    session = get_session()
    try:
        scene_npc = (
            session.query(SceneNPCRecord)
            .filter_by(id=npc_id, scene_id=scene_id)
            .first()
        )
        if not scene_npc:
            return jsonify({"error": "NPC not found in scene"}), 404

        data = request.get_json() or {}
        scene_npc.is_visible_to_players = data.get("is_visible", False)
        session.commit()

        return jsonify({"success": True, "is_visible": scene_npc.is_visible_to_players})
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/npcs/available", methods=["GET"])
def get_available_npcs(scene_id: int):
    """Get NPCs available to add to scene (from campaign manifest + archive)."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        campaign_id = scene.campaign_id

        available = []

        campaign_npcs = (
            session.query(CampaignNPCRecord).filter_by(campaign_id=campaign_id).all()
        )
        for cn in campaign_npcs:
            npc = session.query(NPCRecord).filter_by(id=cn.npc_id).first()
            if npc:
                existing = (
                    session.query(SceneNPCRecord)
                    .filter_by(scene_id=scene_id, npc_id=npc.id)
                    .first()
                )
                if not existing:
                    available.append(
                        {
                            "id": npc.id,
                            "name": npc.name,
                            "npc_type": npc.npc_type,
                            "source": "campaign",
                        }
                    )

        return jsonify({"npcs": available})
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/npcs", methods=["POST"])
def add_npc_to_scene(scene_id: int):
    """Add an NPC to a scene."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        data = request.get_json() or {}

        max_order = session.query(SceneNPCRecord).filter_by(scene_id=scene_id).count()

        if data.get("npc_id"):
            npc_id = data["npc_id"]
            npc = session.query(NPCRecord).filter_by(id=npc_id).first()
            if not npc:
                return jsonify({"error": "NPC not found"}), 404

            existing = (
                session.query(SceneNPCRecord)
                .filter_by(scene_id=scene_id, npc_id=npc_id)
                .first()
            )
            if existing:
                return jsonify({"error": "NPC already in scene"}), 400

            scene_npc = SceneNPCRecord(
                scene_id=scene_id,
                npc_id=npc_id,
                is_visible_to_players=data.get("is_visible", False),
                order_index=max_order,
            )
            session.add(scene_npc)
            session.commit()

            return jsonify(
                {
                    "success": True,
                    "scene_npc_id": scene_npc.id,
                    "name": npc.name,
                    "npc_type": npc.npc_type,
                    "is_visible": scene_npc.is_visible_to_players,
                }
            )

        elif data.get("quick_name"):
            quick_name = data["quick_name"].strip()
            if not quick_name:
                return jsonify({"error": "Name is required"}), 400

            scene_npc = SceneNPCRecord(
                scene_id=scene_id,
                quick_name=quick_name,
                quick_description=data.get("quick_description", ""),
                is_visible_to_players=data.get("is_visible", False),
                order_index=max_order,
            )
            session.add(scene_npc)
            session.commit()

            return jsonify(
                {
                    "success": True,
                    "scene_npc_id": scene_npc.id,
                    "name": quick_name,
                    "npc_type": "quick",
                    "is_visible": scene_npc.is_visible_to_players,
                }
            )

        else:
            return jsonify({"error": "npc_id or quick_name required"}), 400

    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/npcs/<int:scene_npc_id>", methods=["DELETE"])
def remove_npc_from_scene(scene_id: int, scene_npc_id: int):
    """Remove an NPC from a scene."""
    session = get_session()
    try:
        scene_npc = (
            session.query(SceneNPCRecord)
            .filter_by(id=scene_npc_id, scene_id=scene_id)
            .first()
        )
        if not scene_npc:
            return jsonify({"error": "NPC not found in scene"}), 404

        session.delete(scene_npc)
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()
