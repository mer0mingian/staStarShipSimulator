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
    ScenePictureRecord,
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


# ===== PICTURE MANAGEMENT =====


@scenes_bp.route("/<int:scene_id>/pictures", methods=["GET"])
def get_scene_pictures(scene_id: int):
    """Get all pictures for a scene."""
    session = get_session()
    try:
        pictures = (
            session.query(ScenePictureRecord)
            .filter_by(scene_id=scene_id)
            .order_by(ScenePictureRecord.order_index)
            .all()
        )

        return jsonify(
            {
                "pictures": [
                    {
                        "id": p.id,
                        "url": p.url or f"/scenes/uploads/{p.filename}",
                        "original_name": p.original_name,
                        "is_active": p.is_active,
                        "order_index": p.order_index,
                    }
                    for p in pictures
                ]
            }
        )
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/pictures", methods=["POST"])
def upload_scene_picture(scene_id: int):
    """Upload a picture for a scene."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        data = request.get_json() or {}

        if data.get("url"):
            url = data["url"].strip()
            if not url:
                return jsonify({"error": "URL is required"}), 400

            max_order = (
                session.query(ScenePictureRecord).filter_by(scene_id=scene_id).count()
            )

            picture = ScenePictureRecord(
                scene_id=scene_id, url=url, is_active=False, order_index=max_order
            )
            session.add(picture)
            session.commit()

            return jsonify(
                {
                    "success": True,
                    "picture": {
                        "id": picture.id,
                        "url": picture.url,
                        "is_active": picture.is_active,
                    },
                }
            )

        return jsonify({"error": "url required"}), 400

    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/pictures/upload", methods=["POST"])
def upload_picture_file(scene_id: int):
    """Upload a picture file for a scene."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            return jsonify({"error": "Scene not found"}), 404

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        original_name = file.filename
        ext = original_name.rsplit(".", 1)[1].lower()
        filename = f"{scene_id}_{uuid.uuid4().hex[:8]}.{ext}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        file.save(os.path.join(upload_folder, filename))

        max_order = (
            session.query(ScenePictureRecord).filter_by(scene_id=scene_id).count()
        )

        picture = ScenePictureRecord(
            scene_id=scene_id,
            filename=filename,
            original_name=original_name,
            is_active=False,
            order_index=max_order,
        )
        session.add(picture)
        session.commit()

        return jsonify(
            {
                "success": True,
                "picture": {
                    "id": picture.id,
                    "url": f"/scenes/uploads/{filename}",
                    "original_name": original_name,
                    "is_active": picture.is_active,
                },
            }
        )

    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/pictures/<int:picture_id>/activate", methods=["POST"])
def activate_picture(scene_id: int, picture_id: int):
    """Set a picture as the active one for the scene."""
    session = get_session()
    try:
        picture = (
            session.query(ScenePictureRecord)
            .filter_by(id=picture_id, scene_id=scene_id)
            .first()
        )
        if not picture:
            return jsonify({"error": "Picture not found"}), 404

        session.query(ScenePictureRecord).filter_by(scene_id=scene_id).update(
            {"is_active": False}
        )

        picture.is_active = True

        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if scene:
            scene.scene_picture_url = (
                picture.url or f"/scenes/uploads/{picture.filename}"
            )
            scene.show_picture = True

        session.commit()

        return jsonify({"success": True, "is_active": True})
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/pictures/<int:picture_id>", methods=["DELETE"])
def delete_picture(scene_id: int, picture_id: int):
    """Delete a picture from a scene."""
    session = get_session()
    try:
        picture = (
            session.query(ScenePictureRecord)
            .filter_by(id=picture_id, scene_id=scene_id)
            .first()
        )
        if not picture:
            return jsonify({"error": "Picture not found"}), 404

        if picture.filename:
            try:
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                file_path = os.path.join(upload_folder, picture.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        session.delete(picture)
        session.commit()

        return jsonify({"success": True})
    finally:
        session.close()


@scenes_bp.route("/uploads/<filename>")
def serve_upload(filename):
    """Serve uploaded files."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename)
