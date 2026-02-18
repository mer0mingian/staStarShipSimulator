"""Scene routes for scene management."""

import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sta.database import (
    get_session,
    SceneRecord,
    CampaignRecord,
    CampaignPlayerRecord,
    SceneNPCRecord,
    NPCRecord,
    StarshipRecord,
)

scenes_bp = Blueprint("scenes", __name__)


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
            "scene_type": scene.scene_type,
            "status": scene.status,
            "stardate": scene.stardate,
            "scene_picture_url": scene.scene_picture_url,
            "scene_traits": scene_traits,
            "challenges": json.loads(scene.challenges_json or "[]"),
            "characters_present": json.loads(scene.characters_present_json or "[]"),
            "show_picture": scene.show_picture,
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
            encounter=None,
        )
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/edit")
def edit_scene(scene_id: int):
    """Edit a scene - redirect to GM view."""
    return redirect(url_for("scenes.view_scene", scene_id=scene_id, role="gm"))


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
