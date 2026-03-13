"""Universe Library API routes for managing reusable characters and ships (FastAPI)."""

import json
import uuid
import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Query, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sqlalchemy_delete
from sta.database.async_db import get_db
from sta.database.schema import (
    CampaignRecord,
    CampaignPlayerRecord,
    CampaignShipRecord,
    CharacterRecord,
    SceneRecord,
    NPCRecord,
)
from sta.database.vtt_schema import (
    UniverseItemRecord,
    VTTCharacterRecord,
    VTTShipRecord,
)
from sta.models.character import Character  # Used by serialization check
from sta.models.starship import Starship  # Used by generation stub

universe_router = APIRouter(prefix="/universe")

VALID_CATEGORIES = ["pcs", "npcs", "creatures", "ships"]
VALID_ITEM_TYPES = ["character", "ship"]


async def _require_gm_auth(
    campaign_id: int,
    sta_session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> None:
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

    if not gm_player or sta_session_token != gm_player.session_token:
        raise HTTPException(status_code=401, detail="GM authentication required")


# --- STUBS ---
def _serialize_character_vtt(char: VTTCharacterRecord) -> dict:
    """STUB: Serialize VTT Character for API returns."""
    return {
        "id": char.id,
        "name": char.name,
        "description": char.description,
        "category": "pcs",
        "item_type": "character",
    }


def _serialize_ship_vtt(ship: VTTShipRecord) -> dict:
    """STUB: Serialize VTT Ship for API returns."""
    return {"id": ship.id, "name": ship.name, "category": "ships", "item_type": "ship"}


async def _generate_random_character():
    """STUB: Synchronous character generator wrapped in threadpool."""
    return {
        "id": 10001,
        "name": "API_Generated_Char",
        "attributes_json": "{}",
        "campaign_id": None,
    }


async def _generate_random_ship():
    """STUB: Synchronous ship generator wrapped in threadpool."""
    return {"id": 10002, "name": "API_Generated_Ship", "scale": 4}


# ========== LIBRARY CRUD ==========


@universe_router.get("/", response_model=List[Dict[str, Any]])
async def list_universe_items(db: AsyncSession = Depends(get_db)):
    """API: List all library items."""
    result = await db.execute(select(UniverseItemRecord))
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "item_type": item.item_type,
            "description": item.description,
            "image_url": item.image_url,
            "data": json.loads(item.data_json),
        }
        for item in items
    ]


@universe_router.post("/characters", response_model=Dict[str, Any])
async def add_character_to_library(
    data: dict = Body(...), db: AsyncSession = Depends(get_db)
):
    """API: Add a character to the library from a VTTCharacterRecord ID."""

    character_id = data.get("character_id")
    category = data.get("category", "pcs")

    if not character_id:
        raise HTTPException(status_code=400, detail="character_id is required")

    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}",
        )

    character = (
        (
            await db.execute(
                select(VTTCharacterRecord).filter(VTTCharacterRecord.id == character_id)
            )
        )
        .scalars()
        .first()
    )
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    existing = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(
                    UniverseItemRecord.name == character.name,
                    UniverseItemRecord.item_type == "character",
                )
            )
        )
        .scalars()
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Character already in library")

    new_item = UniverseItemRecord(
        name=character.name,
        category=category,
        item_type="character",
        data_json=character.attributes_json,
        description=character.description,
        image_url=character.avatar_url,
    )
    db.add(new_item)
    await db.commit()

    return _serialize_character_vtt(character) | {
        "id": new_item.id,
        "category": category,
    }


@universe_router.post("/ships", response_model=Dict[str, Any])
async def add_ship_to_library(
    data: dict = Body(...), db: AsyncSession = Depends(get_db)
):
    """API: Add a ship to the library from a VTTShipRecord ID."""
    ship_id = data.get("ship_id")
    if not ship_id:
        raise HTTPException(status_code=400, detail="ship_id is required")

    ship = (
        (await db.execute(select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)))
        .scalars()
        .first()
    )
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    existing = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(
                    UniverseItemRecord.name == ship.name,
                    UniverseItemRecord.item_type == "ship",
                )
            )
        )
        .scalars()
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Ship already in library")

    new_item = UniverseItemRecord(
        name=ship.name,
        category="ships",
        item_type="ship",
        data_json=ship.systems_json,
        description=ship.ship_class,
        image_url=ship.token_url,
    )
    db.add(new_item)
    await db.commit()

    return _serialize_ship_vtt(ship) | {"id": new_item.id}


