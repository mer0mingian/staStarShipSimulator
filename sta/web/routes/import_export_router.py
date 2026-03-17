"""Import/Export routes for VTT backup functionality (FastAPI)."""

import json
import uuid
import secrets
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Body,
    Cookie,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sta.database.async_db import get_db
from sta.database.schema import (
    CampaignRecord,
    CampaignPlayerRecord,
    CampaignShipRecord,
    CampaignNPCRecord,
    CharacterRecord,
    NPCRecord,
)
from sta.database.vtt_schema import (
    VTTCharacterRecord,
    VTTShipRecord,
)
from werkzeug.security import generate_password_hash

backup_router = APIRouter(prefix="/backup", tags=["backup"])

DEFAULT_GM_PASSWORD = "ENGAGE1"


def _serialize_character(char: VTTCharacterRecord) -> dict:
    """Serialize a VTTCharacterRecord to JSON for export."""
    return {
        "name": char.name,
        "species": char.species,
        "rank": char.rank,
        "role": char.role,
        "attributes": json.loads(char.attributes_json),
        "disciplines": json.loads(char.disciplines_json),
        "talents": json.loads(char.talents_json),
        "focuses": json.loads(char.focuses_json),
        "stress": char.stress,
        "stress_max": char.stress_max,
        "determination": char.determination,
        "determination_max": char.determination_max,
        "character_type": char.character_type,
        "pronouns": char.pronouns,
        "avatar_url": char.avatar_url,
        "description": char.description,
        "values": json.loads(char.values_json),
        "equipment": json.loads(char.equipment_json),
        "environment": char.environment,
        "upbringing": char.upbringing,
        "career_path": char.career_path,
        "is_visible_to_players": char.is_visible_to_players,
        "state": getattr(char, "state", "Ok"),
    }


def _serialize_ship(ship: VTTShipRecord) -> dict:
    """Serialize a VTTShipRecord to JSON for export."""
    return {
        "name": ship.name,
        "ship_class": ship.ship_class,
        "ship_registry": ship.ship_registry,
        "scale": ship.scale,
        "systems": json.loads(ship.systems_json),
        "departments": json.loads(ship.departments_json),
        "weapons": json.loads(ship.weapons_json),
        "talents": json.loads(ship.talents_json),
        "traits": json.loads(ship.traits_json),
        "breaches": json.loads(ship.breaches_json),
        "shields": ship.shields,
        "shields_max": ship.shields_max,
        "resistance": ship.resistance,
        "has_reserve_power": ship.has_reserve_power,
        "shields_raised": ship.shields_raised,
        "weapons_armed": ship.weapons_armed,
        "crew_quality": ship.crew_quality,
        "is_visible_to_players": ship.is_visible_to_players,
    }


def _serialize_campaign(campaign: CampaignRecord) -> dict:
    """Serialize a CampaignRecord to JSON for export."""
    return {
        "name": campaign.name,
        "description": campaign.description,
        "is_active": campaign.is_active,
        "enemy_turn_multiplier": campaign.enemy_turn_multiplier,
    }


@backup_router.get("/{campaign_id}")
async def export_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """Export full campaign data including characters, NPCs, and ships."""
    stmt = select(CampaignRecord).filter(CampaignRecord.campaign_id == campaign_id)
    result = await db.execute(stmt)
    campaign = result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign_players_stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.campaign_id == campaign.id,
    )
    campaign_players_result = await db.execute(campaign_players_stmt)
    campaign_players = campaign_players_result.scalars().all()

    characters = []
    npcs = []

    for player in campaign_players:
        if player.vtt_character_id:
            char_stmt = select(VTTCharacterRecord).filter(
                VTTCharacterRecord.id == player.vtt_character_id
            )
            char_result = await db.execute(char_stmt)
            char = char_result.scalars().first()
            if char:
                characters.append(_serialize_character(char))

    npc_stmt = select(VTTCharacterRecord).filter(
        VTTCharacterRecord.campaign_id == campaign.id,
        VTTCharacterRecord.character_type == "npc",
    )
    npc_result = await db.execute(npc_stmt)
    npc_chars = npc_result.scalars().all()

    for npc in npc_chars:
        npcs.append(_serialize_character(npc))

    campaign_ships_stmt = select(CampaignShipRecord).filter(
        CampaignShipRecord.campaign_id == campaign.id
    )
    campaign_ships_result = await db.execute(campaign_ships_stmt)
    campaign_ships = campaign_ships_result.scalars().all()

    ships = []
    for cs in campaign_ships:
        if cs.vtt_ship_id:
            ship_stmt = select(VTTShipRecord).filter(VTTShipRecord.id == cs.vtt_ship_id)
            ship_result = await db.execute(ship_stmt)
            ship = ship_result.scalars().first()
            if ship:
                ships.append(_serialize_ship(ship))

    return {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "characters": characters,
        "npcs": npcs,
        "ships": ships,
        "campaigns": [_serialize_campaign(campaign)],
    }


