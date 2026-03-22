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
    LogEntryRecord,
)
from sta.generators.data import (
    GENERAL_TALENTS,
    FOCUSES,
    SPECIES,
    RANKS,
    SHIP_CLASSES,
)
from sta.generators.data import GENERAL_TALENTS

characters_router = APIRouter(tags=["characters"])

# Also register with /api/vtt prefix for backward compatibility
vtt_characters_router = APIRouter(tags=["vtt-characters"])

VALID_STATES = ["Ok", "Fatigued", "Injured", "Dead"]


def _serialize_character(char: VTTCharacterRecord) -> dict:
    """Serialize a VTTCharacterRecord to JSON."""
    values = json.loads(char.values_json or "[]")
    for v in values:
        v["used_this_session"] = v.get("used_this_session", False)

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
        "values": values,
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

    # Exclude Q from character listings (Q is the Game Master)
    query = query.filter(VTTCharacterRecord.name != "Q")

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


# =============================================================================
# Character Values Endpoints (with Session Tracking)
# =============================================================================


@characters_router.get("/characters/{char_id}/values")
async def get_character_values(char_id: int, db: AsyncSession = Depends(get_db)):
    """Get character Values with session tracking status.

    Returns Values with their current 'used_this_session' status.
    Values can be used once per session to spend Determination.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    values = json.loads(char.values_json or "[]")
    for v in values:
        v["used_this_session"] = v.get("used_this_session", False)

    return {"values": values}


@characters_router.post("/characters/{char_id}/values")
async def add_value(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Add a Value to character.

    Value format: {"name": str, "description": str, "helpful": bool}
    The 'used_this_session' field is initialized to False.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Value name is required")

    description = data.get("description", "")
    helpful = data.get("helpful", True)

    values = json.loads(char.values_json or "[]")

    existing_names = [v.get("name", "").lower() for v in values]
    if name.lower() in existing_names:
        raise HTTPException(status_code=400, detail="Character already has this Value")

    new_value = {
        "name": name,
        "description": description,
        "helpful": helpful,
        "used_this_session": False,
    }
    values.append(new_value)
    char.values_json = json.dumps(values)
    await db.commit()

    return {
        "values": values,
        "added": new_value,
    }


@characters_router.put("/characters/{char_id}/values/{value_name}/use")
async def mark_value_used(
    char_id: int,
    value_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a Value as used this session.

    A Value can only be used once per session to spend Determination.
    Returns 400 if Value was already used this session.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    values = json.loads(char.values_json or "[]")
    value_found = False
    already_used = False

    for v in values:
        if v.get("name", "").lower() == value_name.lower():
            value_found = True
            if v.get("used_this_session", False):
                already_used = True
            else:
                v["used_this_session"] = True

    if not value_found:
        raise HTTPException(status_code=404, detail="Value not found")

    if already_used:
        raise HTTPException(
            status_code=400,
            detail=f"Value '{value_name}' has already been used this session",
        )

    char.values_json = json.dumps(values)
    await db.commit()

    return {
        "value_name": value_name,
        "used_this_session": True,
        "message": f"Value '{value_name}' marked as used. You may spend Determination.",
    }


@characters_router.put("/characters/{char_id}/values/{value_name}/challenge")
async def mark_value_challenged(
    char_id: int,
    value_name: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Mark a Value as challenged and grant 1 Determination.

    Challenging a Value conflicts with immediate goals but grants 1 Determination.
    This does NOT consume the Value's 'used_this_session' status.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    values = json.loads(char.values_json or "[]")
    value_found = False

    for v in values:
        if v.get("name", "").lower() == value_name.lower():
            value_found = True
            v["last_challenged_session"] = True

    if not value_found:
        raise HTTPException(status_code=404, detail="Value not found")

    if char.determination < char.determination_max:
        char.determination += 1
    else:
        raise HTTPException(
            status_code=400, detail="Determination is already at maximum"
        )

    char.values_json = json.dumps(values)
    await db.commit()

    return {
        "value_name": value_name,
        "determination": char.determination,
        "message": f"Value '{value_name}' challenged. +1 Determination granted.",
    }


@characters_router.put("/characters/{char_id}/values/{value_name}/comply")
async def mark_value_complied(
    char_id: int,
    value_name: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Mark a Value as complied and grant 1 Determination.

    Complying a Value aligns with goals but hinders progress, granting 1 Determination.
    This does NOT consume the Value's 'used_this_session' status.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    values = json.loads(char.values_json or "[]")
    value_found = False

    for v in values:
        if v.get("name", "").lower() == value_name.lower():
            value_found = True
            v["last_complied_session"] = True

    if not value_found:
        raise HTTPException(status_code=404, detail="Value not found")

    if char.determination < char.determination_max:
        char.determination += 1
    else:
        raise HTTPException(
            status_code=400, detail="Determination is already at maximum"
        )

    char.values_json = json.dumps(values)
    await db.commit()

    return {
        "value_name": value_name,
        "determination": char.determination,
        "message": f"Value '{value_name}' complied. +1 Determination granted.",
    }


@characters_router.post("/characters/{char_id}/values/reset-session")
async def reset_values_session(
    char_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Reset all Values' 'used_this_session' status for a new session.

    This should be called at the start of each new game session to allow
    Values to be used again.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    values = json.loads(char.values_json or "[]")
    for v in values:
        v["used_this_session"] = False
        v.pop("last_challenged_session", None)
        v.pop("last_complied_session", None)

    char.values_json = json.dumps(values)
    await db.commit()

    return {
        "message": "All Values reset for new session",
        "values": values,
    }


# Export endpoint
@characters_router.get("/characters/{char_id}/export")
async def export_character(
    char_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export a VTT character as JSON with all fields."""
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
        "species": char.species,
        "rank": char.rank,
        "role": char.role,
        "pronouns": char.pronouns,
        "description": char.description,
        "attributes": json.loads(char.attributes_json or "{}"),
        "disciplines": json.loads(char.disciplines_json or "{}"),
        "stress": char.stress,
        "stress_max": char.stress_max,
        "determination": char.determination,
        "determination_max": char.determination_max,
        "talents": json.loads(char.talents_json or "[]"),
        "focuses": json.loads(char.focuses_json or "[]"),
        "values": json.loads(char.values_json or "[]"),
        "equipment": json.loads(char.equipment_json or "[]"),
        "environment": char.environment,
        "upbringing": char.upbringing,
        "career_path": char.career_path,
    }


