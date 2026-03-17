"""Campaign routes for campaign management (FastAPI)."""

import json
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Form,
    Query,
    Cookie,
    Body,
)
from fastapi.responses import JSONResponse

from werkzeug.security import generate_password_hash, check_password_hash

from sta.database.async_db import get_db
from sta.database.schema import (
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
from sta.database.vtt_schema import (
    VTTCharacterRecord,
    VTTShipRecord,
)

campaigns_router = APIRouter(prefix="/campaigns", tags=["campaigns"])

DEFAULT_GM_PASSWORD = "ENGAGE1"


async def _get_current_player(
    campaign_id: int,
    sta_session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[CampaignPlayerRecord]:
    """Get current player from session token."""
    if not sta_session_token:
        return None

    stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign_id,
        or_(
            CampaignPlayerRecord.token_expires_at == None,
            CampaignPlayerRecord.token_expires_at > datetime.now(),
        ),
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def _require_gm_auth(
    campaign_id: int,
    sta_session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> CampaignPlayerRecord:
    """Verify GM authentication for a campaign."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign_id,
        CampaignPlayerRecord.is_gm == True,
    )
    result = await db.execute(stmt)
    gm_player = result.scalars().first()

    if not gm_player or sta_session_token != gm_player.session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    return gm_player


# =============================================================================
# Campaign CRUD
# =============================================================================


@campaigns_router.post("/new")
async def new_campaign(
    name: str = Form("New Campaign"),
    description: str = Form(""),
    gm_name: str = Form("Game Master"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new campaign."""
    campaign = CampaignRecord(
        campaign_id=str(uuid.uuid4())[:8],
        name=name,
        description=description,
        gm_password_hash=generate_password_hash(DEFAULT_GM_PASSWORD),
    )
    db.add(campaign)
    await db.flush()

    gm_token = secrets.token_urlsafe(32)
    gm_player = CampaignPlayerRecord(
        campaign_id=campaign.id,
        player_name=gm_name,
        session_token=gm_token,
        token_expires_at=datetime.now() + timedelta(days=30),
        is_gm=True,
        position="gm",
    )
    db.add(gm_player)
    await db.commit()
    await db.refresh(campaign)

    return {
        "campaign_id": campaign.campaign_id,
        "campaign_name": campaign.name,
        "gm_token": gm_token,
    }


@campaigns_router.get("/api/campaigns")
async def api_list_campaigns(db: AsyncSession = Depends(get_db)):
    """API: List all active campaigns."""
    stmt = select(CampaignRecord).filter(CampaignRecord.is_active == True)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    return [
        {
            "id": c.id,
            "campaign_id": c.campaign_id,
            "name": c.name,
            "description": c.description,
            "has_active_ship": c.active_ship_id is not None,
        }
        for c in campaigns
    ]


@campaigns_router.get("/api/campaign/{campaign_id}")
async def api_get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """API: Get campaign details."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {
        "id": campaign.id,
        "campaign_id": campaign.campaign_id,
        "name": campaign.name,
        "description": campaign.description,
        "active_ship_id": campaign.active_ship_id,
        "is_active": campaign.is_active,
    }


@campaigns_router.put("/api/campaign/{campaign_id}")
async def api_update_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    enemy_turn_multiplier: Optional[float] = Form(None),
):
    """API: Update campaign details."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if name is not None:
        campaign.name = name
    if description is not None:
        campaign.description = description

    if enemy_turn_multiplier is not None:
        if not sta_session_token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        gm_stmt = select(CampaignPlayerRecord).filter(
            CampaignPlayerRecord.session_token == sta_session_token,
            CampaignPlayerRecord.campaign_id == campaign.id,
            CampaignPlayerRecord.is_gm == True,
        )
        gm_result = await db.execute(gm_stmt)
        gm = gm_result.scalars().first()

        if not gm:
            raise HTTPException(
                status_code=403, detail="Only the GM can change combat settings"
            )

        multiplier = float(enemy_turn_multiplier)
        if multiplier < 0.1 or multiplier > 2.0:
            raise HTTPException(
                status_code=400, detail="Turn multiplier must be between 0.1 and 2.0"
            )

        campaign.enemy_turn_multiplier = multiplier

    await db.commit()
    return {"success": True}


@campaigns_router.delete("/api/campaign/{campaign_id}")
async def api_delete_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """API: Delete (deactivate) campaign. Requires GM authentication."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="Only the GM can delete campaigns")

    campaign.is_active = False
    await db.commit()
    return {"success": True}


# =============================================================================
# Player Management API
# =============================================================================


@campaigns_router.get("/api/campaign/{campaign_id}/players")
async def api_list_players(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """API: List players in campaign."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    players_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_active == True,
    )
    players_result = await db.execute(players_stmt)
    players = players_result.scalars().all()

    return [
        {
            "id": p.id,
            "player_name": p.player_name,
            "position": p.position,
            "is_gm": p.is_gm,
            "character_id": p.character_id,
        }
        for p in players
    ]


@campaigns_router.post("/api/campaign/{campaign_id}/players")
async def api_create_player(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
    action: str = Form("generate"),
    name: str = Form("New Player"),
):
    """API: Create a new player."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="Only GM can create players")

    character_id = None
    player_name = name

    if action == "generate":
        from sta.generators import generate_character

        char = generate_character()
        char_record = CharacterRecord.from_model(char)
        db.add(char_record)
        await db.flush()
        character_id = char_record.id
        player_name = char.name

    placeholder_token = f"unclaimed_{uuid.uuid4()}"
    new_player = CampaignPlayerRecord(
        campaign_id=campaign.id,
        character_id=character_id,
        player_name=player_name,
        session_token=placeholder_token,
        position="unassigned",
        is_gm=False,
        is_active=True,
    )
    db.add(new_player)
    await db.commit()
    await db.refresh(new_player)

    return {
        "success": True,
        "player": {
            "id": new_player.id,
            "player_name": new_player.player_name,
            "character_id": new_player.character_id,
        },
    }


@campaigns_router.get("/api/campaign/{campaign_id}/player/{player_id}")
async def api_get_player(
    campaign_id: str, player_id: int, db: AsyncSession = Depends(get_db)
):
    """API: Get player details with character data."""
    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    player_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.id == player_id,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    player_result = await db.execute(player_stmt)
    player = player_result.scalars().first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    character_data = None
    if player.character_id:
        char_stmt = select(CharacterRecord).filter(
            CharacterRecord.id == player.character_id
        )
        char_result = await db.execute(char_stmt)
        char_record = char_result.scalars().first()
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

    return {
        "id": player.id,
        "player_name": player.player_name,
        "position": player.position,
        "is_gm": player.is_gm,
        "character_id": player.character_id,
        "character": character_data,
    }


@campaigns_router.put("/api/campaign/{campaign_id}/player/{player_id}/position")
async def api_update_player_position(
    campaign_id: str,
    player_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
    position: Optional[str] = Form(None),
):
    """API: Update player's bridge position."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    current_user_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    current_user_result = await db.execute(current_user_stmt)
    current_user = current_user_result.scalars().first()

    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not current_user.is_gm and current_user.id != player_id:
        raise HTTPException(status_code=403, detail="Can only update your own position")

    player_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.id == player_id,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    player_result = await db.execute(player_stmt)
    player = player_result.scalars().first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    active_encounter_stmt = select(EncounterRecord).filter(
        EncounterRecord.campaign_id == campaign.id,
        EncounterRecord.status == "active",
    )
    active_encounter_result = await db.execute(active_encounter_stmt)
    active_encounter = active_encounter_result.scalars().first()

    if active_encounter and not current_user.is_gm and player.position != "unassigned":
        raise HTTPException(status_code=403, detail="Position locked during combat")

    if position and position != "gm" and position != "unassigned":
        existing_stmt = select(CampaignPlayerRecord).filter(
            CampaignPlayerRecord.campaign_id == campaign.id,
            CampaignPlayerRecord.id != player_id,
            CampaignPlayerRecord.is_active == True,
            CampaignPlayerRecord.is_gm == False,
            CampaignPlayerRecord.position == position,
        )
        existing_result = await db.execute(existing_stmt)
        existing_player = existing_result.scalars().first()

        if existing_player:
            raise HTTPException(
                status_code=400,
                detail=f"Position '{position}' is already taken by {existing_player.player_name}",
            )

    if position is not None:
        player.position = position

    await db.commit()
    return {"success": True}


@campaigns_router.delete("/api/campaign/{campaign_id}/player/{player_id}")
async def api_remove_player(
    campaign_id: str,
    player_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """API: Remove player from campaign (GM only)."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="Only GM can remove players")

    player_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.id == player_id,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    player_result = await db.execute(player_stmt)
    player = player_result.scalars().first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.is_gm:
        raise HTTPException(status_code=400, detail="Cannot remove GM")

    player.is_active = False
    await db.commit()
    return {"success": True}


# =============================================================================
# Scene Management Helper Endpoints
# =============================================================================


@campaigns_router.get("/{campaign_id}/characters/available")
async def get_campaign_available_characters(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get characters available to add to scenes (PCs and NPCs)."""
    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm_player = gm_result.scalars().first()

    if not gm_player or sta_session_token != gm_player.session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    result = []

    campaign_players_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == False,
    )
    campaign_players_result = await db.execute(campaign_players_stmt)
    campaign_players = campaign_players_result.scalars().all()

    pc_char_ids = set()
    for cp in campaign_players:
        if cp.vtt_character_id:
            char_stmt = select(VTTCharacterRecord).filter(
                VTTCharacterRecord.id == cp.vtt_character_id
            )
            char_result = await db.execute(char_stmt)
            char = char_result.scalars().first()
            if char:
                result.append(
                    {
                        "id": char.id,
                        "name": char.name,
                        "type": "pc",
                        "player_id": cp.id,
                        "player_name": cp.player_name,
                    }
                )
                pc_char_ids.add(char.id)

    npc_stmt = select(VTTCharacterRecord).filter(
        VTTCharacterRecord.campaign_id == campaign.id
    )
    if pc_char_ids:
        npc_stmt = npc_stmt.filter(~VTTCharacterRecord.id.in_(pc_char_ids))

    npc_result = await db.execute(npc_stmt)
    npc_chars = npc_result.scalars().all()

    for char in npc_chars:
        result.append(
            {
                "id": char.id,
                "name": char.name,
                "type": "npc",
                "player_id": None,
                "player_name": None,
            }
        )

    return result


@campaigns_router.get("/{campaign_id}/ships/available")
async def get_campaign_available_ships(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get ships available to add to scenes."""
    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm_player = gm_result.scalars().first()

    if not gm_player or sta_session_token != gm_player.session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    campaign_ships_stmt = select(CampaignShipRecord).filter(
        CampaignShipRecord.campaign_id == campaign.id
    )
    campaign_ships_result = await db.execute(campaign_ships_stmt)
    campaign_ships = campaign_ships_result.scalars().all()

    result = []
    for cs in campaign_ships:
        ship_stmt = select(VTTShipRecord).filter(VTTShipRecord.id == cs.ship_id)
        ship_result = await db.execute(ship_stmt)
        ship = ship_result.scalars().first()
        if ship:
            result.append({"id": ship.id, "name": ship.name})

    return result


# =============================================================================
# VTT Character/Ship Linking
# =============================================================================


@campaigns_router.post("/api/campaign/{campaign_id}/link-character")
async def link_vtt_character_to_player(
    campaign_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Link a VTT character to a campaign player (GM only)."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    player_id = data.get("player_id")
    vtt_character_id = data.get("vtt_character_id")

    if player_id is None:
        raise HTTPException(status_code=400, detail="player_id is required")

    if vtt_character_id is None:
        raise HTTPException(status_code=400, detail="vtt_character_id is required")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="GM authentication required")

    player_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.id == player_id,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    player_result = await db.execute(player_stmt)
    player = player_result.scalars().first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    player.vtt_character_id = vtt_character_id
    await db.commit()

    return {"success": True, "vtt_character_id": vtt_character_id}


@campaigns_router.post("/api/campaign/{campaign_id}/link-ship")
async def link_vtt_ship_to_campaign(
    campaign_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Link a VTT ship to a campaign ship (GM only)."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    campaign_ship_id = data.get("campaign_ship_id")
    vtt_ship_id = data.get("vtt_ship_id")

    if campaign_ship_id is None:
        raise HTTPException(status_code=400, detail="campaign_ship_id is required")

    if vtt_ship_id is None:
        raise HTTPException(status_code=400, detail="vtt_ship_id is required")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="GM authentication required")

    ship_stmt = select(CampaignShipRecord).filter(
        CampaignShipRecord.id == campaign_ship_id,
        CampaignShipRecord.campaign_id == campaign.id,
    )
    ship_result = await db.execute(ship_stmt)
    campaign_ship = ship_result.scalars().first()

    if not campaign_ship:
        raise HTTPException(status_code=404, detail="Campaign ship not found")

    campaign_ship.vtt_ship_id = vtt_ship_id
    await db.commit()

    return {"success": True, "vtt_ship_id": vtt_ship_id}


# =============================================================================
# Random Campaign Generation
# =============================================================================


@campaigns_router.post("/api/generate-random")
async def api_generate_random_campaign(db: AsyncSession = Depends(get_db)):
    """API: Generate a random campaign with ship and encounter ready to go."""
    from sta.generators.starship import generate_enemy_ship
    from sta.models.enums import CrewQuality
    import random

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

    campaign_name = random.choice(campaign_names)

    campaign = CampaignRecord(
        campaign_id=str(uuid.uuid4())[:8],
        name=campaign_name,
        description="Quick-start campaign with ship and encounter ready",
        gm_password_hash=generate_password_hash(DEFAULT_GM_PASSWORD),
    )
    db.add(campaign)
    await db.flush()

    gm_token = secrets.token_urlsafe(32)
    gm_player = CampaignPlayerRecord(
        campaign_id=campaign.id,
        player_name="Q",
        session_token=gm_token,
        token_expires_at=datetime.now() + timedelta(days=30),
        is_gm=True,
        position="gm",
    )
    db.add(gm_player)

    from sta.generators import generate_starship, generate_character

    ship = generate_starship()
    ship_record = StarshipRecord.from_model(ship)
    db.add(ship_record)
    await db.flush()

    campaign_ship = CampaignShipRecord(
        campaign_id=campaign.id,
        ship_id=ship_record.id,
    )
    db.add(campaign_ship)
    campaign.active_ship_id = ship_record.id

    char = generate_character()
    char_record = CharacterRecord.from_model(char)
    db.add(char_record)
    await db.flush()

    enemy = generate_enemy_ship(
        difficulty="standard", crew_quality=CrewQuality.TALENTED
    )
    enemy_record = StarshipRecord.from_model(enemy)
    db.add(enemy_record)
    await db.flush()

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
    db.add(encounter)
    await db.commit()

    return {
        "success": True,
        "campaign_id": campaign.campaign_id,
        "campaign_name": campaign_name,
        "ship_name": ship.name,
    }


# =============================================================================
# Campaign Resource Management
# =============================================================================


@campaigns_router.get("/api/campaign/{campaign_id}/resources")
async def get_campaign_resources(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get campaign momentum and threat resources."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {
        "momentum": campaign.momentum or 0,
        "threat": campaign.threat or 0,
        "momentum_max": 6,
    }


@campaigns_router.post("/api/campaign/{campaign_id}/momentum")
async def update_campaign_momentum(
    campaign_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Update campaign momentum pool."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    amount = data.get("amount", 0)
    campaign.momentum = max(0, min(6, (campaign.momentum or 0) + amount))
    await db.commit()

    return {"momentum": campaign.momentum}


@campaigns_router.post("/api/campaign/{campaign_id}/threat")
async def update_campaign_threat(
    campaign_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Update campaign threat level."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    amount = data.get("amount", 0)
    campaign.threat = max(0, (campaign.threat or 0) + amount)
    await db.commit()

    return {"threat": campaign.threat}


# Campaign Scene Management


@campaigns_router.post("/api/campaign/{campaign_id}/scenes")
async def create_scene_for_campaign(
    campaign_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a new scene for a campaign."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    scene = SceneRecord(
        campaign_id=campaign.id,
        name=data.get("name", "New Scene"),
        description=data.get("description"),
        scene_type=data.get("scene_type", "narrative"),
        status="draft",
        stardate=data.get("stardate"),
        scene_traits_json=json.dumps(data.get("scene_traits", [])),
        challenges_json=json.dumps(data.get("challenges", [])),
    )
    db.add(scene)
    await db.commit()

    return {
        "success": True,
        "scene_id": scene.id,
        "name": scene.name,
    }


@campaigns_router.get("/api/campaign/{campaign_id}/scenes/transition-options")
async def get_scene_transition_options(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get scene transition options for a campaign."""
    from sta.database.schema import SceneRecord

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm_player = gm_result.scalars().first()

    if not gm_player or sta_session_token != gm_player.session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    connected_stmt = select(SceneRecord).filter(
        SceneRecord.campaign_id == campaign.id,
        SceneRecord.status == "draft",
    )
    connected_result = await db.execute(connected_stmt)
    connected_scenes = [
        {"id": s.id, "name": s.name, "status": s.status}
        for s in connected_result.scalars().all()
    ]

    ready_stmt = select(SceneRecord).filter(
        SceneRecord.campaign_id == campaign.id,
        SceneRecord.status == "ready",
    )
    ready_result = await db.execute(ready_stmt)
    ready_scenes = [
        {"id": s.id, "name": s.name, "gm_short_description": s.gm_short_description}
        for s in ready_result.scalars().all()
    ]

    return {
        "connected_scenes": connected_scenes,
        "ready_scenes": ready_scenes,
        "can_create_new": True,
    }


@campaigns_router.delete("/api/scene/{scene_id}")
async def delete_scene(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scene."""
    from sta.database.schema import SceneRecord

    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if scene.status == "active":
        raise HTTPException(status_code=400, detail="Cannot delete active scene")

    await db.delete(scene)
    await db.commit()

    return {"success": True}


@campaigns_router.put("/api/scene/{scene_id}/status")
async def update_scene_status(
    scene_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Update scene status."""
    from sta.database.schema import SceneRecord

    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if "status" in data:
        scene.status = data["status"]

    await db.commit()

    return {
        "success": True,
        "status": scene.status,
    }


@campaigns_router.put("/api/scene/{scene_id}/convert")
async def convert_scene_type(
    scene_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Convert a scene to a different type."""
    from sta.database.schema import SceneRecord

    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.id == scene.campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm_player = gm_result.scalars().first()

    if not gm_player or sta_session_token != gm_player.session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    old_type = scene.scene_type
    new_type = data.get("scene_type")

    if not new_type:
        raise HTTPException(status_code=400, detail="scene_type is required")

    if new_type == "starship_encounter" and not campaign.active_ship_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot convert to starship_encounter without active ship",
        )

    if new_type == "starship_encounter":
        scene.scene_type = "starship_encounter"
        scene.has_map = True
    elif new_type == "narrative":
        scene.scene_type = "narrative"
    elif new_type == "social_encounter":
        scene.scene_type = "social_encounter"
        scene.has_map = False
    elif new_type == "personal_encounter":
        scene.scene_type = "personal_encounter"

    await db.commit()

    return {
        "success": True,
        "old_type": old_type,
        "new_type": scene.scene_type,
    }


# =============================================================================
# Character Claiming Pages
# =============================================================================


@campaigns_router.get("/{campaign_id}/join")
async def campaign_join_page(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Display the character claiming join page."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    players_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == False,
    )
    players_result = await db.execute(players_stmt)
    players = players_result.scalars().all()

    html = "<html><body><h1>Join Campaign</h1><ul>"
    for player in players:
        if player.session_token and not player.session_token.startswith("unclaimed_"):
            continue
        html += f'<li><a href="/campaigns/{campaign_id}/claim/{player.id}">{player.player_name}</a></li>'
    html += "</ul></body></html>"

    return {"content": html, "content_type": "text/html"}


@campaigns_router.post("/{campaign_id}/join")
async def claim_character(
    campaign_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Claim a character for a player."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        request_data = await request.json()
    elif (
        "application/x-www-form-urlencoded" in content_type
        or "multipart/form-data" in content_type
    ):
        form = await request.form()
        request_data = dict(form)
    else:
        request_data = {}
    print(f"DEBUG: content_type={content_type}, request_data={request_data}")

    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    player_id = request_data.get("player_id")
    if not player_id:
        raise HTTPException(status_code=400, detail="player_id required")

    # Convert to int if string
    try:
        player_id = int(player_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="player_id must be an integer")

    player_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.id == player_id,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    player_result = await db.execute(player_stmt)
    player = player_result.scalars().first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.is_gm:
        raise HTTPException(status_code=400, detail="GM cannot be claimed")

    new_token = secrets.token_urlsafe(32)
    player.session_token = new_token
    player.token_expires_at = datetime.now() + timedelta(days=30)
    await db.commit()

    return {
        "success": True,
        "session_token": new_token,
        "redirect": f"/campaigns/{campaign_id}/dashboard",
    }


@campaigns_router.get("/{campaign_id}/switch-character")
async def switch_character_page(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Display the character switch page."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    players_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == False,
    )
    players_result = await db.execute(players_stmt)
    players = players_result.scalars().all()

    html = "<html><body><h1>Switch Character</h1><ul>"
    for player in players:
        html += f'<li><a href="/campaigns/{campaign_id}/claim/{player.id}">{player.player_name}</a></li>'
    html += "</ul></body></html>"

    return {"content": html, "content_type": "text/html"}


@campaigns_router.get("/api/campaign/{campaign_id}/npcs")
async def list_campaign_npcs(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List NPCs in a campaign."""
    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign_npcs_stmt = select(CampaignNPCRecord).filter(
        CampaignNPCRecord.campaign_id == campaign.id
    )
    campaign_npcs_result = await db.execute(campaign_npcs_stmt)
    campaign_npcs = campaign_npcs_result.scalars().all()

    result = []
    for cnpc in campaign_npcs:
        npc_stmt = select(NPCRecord).filter(NPCRecord.id == cnpc.npc_id)
        npc_result = await db.execute(npc_stmt)
        npc = npc_result.scalars().first()
        if npc:
            result.append(
                {
                    "id": cnpc.id,
                    "npc_id": npc.id,
                    "name": npc.name,
                    "npc_type": npc.npc_type,
                    "affiliation": npc.affiliation,
                    "is_visible": cnpc.is_visible_to_players,
                }
            )

    return result


@campaigns_router.post("/api/campaign/{campaign_id}/npcs")
async def add_npc_to_campaign(
    campaign_id: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Add an NPC to a campaign."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="Only GM can add NPCs")

    action = data.get("action", "create")

    if action == "create":
        from sta.generators import generate_character

        char = generate_character()
        char.name = data.get("name", char.name)
        char_record = CharacterRecord.from_model(char)
        db.add(char_record)
        await db.flush()

        campaign_npc = CampaignNPCRecord(
            campaign_id=campaign.id,
            npc_id=char_record.id,
            is_visible_to_players=False,
        )
        db.add(campaign_npc)
        await db.commit()

        return {
            "success": True,
            "npc_id": char_record.id,
            "name": char_record.name,
        }

    return {"success": False, "detail": "Unknown action"}


@campaigns_router.delete("/api/campaign/{campaign_id}/npcs/{cnpc_id}")
async def remove_npc_from_campaign(
    campaign_id: str,
    cnpc_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Remove an NPC from a campaign."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="Only GM can remove NPCs")

    campaign_npc_stmt = select(CampaignNPCRecord).filter(
        CampaignNPCRecord.id == cnpc_id,
        CampaignNPCRecord.campaign_id == campaign.id,
    )
    campaign_npc_result = await db.execute(campaign_npc_stmt)
    campaign_npc = campaign_npc_result.scalars().first()

    if not campaign_npc:
        raise HTTPException(status_code=404, detail="NPC not found in campaign")

    await db.delete(campaign_npc)
    await db.commit()

    return {"success": True}


@campaigns_router.put("/api/campaign/{campaign_id}/npcs/{cnpc_id}/visibility")
async def toggle_npc_visibility(
    campaign_id: str,
    cnpc_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Toggle NPC visibility in a campaign."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    gm_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
        CampaignPlayerRecord.is_gm == True,
    )
    gm_result = await db.execute(gm_stmt)
    gm = gm_result.scalars().first()

    if not gm:
        raise HTTPException(status_code=403, detail="Only GM can toggle visibility")

    campaign_npc_stmt = select(CampaignNPCRecord).filter(
        CampaignNPCRecord.id == cnpc_id,
        CampaignNPCRecord.campaign_id == campaign.id,
    )
    campaign_npc_result = await db.execute(campaign_npc_stmt)
    campaign_npc = campaign_npc_result.scalars().first()

    if not campaign_npc:
        raise HTTPException(status_code=404, detail="NPC not found in campaign")

    is_visible = data.get("is_visible", True)
    campaign_npc.is_visible_to_players = is_visible
    await db.commit()

    return {"success": True, "is_visible": is_visible}


@campaigns_router.post("/api/campaign/{campaign_id}/refresh-token")
async def refresh_session_token(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Refresh a session token, extending its expiration."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    player_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    player_result = await db.execute(player_stmt)
    player = player_result.scalars().first()

    if not player:
        raise HTTPException(status_code=401, detail="Invalid token")

    if player.token_expires_at and player.token_expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Token has expired")

    new_token = secrets.token_urlsafe(32)
    player.session_token = new_token
    player.token_expires_at = datetime.now() + timedelta(days=30)
    await db.commit()

    response = JSONResponse(
        content={
            "success": True,
            "session_token": new_token,
            "expires_at": player.token_expires_at.isoformat(),
        }
    )
    response.set_cookie(
        key="sta_session_token",
        value=new_token,
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        samesite="lax",
    )
    return response


@campaigns_router.get("/{campaign_id}/player")
async def player_dashboard(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Player dashboard page."""
    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    player_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    player_result = await db.execute(player_stmt)
    player = player_result.scalars().first()

    if not player:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/", status_code=302)

    html = f"<html><body><h1>Player Dashboard</h1>"
    html += f"<p>Campaign: {campaign.name}</p>"
    html += f"<p>Player: {player.player_name}</p>"
    html += f"<p>Position: {player.position}</p>"
    html += "</body></html>"

    return {"content": html, "content_type": "text/html"}
