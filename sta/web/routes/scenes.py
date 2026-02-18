"""Scene routes for scene management."""

import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sta.database import get_session, SceneRecord, CampaignRecord, CampaignPlayerRecord

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

        # Load campaign
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
        scene_data = {
            "id": scene.id,
            "name": scene.name,
            "scene_type": scene.scene_type,
            "status": scene.status,
            "stardate": scene.stardate,
            "scene_picture_url": scene.scene_picture_url,
            "scene_traits": json.loads(scene.scene_traits_json or "[]"),
            "challenges": json.loads(scene.challenges_json or "[]"),
            "characters_present": json.loads(scene.characters_present_json or "[]"),
            "show_picture": scene.show_picture,
            "has_map": scene.has_map,
            "tactical_map": json.loads(scene.tactical_map_json or "{}"),
        }

        # Select template based on role
        if role == "viewscreen":
            template = "scene_viewscreen.html"
        elif role == "gm":
            template = "scene_gm.html"
        else:
            template = "scene_player.html"

        return render_template(
            template,
            scene=scene_data,
            scene_record=scene,
            campaign=campaign,
            role=role,
        )
    finally:
        session.close()


@scenes_bp.route("/<int:scene_id>/edit", methods=["GET", "POST"])
def edit_scene(scene_id: int):
    """Edit a scene (GM only)."""
    session = get_session()
    try:
        scene = session.query(SceneRecord).filter_by(id=scene_id).first()
        if not scene:
            flash("Scene not found")
            return redirect(url_for("campaigns.gm_home"))

        # Verify GM status
        session_token = request.cookies.get("sta_session_token")
        gm = (
            session.query(CampaignPlayerRecord)
            .filter_by(campaign_id=scene.campaign_id, is_gm=True)
            .first()
        )

        if not gm or session_token != gm.session_token:
            flash("GM access required")
            return redirect(url_for("campaigns.gm_home"))

        campaign = session.query(CampaignRecord).filter_by(id=scene.campaign_id).first()

        if request.method == "POST":
            scene.name = request.form.get("name", scene.name)
            scene.stardate = request.form.get("stardate") or None
            scene.scene_picture_url = request.form.get("scene_picture_url") or None

            traits_text = request.form.get("scene_traits", "")
            scene.scene_traits_json = (
                json.dumps([t.strip() for t in traits_text.split(",") if t.strip()])
                if traits_text
                else "[]"
            )

            session.commit()
            flash("Scene updated")
            return redirect(
                url_for(
                    "campaigns.campaign_dashboard", campaign_id=campaign.campaign_id
                )
            )

        # GET - show form
        scene_data = {
            "id": scene.id,
            "name": scene.name,
            "scene_type": scene.scene_type,
            "status": scene.status,
            "stardate": scene.stardate,
            "scene_picture_url": scene.scene_picture_url,
            "scene_traits": json.loads(scene.scene_traits_json or "[]"),
            "challenges": json.loads(scene.challenges_json or "[]"),
        }

        return render_template(
            "scene_edit.html",
            scene=scene_data,
            scene_record=scene,
            campaign=campaign,
        )
    finally:
        session.close()
