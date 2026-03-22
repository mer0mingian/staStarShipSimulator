"""UI page routes using Jinja2 templates."""

from fastapi import APIRouter, Depends, Request, Query, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.templating import Jinja2Templates

from sta.database.async_db import get_db
from sta.database.schema import (
    CampaignRecord,
    CampaignPlayerRecord,
    SceneRecord,
    EncounterRecord,
    CampaignShipRecord,
    StarshipRecord,
    CharacterRecord,
)
from werkzeug.security import check_password_hash

templates = Jinja2Templates(directory="sta/web/templates")

ui_router = APIRouter()


@ui_router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@ui_router.get("/player/home", response_class=HTMLResponse)
async def player_home(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(CampaignRecord).filter(CampaignRecord.is_active)
    result = await db.execute(stmt)
    all_campaigns = result.scalars().all()

    campaigns = [
        {"campaign_id": c.campaign_id, "name": c.name, "description": c.description}
        for c in all_campaigns
    ]

    return templates.TemplateResponse(
        request,
        "player_home.html",
        {
            "campaigns": campaigns,
            "my_campaigns": [],
        },
    )


@ui_router.get("/gm", response_class=HTMLResponse)
async def gm_home(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(CampaignRecord).filter(CampaignRecord.is_active)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "gm_home.html",
        {
            "my_campaigns": [
                {
                    "campaign_id": c.campaign_id,
                    "name": c.name,
                    "description": c.description,
                }
                for c in campaigns
            ],
            "other_campaigns": [],
        },
    )


@ui_router.get("/gm/{campaign_id}/login", response_class=HTMLResponse)
async def gm_login_page(
    campaign_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return templates.TemplateResponse(
        request,
        "gm_login.html",
        {
            "campaign": {"campaign_id": campaign.campaign_id, "name": campaign.name},
            "error": None,
        },
    )


@ui_router.post("/gm/{campaign_id}/login")
async def gm_login_submit(
    campaign_id: str,
    request: Request,
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not campaign.gm_password_hash or not check_password_hash(
        campaign.gm_password_hash, password
    ):
        return templates.TemplateResponse(
            request,
            "gm_login.html",
            {
                "campaign": {
                    "campaign_id": campaign.campaign_id,
                    "name": campaign.name,
                    "description": campaign.description,
                    "enemy_turn_multiplier": getattr(
                        campaign, "enemy_turn_multiplier", None
                    ),
                },
                "error": "Invalid password",
            },
        )

    stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm,
    )
    result = await db.execute(stmt)
    gm_player = result.scalars().first()

    response = RedirectResponse(url=f"/campaigns/{campaign_id}", status_code=302)
    if gm_player and gm_player.session_token:
        response.set_cookie(
            key="sta_session_token",
            value=gm_player.session_token,
            httponly=True,
            max_age=60 * 60 * 24 * 30,
        )
    return response


@ui_router.get("/campaigns", response_class=HTMLResponse)
async def campaign_list(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(CampaignRecord).filter(CampaignRecord.is_active)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "campaign_list.html",
        {
            "campaigns": [
                {
                    "campaign_id": c.campaign_id,
                    "name": c.name,
                    "description": c.description,
                }
                for c in campaigns
            ],
        },
    )


@ui_router.get("/campaigns/new", response_class=HTMLResponse)
async def new_campaign_page(request: Request):
    return templates.TemplateResponse(request, "campaign_new.html", {})


@ui_router.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
async def campaign_dashboard(
    campaign_id: str,
    request: Request,
    sta_session_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    is_gm = False
    current_player = None

    if sta_session_token:
        player_stmt = select(CampaignPlayerRecord).filter(
            CampaignPlayerRecord.campaign_id == campaign.id,
            CampaignPlayerRecord.session_token == sta_session_token,
        )
        player_result = await db.execute(player_stmt)
        player = player_result.scalars().first()
        if player:
            is_gm = player.is_gm
            current_player = player

    players_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id
    )
    players_result = await db.execute(players_stmt)
    players = players_result.scalars().all()

    ships_stmt = select(CampaignShipRecord).filter(
        CampaignShipRecord.campaign_id == campaign.id
    )
    ships_result = await db.execute(ships_stmt)
    ships = ships_result.scalars().all()

    active_ship = None
    if campaign.active_ship_id:
        ship_stmt = select(StarshipRecord).filter(
            StarshipRecord.id == campaign.active_ship_id
        )
        ship_result = await db.execute(ship_stmt)
        active_ship = ship_result.scalars().first()

    scenes_stmt = select(SceneRecord).filter(SceneRecord.campaign_id == campaign.id)
    scenes_result = await db.execute(scenes_stmt)
    scenes = scenes_result.scalars().all()

    draft_scenes = [s for s in scenes if s.status == "draft"]
    completed_scenes = [s for s in scenes if s.status == "completed"]

    active_scene_data = None
    active_scene = next((s for s in scenes if s.status == "active"), None)
    if active_scene:
        active_scene_data = active_scene

    encounters_stmt = select(EncounterRecord).filter(
        EncounterRecord.campaign_id == campaign.id
    )
    encounters_result = await db.execute(encounters_stmt)
    encounters = encounters_result.scalars().all()

    active_encounter = next((e for e in encounters if e.status == "active"), None)
    draft_encounters = [e for e in encounters if e.status == "draft"]
    completed_encounters = [e for e in encounters if e.status == "completed"]

    return templates.TemplateResponse(
        request,
        "campaign_dashboard.html",
        {
            "campaign": {
                "campaign_id": campaign.campaign_id,
                "name": campaign.name,
                "description": campaign.description,
            },
            "is_gm": is_gm,
            "current_player": current_player,
            "players": [{"id": p.id, "player_name": p.player_name} for p in players],
            "ships": list(ships),
            "active_ship": active_ship,
            "draft_scenes": draft_scenes,
            "completed_scenes": completed_scenes,
            "active_scene_data": active_scene_data,
            "active_encounter": active_encounter,
            "draft_encounters": draft_encounters,
            "completed_encounters": completed_encounters,
            "flash_message": None,
        },
    )


@ui_router.get("/campaigns/{campaign_id}/player", response_class=HTMLResponse)
async def player_dashboard_page(
    campaign_id: str,
    request: Request,
    sta_session_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    player = None
    if sta_session_token:
        player_stmt = select(CampaignPlayerRecord).filter(
            CampaignPlayerRecord.campaign_id == campaign.id,
            CampaignPlayerRecord.session_token == sta_session_token,
            not CampaignPlayerRecord.is_gm,
        )
        player_result = await db.execute(player_stmt)
        player = player_result.scalars().first()

    character = None
    if player:
        char_stmt = select(CharacterRecord).filter(
            CharacterRecord.id == player.character_id
        )
        char_result = await db.execute(char_stmt)
        character = char_result.scalars().first()

    encounters_stmt = select(EncounterRecord).filter(
        EncounterRecord.campaign_id == campaign.id,
        EncounterRecord.status == "active",
    )
    encounters_result = await db.execute(encounters_stmt)
    active_encounter = encounters_result.scalars().first()

    return templates.TemplateResponse(
        request,
        "player_dashboard.html",
        {
            "campaign": {"campaign_id": campaign.campaign_id, "name": campaign.name},
            "player": player,
            "character": character,
            "active_encounter": active_encounter,
            "flash_message": None,
        },
    )


@ui_router.get("/scenes/new", response_class=HTMLResponse)
async def new_scene_page(request: Request, campaign_id: str = Query(None)):
    return templates.TemplateResponse(
        request,
        "new_scene.html",
        {
            "campaign": {"campaign_id": campaign_id, "name": "Campaign"},
        },
    )


@ui_router.get("/encounters/new", response_class=HTMLResponse)
async def new_encounter_page(request: Request, campaign_id: str = Query(None)):
    return templates.TemplateResponse(
        request,
        "deprecated.html",
        {
            "title": "Encounter Creation Deprecated",
            "message": "Standalone encounter creation has been deprecated. "
            "Encounters are now created via Scene activation.",
            "migration_guide": [
                "1. Create a Scene with scene_type='starship_encounter' or 'personal_encounter'",
                "2. Add ships/participants to the scene",
                "3. Set scene traits via the scene editor",
                "4. Configure encounter settings via the scene config",
                "5. Activate the scene to start the encounter",
            ],
            "back_url": f"/campaigns/{campaign_id}/" if campaign_id else "/",
        },
    )


@ui_router.get("/encounters/{encounter_id}", response_class=HTMLResponse)
async def combat_view(
    encounter_id: int,
    request: Request,
    role: str = Query("player"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EncounterRecord).filter(EncounterRecord.id == encounter_id)
    result = await db.execute(stmt)
    encounter = result.scalars().first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.id == encounter.campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if role == "gm":
        return templates.TemplateResponse(
            request,
            "combat_gm.html",
            {
                "encounter": encounter,
                "campaign": {"campaign_id": campaign.campaign_id, "name": campaign.name}
                if campaign
                else {"campaign_id": "", "name": ""},
                "flash_message": None,
            },
        )
    elif role == "viewscreen":
        return templates.TemplateResponse(
            request,
            "combat_viewscreen.html",
            {
                "encounter": encounter,
                "campaign": {"campaign_id": campaign.campaign_id, "name": campaign.name}
                if campaign
                else {"campaign_id": "", "name": ""},
            },
        )
    else:
        return templates.TemplateResponse(
            request,
            "combat_player.html",
            {
                "encounter": encounter,
                "campaign": {"campaign_id": campaign.campaign_id, "name": campaign.name}
                if campaign
                else {"campaign_id": "", "name": ""},
                "flash_message": None,
            },
        )


@ui_router.get("/encounters/{encounter_id}/edit", response_class=HTMLResponse)
async def edit_encounter_page(
    encounter_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    stmt = select(EncounterRecord).filter(EncounterRecord.id == encounter_id)
    result = await db.execute(stmt)
    encounter = result.scalars().first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.id == encounter.campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    return templates.TemplateResponse(
        request,
        "edit_encounter.html",
        {
            "encounter": encounter,
            "campaign": {"campaign_id": campaign.campaign_id, "name": campaign.name}
            if campaign
            else {"campaign_id": "", "name": ""},
            "flash_message": None,
        },
    )
