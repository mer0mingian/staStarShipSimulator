"""Ship routes for VTT ship management (FastAPI)."""

import json
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Body,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sta.database.async_db import get_db
from sta.database.schema import (
    CampaignRecord,
    CampaignPlayerRecord,
)
from sta.database.vtt_schema import (
    VTTShipRecord,
)
from sta.models.enums import SystemType, CrewQuality

ships_router = APIRouter(tags=["ships"])


def _serialize_ship(ship: VTTShipRecord) -> dict:
    """Serialize a VTTShipRecord to JSON."""
    return {
        "id": ship.id,
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
        "token_url": ship.token_url,
        "token_scale": ship.token_scale,
        "is_visible_to_players": ship.is_visible_to_players,
        "vtt_position_json": json.loads(ship.vtt_position_json),
        "vtt_status_effects_json": json.loads(ship.vtt_status_effects_json),
        "vtt_facing_direction": ship.vtt_facing_direction,
        "campaign_id": ship.campaign_id,
        "scene_id": ship.scene_id,
        "created_at": ship.created_at.isoformat() if ship.created_at else None,
        "updated_at": ship.updated_at.isoformat() if ship.updated_at else None,
    }


# =============================================================================
# Ship CRUD Endpoints
# =============================================================================


@ships_router.get("/ships")
async def list_ships(
    campaign_id: Optional[int] = None, db: AsyncSession = Depends(get_db)
):
    """List all ships with optional filters: campaign_id."""
    query = select(VTTShipRecord)

    if campaign_id is not None:
        query = query.filter(VTTShipRecord.campaign_id == campaign_id)

    result = await db.execute(query)
    ships = result.scalars().all()
    return [_serialize_ship(s) for s in ships]


@ships_router.get("/ships/{ship_id}")
async def get_ship(ship_id: int, db: AsyncSession = Depends(get_db)):
    """Get single ship with full details."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    return _serialize_ship(ship)


@ships_router.post("/ships", status_code=status.HTTP_201_CREATED)
async def create_ship(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Create new ship with validation."""
    name = data.get("name", "Unnamed Ship")
    ship_class = data.get("ship_class")
    registry = data.get("registry")
    scale = data.get("scale", 4)
    systems = data.get("systems", {})
    departments = data.get("departments", {})
    weapons = data.get("weapons", [])
    talents = data.get("talents", [])
    traits = data.get("traits", [])
    breaches = data.get("breaches", [])
    shields = data.get("shields", 0)
    shields_max = data.get("shields_max", 0)
    resistance = data.get("resistance", 0)
    has_reserve_power = data.get("has_reserve_power", True)
    shields_raised = data.get("shields_raised", False)
    weapons_armed = data.get("weapons_armed", False)
    crew_quality = data.get("crew_quality")
    campaign_id = data.get("campaign_id")
    is_visible_to_players = data.get("is_visible_to_players", True)

    for sys_name, value in systems.items():
        if not (7 <= value <= 12):
            raise HTTPException(
                status_code=400,
                detail=f"System {sys_name} must be between 7-12, got {value}",
            )

    for dept_name, value in departments.items():
        if not (0 <= value <= 5):
            raise HTTPException(
                status_code=400,
                detail=f"Department {dept_name} must be between 0-5, got {value}",
            )

    if not (1 <= scale <= 7):
        raise HTTPException(
            status_code=400, detail=f"Scale must be between 1-7, got {scale}"
        )

    ship = VTTShipRecord(
        name=name,
        ship_class=ship_class,
        ship_registry=registry,
        scale=scale,
        systems_json=json.dumps(systems),
        departments_json=json.dumps(departments),
        weapons_json=json.dumps(weapons),
        talents_json=json.dumps(talents),
        traits_json=json.dumps(traits),
        breaches_json=json.dumps(breaches),
        shields=shields,
        shields_max=shields_max,
        resistance=resistance,
        has_reserve_power=has_reserve_power,
        shields_raised=shields_raised,
        weapons_armed=weapons_armed,
        crew_quality=crew_quality,
        campaign_id=campaign_id,
        is_visible_to_players=is_visible_to_players,
    )

    db.add(ship)
    await db.commit()
    await db.refresh(ship)

    return _serialize_ship(ship)


