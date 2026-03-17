"""Character routes for VTT character management (FastAPI)."""

import json
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Body,
    Form,
    Cookie,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sta.database.async_db import get_db
from sta.database.schema import (
    CampaignRecord,
    CampaignPlayerRecord,
)
from sta.database.vtt_schema import (
    VTTCharacterRecord,
)
from sta.generators.data import GENERAL_TALENTS

characters_router = APIRouter(tags=["characters"])

# Also register with /api/vtt prefix for backward compatibility
vtt_characters_router = APIRouter(tags=["vtt-characters"])

VALID_STATES = ["Ok", "Fatigued", "Injured", "Dead"]


def _serialize_character(char: VTTCharacterRecord) -> dict:
    """Serialize a VTTCharacterRecord to JSON."""
    return {
        "id": char.id,
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
        "campaign_id": char.campaign_id,
        "scene_id": char.scene_id,
        "is_visible_to_players": char.is_visible_to_players,
        "created_at": char.created_at.isoformat() if char.created_at else None,
        "updated_at": char.updated_at.isoformat() if char.updated_at else None,
        "state": getattr(char, "state", "Ok"),
    }


# =============================================================================
# Character CRUD Endpoints
# =============================================================================


@characters_router.get("/characters")
async def list_characters(
    campaign_id: Optional[int] = None,
    char_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all characters with optional filters: campaign_id, type."""
    query = select(VTTCharacterRecord)

    if campaign_id is not None:
        query = query.filter(VTTCharacterRecord.campaign_id == campaign_id)

    if char_type:
        query = query.filter(VTTCharacterRecord.character_type == char_type)

    result = await db.execute(query)
    characters = result.scalars().all()
    return [_serialize_character(c) for c in characters]


@characters_router.get("/characters/{char_id}")
async def get_character(char_id: int, db: AsyncSession = Depends(get_db)):
    """Get single character with full details."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    return _serialize_character(char)


@characters_router.post("/characters", status_code=status.HTTP_201_CREATED)
async def create_character(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Create new character with validation."""
    name = data.get("name", "Unnamed Character")
    species = data.get("species")
    rank = data.get("rank")
    role = data.get("role")
    attributes = data.get("attributes", {})
    disciplines = data.get("disciplines", {})
    talents = data.get("talents", [])
    focuses = data.get("focuses", [])
    stress = data.get("stress", 0)
    stress_max = data.get("stress_max", 5)
    determination = data.get("determination", 0)
    determination_max = data.get("determination_max", 3)
    character_type = data.get("character_type", "support")
    pronouns = data.get("pronouns")
    avatar_url = data.get("avatar_url")
    description = data.get("description")
    values = data.get("values", [])
    equipment = data.get("equipment", [])
    environment = data.get("environment")
    upbringing = data.get("upbringing")
    career_path = data.get("career_path")
    campaign_id = data.get("campaign_id")
    is_visible_to_players = data.get("is_visible_to_players", True)

    try:
        attributes_json = json.dumps(attributes)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid attributes JSON")

    try:
        disciplines_json = json.dumps(disciplines)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid disciplines JSON")

    for attr_name, value in attributes.items():
        if not (7 <= value <= 12):
            raise HTTPException(
                status_code=400,
                detail=f"Attribute {attr_name} must be between 7-12, got {value}",
            )

    for disc_name, value in disciplines.items():
        if not (0 <= value <= 5):
            raise HTTPException(
                status_code=400,
                detail=f"Discipline {disc_name} must be between 0-5, got {value}",
            )

    if not (0 <= stress <= stress_max):
        raise HTTPException(
            status_code=400,
            detail=f"Stress must be between 0-{stress_max}, got {stress}",
        )

    if not (0 <= determination <= determination_max):
        raise HTTPException(
            status_code=400,
            detail=f"Determination must be between 0-{determination_max}, got {determination}",
        )

    char = VTTCharacterRecord(
        name=name,
        species=species,
        rank=rank,
        role=role,
        attributes_json=attributes_json,
        disciplines_json=disciplines_json,
        talents_json=json.dumps(talents),
        focuses_json=json.dumps(focuses),
        stress=stress,
        stress_max=stress_max,
        determination=determination,
        determination_max=determination_max,
        character_type=character_type,
        pronouns=pronouns,
        avatar_url=avatar_url,
        description=description,
        values_json=json.dumps(values),
        equipment_json=json.dumps(equipment),
        environment=environment,
        upbringing=upbringing,
        career_path=career_path,
        campaign_id=campaign_id,
        is_visible_to_players=is_visible_to_players,
    )

    db.add(char)
    await db.commit()
    await db.refresh(char)

    return _serialize_character(char)


@characters_router.put("/characters/{char_id}")
async def update_character(
    char_id: int,
    db: AsyncSession = Depends(get_db),
    name: Optional[str] = Form(None),
    species: Optional[str] = Form(None),
    rank: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    character_type: Optional[str] = Form(None),
    pronouns: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    environment: Optional[str] = Form(None),
    upbringing: Optional[str] = Form(None),
    career_path: Optional[str] = Form(None),
    is_visible_to_players: Optional[bool] = Form(None),
    campaign_id: Optional[int] = Form(None),
    attributes_json: Optional[str] = Form(None),
    disciplines_json: Optional[str] = Form(None),
    stress: Optional[int] = Form(None),
    stress_max: Optional[int] = Form(None),
    determination: Optional[int] = Form(None),
    determination_max: Optional[int] = Form(None),
    talents_json: Optional[str] = Form(None),
    focuses_json: Optional[str] = Form(None),
    values_json: Optional[str] = Form(None),
    equipment_json: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
):
    """Update character with validation."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    if name is not None:
        char.name = name
    if species is not None:
        char.species = species
    if rank is not None:
        char.rank = rank
    if role is not None:
        char.role = role
    if character_type is not None:
        char.character_type = character_type
    if pronouns is not None:
        char.pronouns = pronouns
    if avatar_url is not None:
        char.avatar_url = avatar_url
    if description is not None:
        char.description = description
    if environment is not None:
        char.environment = environment
    if upbringing is not None:
        char.upbringing = upbringing
    if career_path is not None:
        char.career_path = career_path
    if is_visible_to_players is not None:
        char.is_visible_to_players = is_visible_to_players
    if campaign_id is not None:
        char.campaign_id = campaign_id

    if attributes_json is not None:
        try:
            attrs = json.loads(attributes_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid attributes JSON")
        for attr_name, value in attrs.items():
            if not (7 <= value <= 12):
                raise HTTPException(
                    status_code=400,
                    detail=f"Attribute {attr_name} must be between 7-12, got {value}",
                )
        char.attributes_json = attributes_json

    if disciplines_json is not None:
        try:
            discs = json.loads(disciplines_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid disciplines JSON")
        for disc_name, value in discs.items():
            if not (0 <= value <= 5):
                raise HTTPException(
                    status_code=400,
                    detail=f"Discipline {disc_name} must be between 0-5, got {value}",
                )
        char.disciplines_json = disciplines_json

    if stress is not None or stress_max is not None:
        stress_max_val = stress_max if stress_max is not None else char.stress_max
        stress_val = stress if stress is not None else char.stress
        if not (0 <= stress_val <= stress_max_val):
            raise HTTPException(
                status_code=400,
                detail=f"Stress must be between 0-{stress_max_val}, got {stress_val}",
            )
        if stress is not None:
            char.stress = stress
        if stress_max is not None:
            char.stress_max = stress_max

    if determination is not None or determination_max is not None:
        det_max_val = (
            determination_max
            if determination_max is not None
            else char.determination_max
        )
        det_val = determination if determination is not None else char.determination
        if not (0 <= det_val <= det_max_val):
            raise HTTPException(
                status_code=400,
                detail=f"Determination must be between 0-{det_max_val}, got {det_val}",
            )
        if determination is not None:
            char.determination = determination
        if determination_max is not None:
            char.determination_max = determination_max

    if talents_json is not None:
        char.talents_json = talents_json
    if focuses_json is not None:
        char.focuses_json = focuses_json
    if values_json is not None:
        char.values_json = values_json
    if equipment_json is not None:
        char.equipment_json = equipment_json

    if state is not None:
        if state not in VALID_STATES:
            raise HTTPException(
                status_code=400, detail=f"State must be one of {VALID_STATES}"
            )
        char.state = state

    await db.commit()
    await db.refresh(char)
    return _serialize_character(char)


@characters_router.delete("/characters/{char_id}")
async def delete_character(
    char_id: int,
    db: AsyncSession = Depends(get_db),
    campaign_id: Optional[int] = None,
    sta_session_token: Optional[str] = Cookie(None),
):
    """Delete character (GM only)."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    if char.campaign_id:
        if not sta_session_token:
            raise HTTPException(status_code=401, detail="GM authentication required")

        gm_stmt = select(CampaignPlayerRecord).filter(
            CampaignPlayerRecord.campaign_id == char.campaign_id,
            CampaignPlayerRecord.is_gm == True,
        )
        gm_result = await db.execute(gm_stmt)
        gm_player = gm_result.scalars().first()

        if not gm_player or sta_session_token != gm_player.session_token:
            raise HTTPException(status_code=401, detail="GM authentication required")

    await db.delete(char)
    await db.commit()
    return {"success": True}


# =============================================================================
# Character Model Endpoint
# =============================================================================


@characters_router.get("/characters/{char_id}/model")
async def get_character_model(char_id: int, db: AsyncSession = Depends(get_db)):
    """Return character as legacy Character model."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    model = char.to_model()

    return {
        "name": model.name,
        "attributes": {
            "control": model.attributes.control,
            "fitness": model.attributes.fitness,
            "daring": model.attributes.daring,
            "insight": model.attributes.insight,
            "presence": model.attributes.presence,
            "reason": model.attributes.reason,
        },
        "disciplines": {
            "command": model.disciplines.command,
            "conn": model.disciplines.conn,
            "engineering": model.disciplines.engineering,
            "medicine": model.disciplines.medicine,
            "science": model.disciplines.science,
            "security": model.disciplines.security,
        },
        "talents": model.talents,
        "focuses": model.focuses,
        "stress": model.stress,
        "stress_max": model.stress_max,
        "determination": model.determination,
        "determination_max": model.determination_max,
        "rank": model.rank,
        "species": model.species,
        "role": model.role,
        "character_type": model.character_type,
        "pronouns": model.pronouns,
        "avatar_url": model.avatar_url,
        "description": model.description,
        "values": model.values,
        "equipment": model.equipment,
        "environment": model.environment,
        "upbringing": model.upbringing,
        "career_path": model.career_path,
    }


# =============================================================================
# Character Stress & Determination Endpoints
# =============================================================================


@characters_router.put("/characters/{char_id}/stress")
async def adjust_stress(
    char_id: int,
    adjustment: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Adjust stress."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    new_stress = char.stress + adjustment
    if new_stress < 0:
        new_stress = 0
    if new_stress > char.stress_max:
        new_stress = char.stress_max

    char.stress = new_stress
    await db.commit()

    return {
        "stress": char.stress,
        "stress_max": char.stress_max,
        "adjustment": adjustment,
    }


@characters_router.put("/characters/{char_id}/determination")
async def adjust_determination(
    char_id: int,
    adjustment: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Adjust determination."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    new_determination = char.determination + adjustment
    if new_determination < 0:
        new_determination = 0
    if new_determination > char.determination_max:
        new_determination = char.determination_max

    char.determination = new_determination
    await db.commit()

    return {
        "determination": char.determination,
        "determination_max": char.determination_max,
        "adjustment": adjustment,
    }


# =============================================================================
# Character State Endpoint
# =============================================================================


@characters_router.put("/characters/{char_id}/state")
async def update_character_state(
    char_id: int, state: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)
):
    """Update character state (Ok, Fatigued, Injured, Dead)."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    if state not in VALID_STATES:
        raise HTTPException(
            status_code=400, detail=f"State must be one of {VALID_STATES}"
        )

    char.state = state
    await db.commit()

    return {"state": char.state}


# =============================================================================
# Character Talents Endpoints
# =============================================================================


@characters_router.get("/characters/{char_id}/talents")
async def list_talents(char_id: int, db: AsyncSession = Depends(get_db)):
    """List available talents for a character."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    current_talents = json.loads(char.talents_json)

    return {
        "character_talents": current_talents,
        "available_talents": GENERAL_TALENTS,
    }


@characters_router.post("/characters/{char_id}/talents")
async def add_talent(
    char_id: int,
    talent_name: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Add talent to character."""
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    if talent_name not in GENERAL_TALENTS:
        raise HTTPException(status_code=400, detail=f"Unknown talent: {talent_name}")

    current_talents = json.loads(char.talents_json)

    if talent_name in current_talents:
        raise HTTPException(status_code=400, detail="Character already has this talent")

    current_talents.append(talent_name)
    char.talents_json = json.dumps(current_talents)
    await db.commit()

    return {
        "talents": current_talents,
        "added": talent_name,
    }


# Export endpoint
@characters_router.get("/characters/{char_id}/export")
async def export_character(
    char_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export a VTT character as JSON."""
    char = (
        (
            await db.execute(
                select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
            )
        )
        .scalars()
        .first()
    )
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    return {
        "id": char.id,
        "name": char.name,
        "description": char.description,
        "attributes": json.loads(char.attributes_json or "{}"),
        "disciplines": json.loads(char.disciplines_json or "{}"),
        "talents": json.loads(char.talents_json or "[]"),
        "focuses": json.loads(char.focuses_json or "[]"),
    }


@characters_router.post("/characters/import")
async def import_character(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Import a VTT character from JSON."""
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    attributes = data.get("attributes", {})
    disciplines = data.get("disciplines", {})

    char = VTTCharacterRecord(
        name=name,
        description=data.get("description", ""),
        attributes_json=json.dumps(attributes),
        disciplines_json=json.dumps(disciplines),
        talents_json=json.dumps(data.get("talents", [])),
        focuses_json=json.dumps(data.get("focuses", [])),
    )
    db.add(char)
    await db.commit()

    return {
        "id": char.id,
        "name": char.name,
        "success": True,
    }