@universe_router.get("/{category}", response_model=List[Dict[str, Any]])
async def get_items_by_category(category: str, db: AsyncSession = Depends(get_db)):
    """API: Get items filtered by category."""
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}",
        )

    result = await db.execute(
        select(UniverseItemRecord).filter(UniverseItemRecord.category == category)
    )
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "item_type": item.item_type,
            "description": item.description,
            "image_url": item.image_url,
            "data": json.loads(item.data_json),
        }
        for item in items
    ]


@universe_router.get("/item/<int:item_id>", response_model=Dict[str, Any])
async def get_universe_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """API: Get a specific universe item by ID."""
    item = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(UniverseItemRecord.id == item_id)
            )
        )
        .scalars()
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "item_type": item.item_type,
        "description": item.description,
        "image_url": item.image_url,
        "data": json.loads(item.data_json),
    }


@universe_router.put("/item/<int:item_id>", response_model=Dict[str, Any])
async def update_universe_item(
    item_id: int, data: dict = Body(...), db: AsyncSession = Depends(get_db)
):
    """API: Update a universe item."""
    item = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(UniverseItemRecord.id == item_id)
            )
        )
        .scalars()
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if "name" in data:
        item.name = data["name"]
    if "category" in data:
        if data["category"] not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}",
            )
        item.category = data["category"]
    if "description" in data:
        item.description = data["description"]
    if "image_url" in data:
        item.image_url = data["image_url"]
    if "data" in data:
        item.data_json = json.dumps(data["data"])

    await db.commit()
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "item_type": item.item_type,
        "description": item.description,
        "image_url": item.image_url,
        "data": json.loads(item.data_json),
    }