@ships_router.put("/ships/{ship_id}")
async def update_ship(
    ship_id: int,
    db: AsyncSession = Depends(get_db),
    name: Optional[str] = Body(None, embed=True),
    ship_class: Optional[str] = Body(None, embed=True),
    ship_registry: Optional[str] = Body(None, embed=True),
    campaign_id: Optional[int] = Body(None, embed=True),
    scene_id: Optional[int] = Body(None, embed=True),
    is_visible_to_players: Optional[bool] = Body(None, embed=True),
    token_url: Optional[str] = Body(None, embed=True),
    token_scale: Optional[int] = Body(None, embed=True),
    vtt_facing_direction: Optional[int] = Body(None, embed=True),
    crew_quality: Optional[str] = Body(None, embed=True),
    scale: Optional[int] = Body(None, embed=True),
    shields: Optional[int] = Body(None, embed=True),
    shields_max: Optional[int] = Body(None, embed=True),
    resistance: Optional[int] = Body(None, embed=True),
    has_reserve_power: Optional[bool] = Body(None, embed=True),
    shields_raised: Optional[bool] = Body(None, embed=True),
    weapons_armed: Optional[bool] = Body(None, embed=True),
    systems_json: Optional[str] = Body(None, embed=True),
    departments_json: Optional[str] = Body(None, embed=True),
    weapons_json: Optional[str] = Body(None, embed=True),
    talents_json: Optional[str] = Body(None, embed=True),
    traits_json: Optional[str] = Body(None, embed=True),
    breaches_json: Optional[str] = Body(None, embed=True),
    vtt_position_json: Optional[str] = Body(None, embed=True),
    vtt_status_effects_json: Optional[str] = Body(None, embed=True),
):
    """Update ship with validation."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    if name is not None:
        ship.name = name
    if ship_class is not None:
        ship.ship_class = ship_class
    if ship_registry is not None:
        ship.ship_registry = ship_registry
    if campaign_id is not None:
        ship.campaign_id = campaign_id
    if scene_id is not None:
        ship.scene_id = scene_id
    if is_visible_to_players is not None:
        ship.is_visible_to_players = is_visible_to_players
    if token_url is not None:
        ship.token_url = token_url
    if token_scale is not None:
        ship.token_scale = token_scale
    if vtt_facing_direction is not None:
        ship.vtt_facing_direction = vtt_facing_direction
    if crew_quality is not None:
        if crew_quality is not None:
            try:
                CrewQuality(crew_quality)
            except ValueError:
                valid_qualities = [q.value for q in CrewQuality]
                raise HTTPException(
                    status_code=400,
                    detail=f"crew_quality must be one of {valid_qualities}",
                )
        ship.crew_quality = crew_quality

    if scale is not None:
        if not (1 <= scale <= 7):
            raise HTTPException(
                status_code=400, detail=f"Scale must be between 1-7, got {scale}"
            )
        ship.scale = scale

    if shields is not None or shields_max is not None:
        shields_max_val = shields_max if shields_max is not None else ship.shields_max
        shields_val = shields if shields is not None else ship.shields
        if shields_max_val < 0:
            raise HTTPException(
                status_code=400, detail="Shields max cannot be negative"
            )
        if not (0 <= shields_val <= shields_max_val):
            raise HTTPException(
                status_code=400,
                detail=f"Shields must be between 0-{shields_max_val}, got {shields_val}",
            )
        if shields is not None:
            ship.shields = shields
        if shields_max is not None:
            ship.shields_max = shields_max

    if resistance is not None:
        ship.resistance = resistance
    if has_reserve_power is not None:
        ship.has_reserve_power = has_reserve_power
    if shields_raised is not None:
        ship.shields_raised = shields_raised
    if weapons_armed is not None:
        ship.weapons_armed = weapons_armed

    if systems_json is not None:
        try:
            systems = json.loads(systems_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid systems JSON")
        for sys_name, value in systems.items():
            if not (7 <= value <= 12):
                raise HTTPException(
                    status_code=400,
                    detail=f"System {sys_name} must be between 7-12, got {value}",
                )
        ship.systems_json = systems_json

    if departments_json is not None:
        try:
            departments = json.loads(departments_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid departments JSON")
        for dept_name, value in departments.items():
            if not (0 <= value <= 5):
                raise HTTPException(
                    status_code=400,
                    detail=f"Department {dept_name} must be between 0-5, got {value}",
                )
        ship.departments_json = departments_json

    if weapons_json is not None:
        ship.weapons_json = weapons_json
    if talents_json is not None:
        ship.talents_json = talents_json
    if traits_json is not None:
        ship.traits_json = traits_json
    if breaches_json is not None:
        ship.breaches_json = breaches_json
    if vtt_position_json is not None:
        ship.vtt_position_json = vtt_position_json
    if vtt_status_effects_json is not None:
        ship.vtt_status_effects_json = vtt_status_effects_json

    await db.commit()
    await db.refresh(ship)
    return _serialize_ship(ship)


@ships_router.delete("/ships/{ship_id}")
async def delete_ship(
    ship_id: int,
    db: AsyncSession = Depends(get_db),
    campaign_id: Optional[int] = None,
    sta_session_token: Optional[str] = None,
):
    """Delete ship (GM only)."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    if ship.campaign_id:
        if not sta_session_token:
            raise HTTPException(status_code=401, detail="GM authentication required")

        gm_stmt = select(CampaignPlayerRecord).filter(
            CampaignPlayerRecord.campaign_id == ship.campaign_id,
            CampaignPlayerRecord.is_gm == True,
        )
        gm_result = await db.execute(gm_stmt)
        gm_player = gm_result.scalars().first()

        if not gm_player or sta_session_token != gm_player.session_token:
            raise HTTPException(status_code=401, detail="GM authentication required")

    await db.delete(ship)
    await db.commit()
    return {"success": True}