@backup_router.post("/import")
async def import_campaign(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    """Import campaign data from a backup JSON."""
    version = data.get("version")
    if not version:
        raise HTTPException(status_code=400, detail="Invalid backup: missing version")

    characters = data.get("characters", [])
    npcs = data.get("npcs", [])
    ships = data.get("ships", [])
    campaigns_data = data.get("campaigns", [])

    if not campaigns_data:
        raise HTTPException(
            status_code=400, detail="Invalid backup: missing campaign data"
        )

    campaign_data = campaigns_data[0]

    campaign = CampaignRecord(
        campaign_id=str(uuid.uuid4())[:8],
        name=campaign_data.get("name", "Imported Campaign"),
        description=campaign_data.get("description", ""),
        gm_password_hash=generate_password_hash(DEFAULT_GM_PASSWORD),
    )
    db.add(campaign)
    await db.flush()

    gm_token = secrets.token_urlsafe(32)
    gm_player = CampaignPlayerRecord(
        campaign_id=campaign.id,
        player_name="GM",
        session_token=gm_token,
        token_expires_at=datetime.now(),
        is_gm=True,
        position="gm",
    )
    db.add(gm_player)

    created_character_ids = []
    character_id_map = {}

    for char_data in characters:
        char = VTTCharacterRecord(
            name=char_data.get("name", "Unnamed Character"),
            species=char_data.get("species"),
            rank=char_data.get("rank"),
            role=char_data.get("role"),
            attributes_json=json.dumps(char_data.get("attributes", {})),
            disciplines_json=json.dumps(char_data.get("disciplines", {})),
            talents_json=json.dumps(char_data.get("talents", [])),
            focuses_json=json.dumps(char_data.get("focuses", [])),
            stress=char_data.get("stress", 0),
            stress_max=char_data.get("stress_max", 5),
            determination=char_data.get("determination", 0),
            determination_max=char_data.get("determination_max", 3),
            character_type=char_data.get("character_type", "support"),
            pronouns=char_data.get("pronouns"),
            avatar_url=char_data.get("avatar_url"),
            description=char_data.get("description"),
            values_json=json.dumps(char_data.get("values", [])),
            equipment_json=json.dumps(char_data.get("equipment", [])),
            environment=char_data.get("environment"),
            upbringing=char_data.get("upbringing"),
            career_path=char_data.get("career_path"),
            campaign_id=campaign.id,
            is_visible_to_players=char_data.get("is_visible_to_players", True),
        )
        db.add(char)
        await db.flush()
        created_character_ids.append(char.id)
        character_id_map[char_data.get("name")] = char.id

    for npc_data in npcs:
        npc = VTTCharacterRecord(
            name=npc_data.get("name", "Unnamed NPC"),
            species=npc_data.get("species"),
            rank=npc_data.get("rank"),
            role=npc_data.get("role"),
            attributes_json=json.dumps(npc_data.get("attributes", {})),
            disciplines_json=json.dumps(npc_data.get("disciplines", {})),
            talents_json=json.dumps(npc_data.get("talents", [])),
            focuses_json=json.dumps(npc_data.get("focuses", [])),
            stress=npc_data.get("stress", 0),
            stress_max=npc_data.get("stress_max", 5),
            determination=npc_data.get("determination", 0),
            determination_max=npc_data.get("determination_max", 3),
            character_type="npc",
            pronouns=npc_data.get("pronouns"),
            avatar_url=npc_data.get("avatar_url"),
            description=npc_data.get("description"),
            values_json=json.dumps(npc_data.get("values", [])),
            equipment_json=json.dumps(npc_data.get("equipment", [])),
            environment=npc_data.get("environment"),
            upbringing=npc_data.get("upbringing"),
            career_path=npc_data.get("career_path"),
            campaign_id=campaign.id,
            is_visible_to_players=npc_data.get("is_visible_to_players", True),
        )
        db.add(npc)
        await db.flush()
        created_character_ids.append(npc.id)

    created_ship_ids = []

    for ship_data in ships:
        ship = VTTShipRecord(
            name=ship_data.get("name", "Unnamed Ship"),
            ship_class=ship_data.get("ship_class", "Unknown"),
            ship_registry=ship_data.get("ship_registry"),
            scale=ship_data.get("scale", 4),
            systems_json=json.dumps(ship_data.get("systems", {})),
            departments_json=json.dumps(ship_data.get("departments", {})),
            weapons_json=json.dumps(ship_data.get("weapons", [])),
            talents_json=json.dumps(ship_data.get("talents", [])),
            traits_json=json.dumps(ship_data.get("traits", [])),
            breaches_json=json.dumps(ship_data.get("breaches", [])),
            shields=ship_data.get("shields", 0),
            shields_max=ship_data.get("shields_max", 0),
            resistance=ship_data.get("resistance", 0),
            has_reserve_power=ship_data.get("has_reserve_power", True),
            shields_raised=ship_data.get("shields_raised", False),
            weapons_armed=ship_data.get("weapons_armed", False),
            crew_quality=ship_data.get("crew_quality"),
            campaign_id=campaign.id,
            is_visible_to_players=ship_data.get("is_visible_to_players", True),
        )
        db.add(ship)
        await db.flush()
        created_ship_ids.append(ship.id)

        campaign_ship = CampaignShipRecord(
            campaign_id=campaign.id,
            ship_id=ship.id,
            vtt_ship_id=ship.id,
        )
        db.add(campaign_ship)

    await db.commit()

    return {
        "success": True,
        "campaign_id": campaign.campaign_id,
        "campaign_name": campaign.name,
        "characters_imported": len(created_character_ids),
        "ships_imported": len(created_ship_ids),
    }