@universe_router.delete("/item/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_universe_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """API: Delete a universe item (Requires reference checks/GM Auth stubbed)."""

    # Reference checks are stubbed (we only check library record existence)

    result = await db.execute(
        sqlalchemy_delete(UniverseItemRecord).where(UniverseItemRecord.id == item_id)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.commit()
    return {"success": True}


# ========== IMPORT/TEMPLATE ENDPOINTS ==========


@universe_router.post(
    "/import/character/{universe_item_id}", status_code=status.HTTP_201_CREATED
)
async def import_character_to_campaign(
    universe_item_id: int, data: dict = Body(...), db: AsyncSession = Depends(get_db)
):
    """API: Import a character from universe library to a campaign (GM action)."""

    campaign_id = data.get("campaign_id")
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required")

    campaign = (
        (
            await db.execute(
                select(CampaignRecord).filter(CampaignRecord.id == campaign_id)
            )
        )
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await _require_gm_auth(campaign.id, db=db)  # GM Auth stub

    universe_item = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(
                    UniverseItemRecord.id == universe_item_id,
                    UniverseItemRecord.item_type == "character",
                )
            )
        )
        .scalars()
        .first()
    )
    if not universe_item:
        raise HTTPException(status_code=404, detail="Character not found in library")

    existing_in_campaign = (
        (
            await db.execute(
                select(VTTCharacterRecord).filter(
                    VTTCharacterRecord.name == universe_item.name,
                    VTTCharacterRecord.campaign_id == campaign.id,
                )
            )
        )
        .scalars()
        .first()
    )
    if existing_in_campaign:
        raise HTTPException(
            status_code=409, detail="Character already exists in campaign"
        )

    character_data = json.loads(universe_item.data_json)

    # Minimal stubbed creation based on available data
    new_character = VTTCharacterRecord(
        name=universe_item.name,
        description=universe_item.description,
        avatar_url=universe_item.image_url,
        attributes_json=universe_item.data_json,
        disciplines_json=json.dumps(
            {
                "command": 1,
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 1,
                "security": 1,
            }
        ),
        talents_json="[]",
        focuses_json="[]",
        campaign_id=campaign.id,
        is_visible_to_players=True,
        state="Ok",
    )
    db.add(new_character)
    await db.commit()

    return {
        "id": new_character.id,
        "name": new_character.name,
        "campaign_id": new_character.campaign_id,
    }


@universe_router.post(
    "/import/ship/{universe_item_id}", status_code=status.HTTP_201_CREATED
)
async def import_ship_to_campaign(
    universe_item_id: int, data: dict = Body(...), db: AsyncSession = Depends(get_db)
):
    """API: Import a ship from universe library to a campaign."""

    campaign_id = data.get("campaign_id")
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required")

    campaign = (
        (
            await db.execute(
                select(CampaignRecord).filter(CampaignRecord.id == campaign_id)
            )
        )
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await _require_gm_auth(campaign.id, db=db)

    universe_item = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(
                    UniverseItemRecord.id == universe_item_id,
                    UniverseItemRecord.item_type == "ship",
                )
            )
        )
        .scalars()
        .first()
    )
    if not universe_item:
        raise HTTPException(
            status_code=404, detail="Ship template not found in library"
        )

    existing_in_campaign = (
        (
            await db.execute(
                select(VTTShipRecord).filter(
                    VTTShipRecord.name == universe_item.name,
                    VTTShipRecord.campaign_id == campaign.id,
                )
            )
        )
        .scalars()
        .first()
    )
    if existing_in_campaign:
        raise HTTPException(status_code=409, detail="Ship already exists in campaign")

    ship_data = json.loads(universe_item.data_json)

    new_ship = VTTShipRecord(
        name=universe_item.name,
        ship_class=universe_item.description or "Unknown Class",
        scale=ship_data.get("scale", 4),
        token_url=universe_item.image_url,
        systems_json=universe_item.data_json,
        departments_json=json.dumps(
            {
                "command": 1,
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 1,
                "security": 1,
            }
        ),  # Stubbed
        weapons_json="[]",
        talents_json="[]",
        traits_json="[]",
        breaches_json="[]",
        shields=ship_data.get("shields", 10),
        shields_max=ship_data.get("shields_max", 10),
        resistance=ship_data.get("resistance", 0),
        has_reserve_power=ship_data.get("has_reserve_power", True),
        campaign_id=campaign.id,
    )
    db.add(new_ship)
    await db.commit()

    return {
        "id": new_ship.id,
        "name": new_ship.name,
        "campaign_id": new_ship.campaign_id,
    }


# ========== TEMPLATE LISTING (API Style) ==========


@universe_router.get("/templates/characters", response_model=List[Dict[str, Any]])
async def list_character_templates(db: AsyncSession = Depends(get_db)):
    """API: List character templates from universe library."""
    result = await db.execute(
        select(UniverseItemRecord).filter(UniverseItemRecord.item_type == "character")
    )
    items = result.scalars().all()

    return [
        {"id": item.id, "name": item.name, "category": item.category} for item in items
    ]


@universe_router.get("/templates/ships", response_model=List[Dict[str, Any]])
async def list_ship_templates(db: AsyncSession = Depends(get_db)):
    """API: List ship templates from universe library."""
    result = await db.execute(
        select(UniverseItemRecord).filter(UniverseItemRecord.item_type == "ship")
    )
    items = result.scalars().all()

    return [
        {"id": item.id, "name": item.name, "category": item.category} for item in items
    ]


@universe_router.get(
    "/campaigns/<int:campaign_id>/characters/available",
    response_model=List[Dict[str, Any]],
)
async def list_available_characters(
    campaign_id: int, db: AsyncSession = Depends(get_db)
):
    """API: List available characters for a campaign (library templates)."""
    campaign = (
        (
            await db.execute(
                select(CampaignRecord).filter(CampaignRecord.id == campaign_id)
            )
        )
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await _require_gm_auth(campaign.id, db=db)

    library_items = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(
                    UniverseItemRecord.item_type == "character"
                )
            )
        )
        .scalars()
        .all()
    )

    # Check existing characters in this campaign
    existing_char_names = {
        (c.name)
        for c in (
            await db.execute(
                select(VTTCharacterRecord).filter_by(campaign_id=campaign_id)
            )
        ).all()
    }

    available = []
    for item in library_items:
        if item.name not in existing_char_names:
            available.append(
                {"id": item.id, "name": item.name, "category": item.category}
            )

    return available


@universe_router.get(
    "/campaigns/<int:campaign_id>/ships/available", response_model=List[Dict[str, Any]]
)
async def list_available_ships(campaign_id: int, db: AsyncSession = Depends(get_db)):
    """API: List available ships for a campaign (library templates)."""
    campaign = (
        (
            await db.execute(
                select(CampaignRecord).filter(CampaignRecord.id == campaign_id)
            )
        )
        .scalars()
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await _require_gm_auth(campaign.id, db=db)

    library_items = (
        (
            await db.execute(
                select(UniverseItemRecord).filter(
                    UniverseItemRecord.item_type == "ship"
                )
            )
        )
        .scalars()
        .all()
    )

    campaign_ship_ids = {
        (s.ship_id)
        for s in (
            await db.execute(
                select(CampaignShipRecord).filter_by(campaign_id=campaign.id)
            )
        ).all()
    }

    available = []
    for item in library_items:
        # Assuming item.id links to VTTShipRecord.id for simplicity in this stubbed API
        if item.id not in campaign_ship_ids:
            available.append({"id": item.id, "name": item.name})

    return available