# =============================================================================
# Ship Model Endpoint
# =============================================================================


@ships_router.get("/ships/{ship_id}/model")
async def get_ship_model(ship_id: int, db: AsyncSession = Depends(get_db)):
    """Return ship as legacy Starship model."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    model = ship.to_model()

    return {
        "name": model.name,
        "ship_class": model.ship_class,
        "registry": model.registry,
        "scale": model.scale,
        "systems": {
            "comms": model.systems.comms,
            "computers": model.systems.computers,
            "engines": model.systems.engines,
            "sensors": model.systems.sensors,
            "structure": model.systems.structure,
            "weapons": model.systems.weapons,
        },
        "departments": {
            "command": model.departments.command,
            "conn": model.departments.conn,
            "engineering": model.departments.engineering,
            "medicine": model.departments.medicine,
            "science": model.departments.science,
            "security": model.departments.security,
        },
        "weapons": [
            {
                "name": w.name,
                "weapon_type": w.weapon_type.value,
                "damage": w.damage,
                "range": w.range.value,
                "qualities": w.qualities,
                "requires_calibration": w.requires_calibration,
            }
            for w in model.weapons
        ],
        "talents": model.talents,
        "traits": model.traits,
        "breaches": [
            {"system": b.system.value, "potency": b.potency} for b in model.breaches
        ],
        "shields": model.shields,
        "shields_max": model.shields_max,
        "resistance": model.resistance,
        "has_reserve_power": model.has_reserve_power,
        "shields_raised": model.shields_raised,
        "weapons_armed": model.weapons_armed,
        "crew_quality": model.crew_quality.value if model.crew_quality else None,
    }


# =============================================================================
# Ship Shields Endpoints
# =============================================================================


@ships_router.put("/ships/{ship_id}/shields")
async def adjust_shields(
    ship_id: int,
    shields: Optional[int] = Body(None, embed=True),
    raised: Optional[bool] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Adjust shields."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    if shields is not None:
        if not (0 <= shields <= ship.shields_max):
            raise HTTPException(
                status_code=400,
                detail=f"Shields must be between 0-{ship.shields_max}, got {shields}",
            )
        ship.shields = shields

    if raised is not None:
        ship.shields_raised = raised

    await db.commit()

    return {
        "shields": ship.shields,
        "shields_max": ship.shields_max,
        "shields_raised": ship.shields_raised,
    }


# =============================================================================
# Ship Power Endpoints
# =============================================================================


@ships_router.put("/ships/{ship_id}/power")
async def adjust_power(
    ship_id: int,
    current: Optional[int] = Body(None, embed=True),
    reserve: Optional[bool] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Adjust power."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    if current is not None:
        if current not in [0, 1]:
            raise HTTPException(status_code=400, detail="current power must be 0 or 1")
        ship.has_reserve_power = current == 1

    if reserve is not None:
        ship.has_reserve_power = reserve

    await db.commit()

    return {
        "has_reserve_power": ship.has_reserve_power,
    }


# =============================================================================
# Ship Breach Endpoints
# =============================================================================


@ships_router.put("/ships/{ship_id}/breach")
async def adjust_breach(
    ship_id: int,
    system: str = Body(..., embed=True),
    potency: int = Body(1, embed=True),
    action: str = Body("add", embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Add/remove system breach."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    try:
        system_type = SystemType(system)
    except ValueError:
        valid_systems = [s.value for s in SystemType]
        raise HTTPException(
            status_code=400, detail=f"Invalid system. Must be one of {valid_systems}"
        )

    breaches = json.loads(ship.breaches_json)

    if action == "add":
        existing = [b for b in breaches if b["system"] == system]
        if existing:
            existing[0]["potency"] = potency
        else:
            breaches.append({"system": system, "potency": potency})
    elif action == "remove":
        breaches = [b for b in breaches if b["system"] != system]
    else:
        raise HTTPException(status_code=400, detail="action must be 'add' or 'remove'")

    ship.breaches_json = json.dumps(breaches)
    await db.commit()

    return {
        "breaches": breaches,
    }


# =============================================================================
# Ship Weapons Endpoints
# =============================================================================


@ships_router.put("/ships/{ship_id}/weapons")
async def update_weapons(
    ship_id: int,
    weapons: list = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Update weapons list."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    ship.weapons_json = json.dumps(weapons)
    await db.commit()

    return {
        "weapons": weapons,
    }


@ships_router.post("/ships/{ship_id}/weapons/{weapon_name}/arm")
async def arm_weapon(
    ship_id: int,
    weapon_name: str,
    armed: bool = Body(True, embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Arm/disarm weapon."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    weapons = json.loads(ship.weapons_json)

    weapon_found = False
    for weapon in weapons:
        if weapon.get("name") == weapon_name:
            weapon_found = True
            break

    if not weapon_found:
        raise HTTPException(status_code=404, detail=f"Weapon '{weapon_name}' not found")

    ship.weapons_armed = armed
    await db.commit()

    return {
        "weapons_armed": ship.weapons_armed,
        "weapon_name": weapon_name,
        "armed": armed,
    }


# =============================================================================
# Ship Crew Quality Endpoints
# =============================================================================


@ships_router.get("/ships/{ship_id}/crew-quality")
async def get_crew_quality(ship_id: int, db: AsyncSession = Depends(get_db)):
    """Get crew quality (NPC ships only)."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    return {
        "crew_quality": ship.crew_quality,
    }