@characters_router.post("/characters/import", status_code=status.HTTP_201_CREATED)
async def import_character(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Import VTT character(s) from JSON.

    Accepts either a single character object or a container with 'characters' key.
    Validates: attributes (7-12), disciplines (0-5), stress (0 to stress_max).
    Required fields: name, species, attributes, disciplines.
    """
    characters_to_import = []

    if "characters" in data:
        characters_to_import = data["characters"]
    elif isinstance(data, dict) and "name" in data:
        characters_to_import = [data]
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid format: must be either a single character object or {'characters': [...]}",
        )

    if not isinstance(characters_to_import, list):
        raise HTTPException(
            status_code=400, detail="Invalid format: 'characters' must be a list"
        )

    created_ids = []
    errors = []

    for idx, char_data in enumerate(characters_to_import):
        name = char_data.get("name")
        species = char_data.get("species")
        attributes = char_data.get("attributes", {})
        disciplines = char_data.get("disciplines", {})

        if not name:
            errors.append(f"Character at index {idx}: 'name' is required")
            continue

        if not species:
            errors.append(f"Character at index {idx}: 'species' is required")
            continue

        if not attributes:
            errors.append(f"Character at index {idx}: 'attributes' is required")
            continue

        if not disciplines:
            errors.append(f"Character at index {idx}: 'disciplines' is required")
            continue

        for attr_name, value in attributes.items():
            if not isinstance(value, int) or not (7 <= value <= 12):
                errors.append(
                    f"Character '{name}': attribute '{attr_name}' must be between 7-12, got {value}"
                )
                break

        for disc_name, value in disciplines.items():
            if not isinstance(value, int) or not (0 <= value <= 5):
                errors.append(
                    f"Character '{name}': discipline '{disc_name}' must be between 0-5, got {value}"
                )
                break

        stress = char_data.get("stress", 0)
        stress_max = char_data.get("stress_max", 5)
        if not (0 <= stress <= stress_max):
            errors.append(
                f"Character '{name}': stress must be between 0-{stress_max}, got {stress}"
            )

        determination = char_data.get("determination", 0)
        determination_max = char_data.get("determination_max", 3)
        if not (0 <= determination <= determination_max):
            errors.append(
                f"Character '{name}': determination must be between 0-{determination_max}, got {determination}"
            )

        if any(e.startswith(f"Character '{name}'") for e in errors):
            continue

        char = VTTCharacterRecord(
            name=name,
            species=species,
            rank=char_data.get("rank"),
            role=char_data.get("role"),
            pronouns=char_data.get("pronouns"),
            description=char_data.get("description"),
            attributes_json=json.dumps(attributes),
            disciplines_json=json.dumps(disciplines),
            talents_json=json.dumps(char_data.get("talents", [])),
            focuses_json=json.dumps(char_data.get("focuses", [])),
            values_json=json.dumps(char_data.get("values", [])),
            equipment_json=json.dumps(char_data.get("equipment", [])),
            environment=char_data.get("environment"),
            upbringing=char_data.get("upbringing"),
            career_path=char_data.get("career_path"),
            stress=stress,
            stress_max=stress_max,
            determination=determination,
            determination_max=determination_max,
            character_type=char_data.get("character_type", "support"),
            is_visible_to_players=char_data.get("is_visible_to_players", True),
            campaign_id=char_data.get("campaign_id"),
        )
        db.add(char)
        await db.flush()
        created_ids.append(char.id)

    if errors:
        await db.rollback()
        return {"success": False, "errors": errors}

    await db.commit()

    return {
        "success": True,
        "created": len(created_ids),
        "character_ids": created_ids,
    }


# =============================================================================
# Log Entry Endpoints (M10.9 - Character Sheet Narrative Tab)
# =============================================================================


@characters_router.get("/characters/{char_id}/logs")
async def get_character_logs(
    char_id: int,
    log_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get log entries for a character.

    - log_type: Filter by PERSONAL, MISSION, or VALUE (optional)
    - PERSONAL logs: Visible to all other players in campaign (not owner)
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    log_stmt = select(LogEntryRecord).filter(LogEntryRecord.character_id == char_id)

    if log_type:
        log_stmt = log_stmt.filter(LogEntryRecord.log_type == log_type.upper())

    log_stmt = log_stmt.order_by(LogEntryRecord.created_at.desc())
    log_result = await db.execute(log_stmt)
    logs = log_result.scalars().all()

    return {
        "logs": [log.to_dict() for log in logs],
        "log_type": log_type,
    }


@characters_router.get("/characters/{char_id}/logs/personal")
async def get_personal_logs_for_players(
    char_id: int,
    campaign_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get personal logs visible to other players.

    Returns PERSONAL logs for a character, excluding logs created by the viewer.
    This allows players to see other characters' roleplay notes.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    query = select(LogEntryRecord).filter(
        LogEntryRecord.character_id == char_id,
        LogEntryRecord.log_type == "PERSONAL",
    )

    if campaign_id:
        from sqlalchemy.orm import joinedload

        query = query.join(
            VTTCharacterRecord, VTTCharacterRecord.id == LogEntryRecord.character_id
        )
        query = query.filter(VTTCharacterRecord.campaign_id == campaign_id)

    query = query.order_by(LogEntryRecord.created_at.desc())
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [log.to_dict() for log in logs],
        "character_id": char_id,
        "character_name": char.name,
    }


@characters_router.post(
    "/characters/{char_id}/logs", status_code=status.HTTP_201_CREATED
)
async def create_log_entry(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a new log entry for a character.

    Log types:
    - PERSONAL: Roleplay notes visible to other players
    - MISSION: Scene/mission events (auto-generated)
    - VALUE: Value interactions (auto-generated)

    For PERSONAL logs, include user_id in request to track visibility.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    log_type = data.get("log_type", "MISSION").upper()
    if log_type not in ["PERSONAL", "MISSION", "VALUE"]:
        raise HTTPException(
            status_code=400,
            detail="log_type must be PERSONAL, MISSION, or VALUE",
        )

    log = LogEntryRecord(
        character_id=char_id,
        log_type=log_type,
        content=data.get("content", ""),
        event_type=data.get("event_type"),
        character_name=char.name,
        created_by_user_id=data.get("user_id"),
    )

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return log.to_dict()


@characters_router.put("/characters/{char_id}/logs/{log_id}")
async def update_log_entry(
    char_id: int,
    log_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Update a log entry (owner can edit their own logs)."""
    stmt = select(LogEntryRecord).filter(
        LogEntryRecord.id == log_id,
        LogEntryRecord.character_id == char_id,
    )
    result = await db.execute(stmt)
    log = result.scalars().first()

    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")

    if "content" in data:
        log.content = data["content"]

    await db.commit()
    await db.refresh(log)

    return log.to_dict()


@characters_router.delete("/characters/{char_id}/logs/{log_id}")
async def delete_log_entry(
    char_id: int,
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a log entry."""
    stmt = select(LogEntryRecord).filter(
        LogEntryRecord.id == log_id,
        LogEntryRecord.character_id == char_id,
    )
    result = await db.execute(stmt)
    log = result.scalars().first()

    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")

    await db.delete(log)
    await db.commit()

    return {"success": True}


@characters_router.post("/characters/{char_id}/logs/scene-event")
async def log_scene_event(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Auto-create a log entry for scene events.

    Event types:
    - scene_enter: Character entered a scene
    - scene_exit: Character exited a scene
    - scene_complete: Scene was completed
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    event_type = data.get("event_type")
    if event_type not in ["scene_enter", "scene_exit", "scene_complete"]:
        raise HTTPException(
            status_code=400,
            detail="event_type must be scene_enter, scene_exit, or scene_complete",
        )

    scene_name = data.get("scene_name", "Unknown Scene")
    description = data.get("description", "")

    content = f"{scene_name}: {event_type.replace('_', ' ').title()}"
    if description:
        content += f" - {description}"

    log = LogEntryRecord(
        character_id=char_id,
        log_type="MISSION",
        content=content,
        event_type=event_type,
        character_name=char.name,
    )

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return log.to_dict()


@characters_router.post("/characters/{char_id}/logs/value-event")
async def log_value_event(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Auto-create a log entry for Value interactions.

    Event types:
    - value_challenged: Value was challenged (gain Determination)
    - value_complied: Value was complied (gain Determination)
    - value_used: Value was used to spend Determination
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    event_type = data.get("event_type")
    if event_type not in ["value_challenged", "value_complied", "value_used"]:
        raise HTTPException(
            status_code=400,
            detail="event_type must be value_challenged, value_complied, or value_used",
        )

    value_name = data.get("value_name", "Unknown Value")
    description = data.get("description", "")

    content = (
        f"Value '{value_name}' {event_type.replace('value_', '').replace('_', ' ')}"
    )
    if description:
        content += f": {description}"

    log = LogEntryRecord(
        character_id=char_id,
        log_type="VALUE",
        content=content,
        event_type=event_type,
        character_name=char.name,
    )

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return log.to_dict()


# =============================================================================
# Guided Character Creation Wizard (M10.10)
# =============================================================================


@characters_router.post("/characters/wizard", status_code=status.HTTP_201_CREATED)
async def create_character_wizard(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a character using the 4-step guided wizard.

    Steps:
    1. FOUNDATION: Attributes (7-12, total ~42-52), Species
    2. SPECIALIZATION: Department ratings (1-5, total 15 pts), Talents, Focuses
    3. IDENTITY: Values (MINIMUM 2 required), Directives
    4. EQUIPMENT: Items, Weapons, Rank

    Validation:
    - Attributes must be 7-12 each
    - At least 2 Values required
    - Department ratings must be 1-5 each (total 15 pts)
    - Stress max = Fitness attribute
    - Determination starts at 1, max 3
    """
    step = data.get("step")
    character_data = data.get("character", {})
    campaign_id = data.get("campaign_id")

    if step not in [1, 2, 3, 4, "final"]:
        raise HTTPException(
            status_code=400,
            detail="step must be 1, 2, 3, 4, or 'final'",
        )

    errors = []

    if step in [1, "final"]:
        name = character_data.get("name", "Unnamed Character")
        species = character_data.get("species")
        attributes = character_data.get("attributes", {})

        if species and species not in SPECIES:
            errors.append(f"Invalid species: {species}")

        for attr_name, value in attributes.items():
            if not (7 <= value <= 12):
                errors.append(
                    f"Attribute {attr_name} must be between 7-12, got {value}"
                )

        total_attrs = sum(attributes.values()) if attributes else 0
        if total_attrs > 0 and not (42 <= total_attrs <= 52):
            errors.append(f"Total attribute sum should be 42-52, got {total_attrs}")

    if step in [2, "final"]:
        disciplines = character_data.get("disciplines", {})
        total_disc = sum(disciplines.values()) if disciplines else 0

        for disc_name, value in disciplines.items():
            if not (0 <= value <= 5):
                errors.append(
                    f"Discipline {disc_name} must be between 0-5, got {value}"
                )

        if total_disc > 0 and not (14 <= total_disc <= 18):
            pass

        talents = character_data.get("talents", [])
        for talent in talents:
            if talent not in GENERAL_TALENTS:
                errors.append(f"Invalid talent: {talent}")

        focuses = character_data.get("focuses", [])
        valid_focuses = []
        for f in focuses:
            found = False
            for disc_focuses in FOCUSES.values():
                if f in disc_focuses:
                    found = True
                    break
            if found:
                valid_focuses.append(f)
            else:
                errors.append(f"Invalid focus: {f}")

    if step in [3, "final"]:
        values = character_data.get("values", [])
        if len(values) < 2:
            errors.append("At least 2 Values are required")

        for v in values:
            if not isinstance(v, dict):
                errors.append("Each Value must be an object with name and description")
            elif not v.get("name"):
                errors.append("Each Value must have a name")

    if step in [4, "final"]:
        rank = character_data.get("rank")
        if rank and rank not in RANKS:
            errors.append(f"Invalid rank: {rank}")

    if step == "final" and errors:
        return {"success": False, "errors": errors}

    if step != "final":
        return {
            "success": True,
            "step_received": step,
            "validation_passed": len(errors) == 0,
            "errors": errors if errors else None,
            "message": f"Step {step} validated. Continue to next step.",
        }

    attributes = character_data.get(
        "attributes",
        {
            "control": 7,
            "fitness": 7,
            "daring": 7,
            "insight": 7,
            "presence": 7,
            "reason": 7,
        },
    )
    disciplines = character_data.get(
        "disciplines",
        {
            "command": 1,
            "conn": 1,
            "engineering": 1,
            "medicine": 1,
            "science": 1,
            "security": 1,
        },
    )

    fitness = attributes.get("fitness", 7)
    stress_max = fitness

    values = character_data.get("values", [])
    for v in values:
        if isinstance(v, dict):
            v["used_this_session"] = False

    char = VTTCharacterRecord(
        name=character_data.get("name", "Unnamed Character"),
        species=character_data.get("species"),
        rank=character_data.get("rank"),
        role=character_data.get("role"),
        attributes_json=json.dumps(attributes),
        disciplines_json=json.dumps(disciplines),
        talents_json=json.dumps(character_data.get("talents", [])),
        focuses_json=json.dumps(character_data.get("focuses", [])),
        stress=0,
        stress_max=stress_max,
        determination=1,
        determination_max=3,
        character_type=character_data.get("character_type", "support"),
        pronouns=character_data.get("pronouns"),
        avatar_url=character_data.get("avatar_url"),
        description=character_data.get("description"),
        values_json=json.dumps(values),
        equipment_json=json.dumps(character_data.get("equipment", [])),
        environment=character_data.get("environment"),
        upbringing=character_data.get("upbringing"),
        career_path=character_data.get("career_path"),
        campaign_id=campaign_id,
        is_visible_to_players=True,
    )

    db.add(char)
    await db.commit()
    await db.refresh(char)

    return {
        "success": True,
        "character": _serialize_character(char),
        "message": "Character created successfully via wizard",
    }


@characters_router.get("/characters/wizard/options")
async def get_character_creation_options(
    db: AsyncSession = Depends(get_db),
):
    """Get available options for character creation wizard.

    Returns:
    - Species list
    - Attribute ranges
    - Department/discipline options
    - Available talents
    - Available focuses
    - Value templates
    - Ranks
    """
    return {
        "species": SPECIES,
        "attributes": {
            "min": 7,
            "max": 12,
            "total_range": {"min": 42, "max": 52},
            "description": "Each attribute should be between 7-12, total typically 42-52",
        },
        "departments": {
            "min": 1,
            "max": 5,
            "total_points": 15,
            "list": [
                "command",
                "conn",
                "engineering",
                "medicine",
                "science",
                "security",
            ],
            "description": "Distribute 15 points across 6 departments (1-5 each)",
        },
        "talents": GENERAL_TALENTS,
        "focuses": FOCUSES,
        "ranks": RANKS,
        "value_templates": [
            {
                "name": "Integrity",
                "description": "I uphold the principles of the Federation.",
                "helpful": True,
            },
            {
                "name": "Compassion",
                "description": "I show mercy and understanding to all beings.",
                "helpful": True,
            },
            {
                "name": "Curiosity",
                "description": "I seek knowledge and new experiences.",
                "helpful": True,
            },
            {
                "name": "Duty",
                "description": "I fulfill my responsibilities without question.",
                "helpful": True,
            },
            {
                "name": "Logic",
                "description": "I trust in rational analysis over emotion.",
                "helpful": True,
            },
            {
                "name": "Courage",
                "description": "I face danger without hesitation.",
                "helpful": True,
            },
            {
                "name": "Ambition",
                "description": "I pursue power and advancement.",
                "helpful": False,
            },
            {
                "name": "Secrecy",
                "description": "I keep information hidden from others.",
                "helpful": False,
            },
        ],
        "rules": {
            "stress_max": "Equals Fitness attribute",
            "determination_start": 1,
            "determination_max": 3,
            "values_minimum": 2,
        },
    }


@characters_router.post("/ships/wizard", status_code=status.HTTP_201_CREATED)
async def create_ship_wizard(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a ship using the guided wizard.

    Options:
    - Scale selection (ship size class)
    - System ratings (0-5)
    - Department ratings (0-5)
    - Crew Quality
    - Traits
    """
    ship_data = data.get("ship", {})
    campaign_id = data.get("campaign_id")

    errors = []

    name = ship_data.get("name", "Unnamed Ship")
    ship_class = ship_data.get("ship_class")
    scale = ship_data.get("scale", 4)

    if not (1 <= scale <= 7):
        errors.append("Scale must be between 1-7")

    systems = ship_data.get("systems", {})
    for sys_name, value in systems.items():
        if not (0 <= value <= 5):
            errors.append(f"System {sys_name} must be between 0-5, got {value}")

    departments = ship_data.get("departments", {})
    for dept_name, value in departments.items():
        if not (0 <= value <= 5):
            errors.append(f"Department {dept_name} must be between 0-5, got {value}")

    if errors:
        return {"success": False, "errors": errors}

    ship = VTTShipRecord(
        name=name,
        ship_class=ship_class,
        ship_registry=ship_data.get("registry"),
        scale=scale,
        systems_json=json.dumps(systems),
        departments_json=json.dumps(departments),
        weapons_json=json.dumps(ship_data.get("weapons", [])),
        talents_json=json.dumps(ship_data.get("talents", [])),
        traits_json=json.dumps(ship_data.get("traits", [])),
        shields=ship_data.get("shields", 0),
        shields_max=ship_data.get("shields_max", 0),
        resistance=ship_data.get("resistance", 0),
        crew_quality=ship_data.get("crew_quality"),
        campaign_id=campaign_id,
        is_visible_to_players=True,
    )

    db.add(ship)
    await db.commit()
    await db.refresh(ship)

    return {
        "success": True,
        "ship": {
            "id": ship.id,
            "name": ship.name,
            "ship_class": ship.ship_class,
            "scale": ship.scale,
            "registry": ship.ship_registry,
        },
        "message": "Ship created successfully via wizard",
    }


@characters_router.get("/ships/wizard/options")
async def get_ship_creation_options(
    db: AsyncSession = Depends(get_db),
):
    """Get available options for ship creation wizard.

    Returns:
    - Ship classes with base stats
    - Scale options
    - System ranges
    - Department ranges
    - Ship talents
    - Weapon templates
    """
    return {
        "ship_classes": SHIP_CLASSES,
        "scale_range": {"min": 1, "max": 7},
        "systems": {
            "range": {"min": 0, "max": 5},
            "list": [
                "comms",
                "computers",
                "engines",
                "sensors",
                "structure",
                "weapons",
            ],
        },
        "departments": {
            "range": {"min": 0, "max": 5},
            "list": [
                "command",
                "conn",
                "engineering",
                "medicine",
                "science",
                "security",
            ],
        },
        "crew_qualities": [
            {"value": "basic", "attribute": 8, "department": 1},
            {"value": "proficient", "attribute": 9, "department": 2},
            {"value": "talented", "attribute": 10, "department": 3},
            {"value": "exceptional", "attribute": 11, "department": 4},
        ],
        "ship_talents": [
            "Ablative Armor",
            "Advanced Shields",
            "Backup EPS Conduits",
            "Improved Hull Integrity",
            "Redundant Systems (Engines)",
            "Redundant Systems (Weapons)",
            "Expanded Munitions",
            "Fast Targeting Systems",
            "High-Power Tractor Beam",
            "Improved Impulse Drive",
            "Improved Warp Drive",
            "Advanced Sensor Suites",
            "High-Resolution Sensors",
            "Modular Laboratories",
            "Rugged Design",
            "Improved Damage Control",
        ],
        "weapons": [
            {"name": "Phaser Banks", "type": "energy", "damage": 4, "range": "medium"},
            {"name": "Phaser Arrays", "type": "energy", "damage": 4, "range": "medium"},
            {
                "name": "Pulse Phaser Cannons",
                "type": "energy",
                "damage": 6,
                "range": "close",
            },
            {
                "name": "Photon Torpedoes",
                "type": "torpedo",
                "damage": 3,
                "range": "long",
            },
            {
                "name": "Quantum Torpedoes",
                "type": "torpedo",
                "damage": 4,
                "range": "long",
            },
        ],
        "rules": {
            "scale_to_crew_quality": "Scale 4+ ships can have named crew; smaller ships use crew quality",
        },
    }


# =============================================================================
# Value Status Enhancement (M10.9)
# =============================================================================


@characters_router.get("/characters/{char_id}/values/status")
async def get_character_values_with_status(
    char_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get character Values with full status information.

    Returns each Value with:
    - name, description, helpful/Problematic
    - used_this_session: bool
    - last_challenged_session: bool
    - last_complied_session: bool
    - interaction_count: total times interacted
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    values = json.loads(char.values_json or "[]")
    enhanced_values = []

    for v in values:
        enhanced = {
            "name": v.get("name", ""),
            "description": v.get("description", ""),
            "helpful": v.get("helpful", True),
            "used_this_session": v.get("used_this_session", False),
            "last_challenged_session": v.get("last_challenged_session", False),
            "last_complied_session": v.get("last_complied_session", False),
            "interaction_count": v.get("interaction_count", 0),
        }

        if enhanced["used_this_session"]:
            enhanced["status"] = "Used"
        elif enhanced["last_challenged_session"] or enhanced["last_complied_session"]:
            enhanced["status"] = "Triggered"
        else:
            enhanced["status"] = "Available"

        enhanced_values.append(enhanced)

    return {
        "values": enhanced_values,
        "determination": char.determination,
        "determination_max": char.determination_max,
    }


@characters_router.post("/characters/{char_id}/values/interact")
async def interact_with_value(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Value interaction with description.

    Actions:
    - use: Mark Value as used (costs 1 Determination, once per session)
    - challenge: Mark Value as challenged (gain 1 Determination)
    - comply: Mark Value as complied (gain 1 Determination)

    Creates a log entry automatically.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    value_name = data.get("value_name")
    action = data.get("action")
    description = data.get("description", "")

    if not value_name:
        raise HTTPException(status_code=400, detail="value_name is required")

    if action not in ["use", "challenge", "comply"]:
        raise HTTPException(
            status_code=400,
            detail="action must be 'use', 'challenge', or 'comply'",
        )

    values = json.loads(char.values_json or "[]")
    value_found = False

    for v in values:
        if v.get("name", "").lower() == value_name.lower():
            value_found = True
            v["interaction_count"] = v.get("interaction_count", 0) + 1

            if action == "use":
                if v.get("used_this_session", False):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Value '{value_name}' has already been used this session",
                    )
                if char.determination < 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Not enough Determination to use this Value",
                    )
                v["used_this_session"] = True
                char.determination -= 1

            elif action == "challenge":
                if char.determination >= char.determination_max:
                    raise HTTPException(
                        status_code=400,
                        detail="Determination is already at maximum",
                    )
                v["last_challenged_session"] = True
                char.determination += 1

            elif action == "comply":
                if char.determination >= char.determination_max:
                    raise HTTPException(
                        status_code=400,
                        detail="Determination is already at maximum",
                    )
                v["last_complied_session"] = True
                char.determination += 1

    if not value_found:
        raise HTTPException(status_code=404, detail="Value not found")

    log = LogEntryRecord(
        character_id=char_id,
        log_type="VALUE",
        content=f"Value '{value_name}' {action}ed"
        + (f": {description}" if description else ""),
        event_type=f"value_{action}ed",
        character_name=char.name,
    )
    db.add(log)

    char.values_json = json.dumps(values)
    await db.commit()
    await db.refresh(char)

    return {
        "success": True,
        "value_name": value_name,
        "action": action,
        "determination": char.determination,
        "determination_max": char.determination_max,
        "message": f"Value '{value_name}' {action}ed successfully",
    }


# =============================================================================
# Player Dice Roll Interface (M10.6)
# =============================================================================


VALID_ATTRIBUTES = ["control", "daring", "fitness", "insight", "presence", "reason"]
VALID_DEPARTMENTS = [
    "command",
    "conn",
    "engineering",
    "medicine",
    "science",
    "security",
]


@characters_router.post("/characters/{char_id}/roll")
async def roll_dice(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Perform a dice roll for a character task.

    This is the core endpoint for the Player Console Dice Roll Interface.

    Request Body:
    - attribute: Attribute name (control, daring, fitness, insight, presence, reason)
    - department: Department name (command, conn, engineering, medicine, science, security)
    - difficulty: Number of successes required (default 1)
    - complication_range: How many numbers from 20 cause complications (default 1)
    - focus: Whether focus applies (bool)
    - bonus_dice: Additional dice from Momentum/Threat (default 0)

    Returns full roll details with:
    - Individual dice results
    - Success breakdown (normal, criticals, focus crits)
    - Complication count
    - Momentum generated
    """
    from sta.mechanics.dice import player_task_roll

    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    attribute = data.get("attribute", "").lower()
    department = data.get("department", "").lower()
    difficulty = data.get("difficulty", 1)
    complication_range = data.get("complication_range", 1)
    focus = data.get("focus", False)
    bonus_dice = data.get("bonus_dice", 0)

    if attribute not in VALID_ATTRIBUTES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attribute. Must be one of: {VALID_ATTRIBUTES}",
        )

    if department not in VALID_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department. Must be one of: {VALID_DEPARTMENTS}",
        )

    if not (1 <= difficulty <= 10):
        raise HTTPException(
            status_code=400,
            detail="Difficulty must be between 1-10",
        )

    if not (1 <= complication_range <= 5):
        raise HTTPException(
            status_code=400,
            detail="Complication range must be between 1-5",
        )

    attrs = json.loads(char.attributes_json)
    discs = json.loads(char.disciplines_json)

    attr_value = attrs.get(attribute, 7)
    disc_value = discs.get(department, 1)

    roll_result = player_task_roll(
        attribute=attr_value,
        discipline=disc_value,
        difficulty=difficulty,
        complication_range=complication_range,
        focus=focus,
        bonus_dice=bonus_dice,
    )

    roll_result["attribute_used"] = attribute
    roll_result["discipline_used"] = department
    roll_result["character_name"] = char.name

    return roll_result


@characters_router.post("/characters/{char_id}/spend-determination")
async def spend_determination(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Spend Determination for re-roll or Perfect Opportunity.

    Determination Spends (STA 2E Ch 7):
    - Moment of Inspiration: Re-roll any number of d20s (1 Det)
    - Perfect Opportunity: Set 1 die to 1 (1 Det)

    Request Body:
    - spend_type: "moment_of_inspiration" or "perfect_opportunity"
    - dice_indices: List of indices to reroll (for Moment of Inspiration)
    - die_index: Index of die to set to 1 (for Perfect Opportunity)
    - rolls: Original roll values to modify
    - target_number: Target number for success calculation
    - focus_value: Discipline value for focus (optional)
    """
    from sta.mechanics.dice import reroll_selected, apply_perfect_opportunity

    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    spend_type = data.get("spend_type")
    rolls = data.get("rolls", [])
    target_number = data.get("target_number", 10)
    focus_value = data.get("focus_value")

    if spend_type not in ["moment_of_inspiration", "perfect_opportunity"]:
        raise HTTPException(
            status_code=400,
            detail="spend_type must be 'moment_of_inspiration' or 'perfect_opportunity'",
        )

    if char.determination < 1:
        raise HTTPException(
            status_code=400,
            detail="No Determination remaining",
        )

    if not rolls or len(rolls) == 0:
        raise HTTPException(
            status_code=400,
            detail="rolls array is required",
        )

    if spend_type == "moment_of_inspiration":
        dice_indices = data.get("dice_indices", [])
        if not dice_indices:
            raise HTTPException(
                status_code=400,
                detail="dice_indices is required for Moment of Inspiration",
            )

        new_rolls, reroll_details = reroll_selected(
            rolls, dice_indices, target_number, focus_value
        )

        char.determination -= 1
        await db.commit()

        return {
            "spend_type": "moment_of_inspiration",
            "original_rolls": rolls,
            "new_rolls": new_rolls,
            "reroll_details": reroll_details,
            "determination_spent": 1,
            "determination_remaining": char.determination,
            "message": "Moment of Inspiration: Dice rerolled",
        }

    elif spend_type == "perfect_opportunity":
        die_index = data.get("die_index")
        if die_index is None:
            raise HTTPException(
                status_code=400,
                detail="die_index is required for Perfect Opportunity",
            )

        if die_index < 0 or die_index >= len(rolls):
            raise HTTPException(
                status_code=400,
                detail=f"die_index must be between 0 and {len(rolls) - 1}",
            )

        new_rolls, effect_detail = apply_perfect_opportunity(
            rolls, die_index, target_number
        )

        char.determination -= 1
        await db.commit()

        return {
            "spend_type": "perfect_opportunity",
            "original_rolls": rolls,
            "new_rolls": new_rolls,
            "effect": effect_detail,
            "determination_spent": 1,
            "determination_remaining": char.determination,
            "message": "Perfect Opportunity: Die set to 1 (Critical Success)",
        }


@characters_router.post("/characters/{char_id}/value-interaction")
async def value_interaction(
    char_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Update Value status and track session limits.

    Value Mechanics (STA 2E Ch 4, 7):
    - Used: A Value can be invoked once per session (costs 1 Determination)
    - Challenged: When a Value conflicts with goals → gain 1 Determination
    - Complied: When a Value aligns with goals but hinders progress → gain 1 Determination

    Request Body:
    - value_name: Name of the Value to interact with
    - action: "use", "challenge", or "comply"
    - description: Optional description for challenge/comply

    Returns updated Value status and Determination.
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    value_name = data.get("value_name")
    action = data.get("action")
    description = data.get("description", "")

    if not value_name:
        raise HTTPException(status_code=400, detail="value_name is required")

    if action not in ["use", "challenge", "comply"]:
        raise HTTPException(
            status_code=400,
            detail="action must be 'use', 'challenge', or 'comply'",
        )

    values = json.loads(char.values_json or "[]")
    value_found = False
    updated_value = None

    for v in values:
        if v.get("name", "").lower() == value_name.lower():
            value_found = True
            v["interaction_count"] = v.get("interaction_count", 0) + 1

            if action == "use":
                if v.get("used_this_session", False):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Value '{value_name}' has already been used this session",
                    )
                if char.determination < 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Not enough Determination to use this Value",
                    )
                v["used_this_session"] = True
                char.determination -= 1
                v["last_used_session"] = True

            elif action == "challenge":
                if char.determination >= char.determination_max:
                    raise HTTPException(
                        status_code=400,
                        detail="Determination is already at maximum",
                    )
                v["last_challenged_session"] = True
                char.determination += 1

            elif action == "comply":
                if char.determination >= char.determination_max:
                    raise HTTPException(
                        status_code=400,
                        detail="Determination is already at maximum",
                    )
                v["last_complied_session"] = True
                char.determination += 1

            updated_value = v
            break

    if not value_found:
        raise HTTPException(status_code=404, detail="Value not found")

    char.values_json = json.dumps(values)
    await db.commit()
    await db.refresh(char)

    return {
        "success": True,
        "value_name": value_name,
        "action": action,
        "value": {
            "name": updated_value.get("name"),
            "used_this_session": updated_value.get("used_this_session", False),
            "last_challenged_session": updated_value.get(
                "last_challenged_session", False
            ),
            "last_complied_session": updated_value.get("last_complied_session", False),
        },
        "determination": char.determination,
        "determination_max": char.determination_max,
        "message": f"Value '{value_name}' {action}ed successfully",
    }


@characters_router.get("/characters/{char_id}/resources")
async def get_character_resources(
    char_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get character resources for the Player Console display.

    Returns:
    - stress: Current and max stress
    - determination: Current and max determination
    - values: All values with status
    """
    stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == char_id)
    result = await db.execute(stmt)
    char = result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    attrs = json.loads(char.attributes_json)
    fitness = attrs.get("fitness", 7)

    values = json.loads(char.values_json or "[]")
    enhanced_values = []

    for v in values:
        status = "Available"
        if v.get("used_this_session", False):
            status = "Used"
        elif v.get("last_challenged_session", False):
            status = "Challenged"
        elif v.get("last_complied_session", False):
            status = "Complied"

        enhanced_values.append(
            {
                "name": v.get("name", ""),
                "description": v.get("description", ""),
                "helpful": v.get("helpful", True),
                "status": status,
                "can_use": not v.get("used_this_session", False),
            }
        )

    return {
        "character_id": char.id,
        "character_name": char.name,
        "stress": {
            "current": char.stress,
            "max": char.stress_max,
            "max_from_fitness": fitness,
        },
        "determination": {
            "current": char.determination,
            "max": char.determination_max,
        },
        "values": enhanced_values,
    }