@ships_router.put("/ships/{ship_id}/crew-quality")
async def set_crew_quality(
    ship_id: int,
    crew_quality: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Set crew quality (NPC ships only)."""
    stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    result = await db.execute(stmt)
    ship = result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    if crew_quality is not None:
        try:
            CrewQuality(crew_quality)
        except ValueError:
            valid_qualities = [q.value for q in CrewQuality]
            raise HTTPException(
                status_code=400, detail=f"crew_quality must be one of {valid_qualities}"
            )

    ship.crew_quality = crew_quality
    await db.commit()

    return {
        "crew_quality": ship.crew_quality,
    }


# Export endpoint
@ships_router.get("/ships/{ship_id}/export")
async def export_ship(
    ship_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export a VTT ship as JSON."""
    ship = (
        (await db.execute(select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)))
        .scalars()
        .first()
    )
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    return {
        "id": ship.id,
        "name": ship.name,
        "ship_class": ship.ship_class,
        "systems": json.loads(ship.systems_json or "{}"),
        "departments": json.loads(ship.departments_json or "{}"),
        "weapons": json.loads(ship.weapons_json or "[]"),
        "talents": json.loads(ship.talents_json or "[]"),
    }


@ships_router.post("/ships/import")
async def import_ship(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Import a VTT ship from JSON."""
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    ship = VTTShipRecord(
        name=name,
        ship_class=data.get("ship_class", "Unknown"),
        systems_json=json.dumps(data.get("systems", {})),
        departments_json=json.dumps(data.get("departments", {})),
        weapons_json=json.dumps(data.get("weapons", [])),
        talents_json=json.dumps(data.get("talents", [])),
    )
    db.add(ship)
    await db.commit()

    return {
        "id": ship.id,
        "name": ship.name,
        "success": True,
    }
