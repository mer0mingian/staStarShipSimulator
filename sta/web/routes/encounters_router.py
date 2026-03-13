"""Encounter routes for combat management (FastAPI)."""

import json
import uuid
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Query,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sqlalchemy_delete

from sta.database.async_db import get_db
from sta.database.schema import (
    EncounterRecord,
    CharacterRecord,
    StarshipRecord,
    CampaignRecord,
    CampaignPlayerRecord,
    SceneRecord,
    PersonnelEncounterRecord,
)
from sta.models.enums import Position, CrewQuality
from sta.models.combat import (
    ActiveEffect,
)  # Assuming this structure is accessible and usable


# --- STUB CLASSES/FUNCTIONS for migrated code paths ---
class PlaceholderGenerator:
    @staticmethod
    def generate_character():
        return {"id": 9999, "name": "Stubbed Player"}

    @staticmethod
    def generate_enemy_ship(difficulty, crew_quality):
        return {"name": f"Stubbed Enemy ({crew_quality.name})", "scale": 2}


# --- ROUTER SETUP ---
encounters_router = APIRouter(prefix="/encounters")


async def _handle_new_encounter_generation(
    db: AsyncSession, campaign_id_param: str, form_data: dict
) -> EncounterRecord:
    """Stubs character/ship generation and database insertions for POST /new."""

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.campaign_id == campaign_id_param
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign: CampaignRecord = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign_db_id = campaign.id

    if not campaign.active_ship_id:
        raise HTTPException(
            status_code=400, detail="No active ship assigned to campaign."
        )

    ship_id = campaign.active_ship_id

    char_action = form_data.get("character_action", "generate")
    char_id = 0
    if char_action == "generate":
        placeholder_char = PlaceholderGenerator.generate_character()
        char_id = 10000 + uuid.uuid4().int % 1000
    else:
        char_id = int(form_data.get("character_id", 0))

    crew_quality_str = form_data.get("crew_quality", "talented")
    try:
        crew_quality = CrewQuality(crew_quality_str)
    except ValueError:
        crew_quality = CrewQuality.TALENTED

    enemy_count = int(form_data.get("enemy_count", 1))
    enemy_count = max(1, min(4, enemy_count))

    enemy_ids = []
    for _ in range(enemy_count):
        enemy_ids.append(uuid.uuid4().int % 100000 + 20000)

    encounter_name = form_data.get("name", "New Encounter")
    encounter_description = form_data.get("description", "").strip() or None
    position = form_data.get("position", "captain")

    tactical_map_json = form_data.get("tactical_map_json", "{}")
    ship_positions_json = form_data.get("ship_positions_json", "{}")

    initial_status = "active"
    if campaign_db_id and form_data.get("status") == "draft":
        initial_status = "draft"

    encounter = EncounterRecord(
        encounter_id=str(uuid.uuid4()),
        name=encounter_name,
        description=encounter_description,
        campaign_id=campaign_db_id,
        status=initial_status,
        player_character_id=char_id,
        player_ship_id=ship_id,
        player_position=position,
        enemy_ship_ids_json=json.dumps(enemy_ids),
        tactical_map_json=tactical_map_json,
        ship_positions_json=ship_positions_json,
        threat=2,
    )
    db.add(encounter)
    await db.flush()
    await db.refresh(encounter)

    return encounter, campaign, initial_status


# --- ROUTES ---


@encounters_router.post("/new")
async def new_encounter_post(request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new encounter (API POST)."""
    form_data = await request.form()
    campaign_id_param = form_data.get("campaign") or form_data.get("campaign_id")

    if not campaign_id_param:
        raise HTTPException(
            status_code=400,
            detail="Campaign context required (query/form 'campaign_id').",
        )

    try:
        encounter, campaign, initial_status = await _handle_new_encounter_generation(
            db, campaign_id_param, form_data
        )

        if initial_status == "draft":
            return {
                "status": "draft_created",
                "message": "Encounter created as draft.",
                "campaign_id": campaign.campaign_id,
            }

        return {
            "status": "active_created",
            "message": "Encounter started.",
            "encounter_id": encounter.encounter_id,
            "role": "gm",
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create encounter: {e}")


@encounters_router.get("/new")
async def new_encounter_get(campaign_id_param: str = Query(None, alias="campaign")):
    """GET /new is removed for API conversion, only POST is kept."""
    if not campaign_id_param:
        raise HTTPException(
            status_code=400,
            detail="Please provide campaign context via 'campaign' query parameter.",
        )

    return {
        "message": "Use POST method to create an encounter.",
        "campaign_id": campaign_id_param,
        "action_required": "POST",
    }


@encounters_router.post("/{encounter_id}/edit")
async def edit_encounter_post(
    encounter_id: str,
    name: str = Form(None),
    description: Optional[str] = Form(None),
    threat: int = Form(None),
    tactical_map_json: Optional[str] = Form(None),
    ship_positions_json: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Edit an existing encounter (API POST submission)."""

    encounter_stmt = select(EncounterRecord).filter(
        EncounterRecord.encounter_id == encounter_id
    )
    encounter_result = await db.execute(encounter_stmt)
    encounter: Optional[EncounterRecord] = encounter_result.scalars().first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.id == encounter.campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign: Optional[CampaignRecord] = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Update fields if provided
    if name is not None:
        encounter.name = name
    if description is not None:
        encounter.description = description.strip() or None
    if threat is not None:
        encounter.threat = threat

    if tactical_map_json is not None:
        encounter.tactical_map_json = tactical_map_json

    if ship_positions_json is not None:
        encounter.ship_positions_json = ship_positions_json

    await db.commit()

    return {
        "status": "updated",
        "message": "Encounter updated successfully",
        "campaign_id": campaign.campaign_id,
    }


@encounters_router.get("/{encounter_id}/edit")
async def edit_encounter_get(encounter_id: str, db: AsyncSession = Depends(get_db)):
    """Edit an existing encounter (GET returns data for form fill)."""

    encounter_stmt = select(EncounterRecord).filter(
        EncounterRecord.encounter_id == encounter_id
    )
    encounter_result = await db.execute(encounter_stmt)
    encounter: Optional[EncounterRecord] = encounter_result.scalars().first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.id == encounter.campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign: Optional[CampaignRecord] = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    player_ship_model = None
    if encounter.player_ship_id:
        ship_stmt = select(StarshipRecord).filter(
            StarshipRecord.id == encounter.player_ship_id
        )
        ship_result = await db.execute(ship_stmt)
        ship_record = ship_result.scalars().first()
        if ship_record:
            player_ship_model = ship_record.to_model()

    enemy_ship_ids = json.loads(encounter.enemy_ship_ids_json or "[]")
    enemy_ships_models = []
    for eid in enemy_ship_ids:
        enemy_stmt = select(StarshipRecord).filter(StarshipRecord.id == eid)
        enemy_result = await db.execute(enemy_stmt)
        enemy_record = enemy_result.scalars().first()
        if enemy_record:
            enemy_ships_models.append(enemy_record.to_model())

    data = {
        "encounter": encounter.__dict__,
        "campaign_id_str": campaign.campaign_id,
        "player_ship": player_ship_model.__dict__ if player_ship_model else None,
        "enemy_ships": [e.__dict__ for e in enemy_ships_models],
        "tactical_map_json": encounter.tactical_map_json or "{}",
        "ship_positions_json": encounter.ship_positions_json or "{}",
    }
    return data


@encounters_router.get("/{encounter_id}")
async def combat_data(
    encounter_id: str, role: str = Query("player"), db: AsyncSession = Depends(get_db)
):
    """Main combat view - returns state data as JSON."""
    if role not in ("player", "gm", "viewscreen"):
        role = "player"

    encounter_stmt = select(EncounterRecord).filter(
        EncounterRecord.encounter_id == encounter_id
    )
    encounter_result = await db.execute(encounter_stmt)
    encounter: Optional[EncounterRecord] = encounter_result.scalars().first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    # STUB: Authentication/Authorization checks based on cookies are removed.

    # Load Ship Data
    player_ship_model = None
    if encounter.player_ship_id:
        ship_stmt = select(StarshipRecord).filter(
            StarshipRecord.id == encounter.player_ship_id
        )
        ship_result = await db.execute(ship_stmt)
        ship_record = ship_result.scalars().first()
        if ship_record:
            player_ship_model = ship_record.to_model()

    # Load enemy ships
    enemy_ids = json.loads(encounter.enemy_ship_ids_json or "[]")
    enemy_ships_models = []
    enemy_ship_db_ids = []
    for eid in enemy_ids:
        enemy_stmt = select(StarshipRecord).filter(StarshipRecord.id == eid)
        enemy_result = await db.execute(enemy_stmt)
        enemy_record = enemy_result.scalars().first()
        if enemy_record:
            enemy_ships_models.append(enemy_record.to_model())
            enemy_ship_db_ids.append(eid)

    # Load Player Character / Position Logic Stub
    player_char_model = None
    if encounter.player_character_id:
        char_stmt = select(CharacterRecord).filter(
            CharacterRecord.id == encounter.player_character_id
        )
        char_result = await db.execute(char_stmt)
        char_record = char_result.scalars().first()
        if char_record:
            player_char_model = char_record.to_model()

    # Load Active Effects (Stubbed)
    active_effects_data = json.loads(encounter.active_effects_json or "[]")
    active_effects = (
        [ActiveEffect.from_dict(e) for e in active_effects_data]
        if active_effects_data
        else []
    )
    resistance_bonus = sum(
        e.resistance_bonus
        for e in active_effects
        if hasattr(e, "resistance_bonus") and e.resistance_bonus > 0
    )

    # Load Tactical Map Data
    tactical_map_data = json.loads(encounter.tactical_map_json or "{}")
    if not tactical_map_data or "radius" not in tactical_map_data:
        tactical_map_data = {"radius": 3, "tiles": []}

    ship_positions_data = json.loads(encounter.ship_positions_json or "{}")
    ship_positions_list = []

    player_pos = ship_positions_data.get("player", {"q": 0, "r": 0})
    if player_ship_model:
        ship_positions_list.append(
            {
                "id": "player",
                "name": player_ship_model.name,
                "faction": "player",
                "position": player_pos,
            }
        )

    for i, _ in enumerate(enemy_ids):
        enemy_pos = ship_positions_data.get(f"enemy_{i}", {"q": 2, "r": -1 + i})
        ship_positions_list.append(
            {
                "id": f"enemy_{i}",
                "name": f"Enemy {i}",
                "faction": "enemy",
                "position": enemy_pos,
            }
        )

    # Load Scene Info Stub
    scene_data = None
    campaign = None
    if encounter.campaign_id:
        campaign_stmt = select(CampaignRecord).filter(
            CampaignRecord.id == encounter.campaign_id
        )
        campaign_result = await db.execute(campaign_stmt)
        campaign = campaign_result.scalars().first()

        scene_stmt = select(SceneRecord).filter(
            SceneRecord.encounter_id == encounter.id
        )
        scene_result = await db.execute(scene_stmt)
        scene = scene_result.scalars().first()

        if scene:
            scene_data = {
                "stardate": scene.stardate if hasattr(scene, "stardate") else "N/A",
                "scene_traits": json.loads(scene.scene_traits_json or "[]"),
            }

    return {
        "role": role,
        "encounter_data": encounter.__dict__,
        "campaign": campaign.__dict__ if campaign else None,
        "player_char": player_char_model.__dict__ if player_char_model else None,
        "player_ship": player_ship_model.__dict__ if player_ship_model else None,
        "enemy_ships": [e.__dict__ for e in enemy_ships_models],
        "player_position": encounter.player_position,
        "resistance_bonus": resistance_bonus,
        "tactical_map": tactical_map_data,
        "ship_positions": ship_positions_list,
        "scene": scene_data,
    }


@encounters_router.delete("/{encounter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_encounter(encounter_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an encounter."""

    encounter_id_stmt = select(EncounterRecord.id).filter(
        EncounterRecord.encounter_id == encounter_id
    )
    encounter_id_result = await db.execute(encounter_id_stmt)
    encounter_db_id = encounter_id_result.scalars().first()

    if not encounter_db_id:
        raise HTTPException(status_code=404, detail="Encounter not found")

    # Delete Personnel Encounter (must delete related scene first if cascade isn't set up)
    await db.execute(
        sqlalchemy_delete(PersonnelEncounterRecord).where(
            PersonnelEncounterRecord.scene_id.in_(
                select(SceneRecord.id).where(
                    SceneRecord.encounter_id == encounter_db_id
                )
            )
        )
    )

    # Delete related Scene if it exists
    await db.execute(
        sqlalchemy_delete(SceneRecord).where(
            SceneRecord.encounter_id == encounter_db_id
        )
    )

    # Delete Encounter record itself
    delete_stmt = sqlalchemy_delete(EncounterRecord).where(
        EncounterRecord.id == encounter_db_id
    )
    await db.execute(delete_stmt)

    await db.commit()
    return {"detail": "Encounter deleted"}


@encounters_router.get("/personnel/{scene_id}")
async def personnel_combat_data(
    scene_id: int, role: str = Query("player"), db: AsyncSession = Depends(get_db)
):
    """Personnel combat view - returns state data as JSON."""
    if role not in ("player", "gm", "viewscreen"):
        role = "player"

    enc_stmt = select(PersonnelEncounterRecord).filter(
        PersonnelEncounterRecord.scene_id == scene_id
    )
    enc_result = await db.execute(enc_stmt)
    encounter: Optional[PersonnelEncounterRecord] = enc_result.scalars().first()

    scene = None
    if encounter:
        scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
        scene_result = await db.execute(scene_stmt)
        scene = scene_result.scalars().first()

    if not encounter or not scene:
        raise HTTPException(
            status_code=404, detail="Personnel encounter or associated scene not found."
        )

    character_states = json.loads(encounter.character_states_json or "[]")
    character_positions = json.loads(encounter.character_positions_json or "{}")

    characters = []
    for i, char_state in enumerate(character_states):
        char_key = f"character_{i}"
        pos = character_positions.get(char_key, {"q": 0, "r": 0})

        characters.append(
            {
                "index": i,
                "name": char_state.get("name", f"Character {i}"),
                "is_player": char_state.get("is_player", False),
                "stress": char_state.get("stress", 5),
                "stress_max": char_state.get("stress_max", 5),
                "injuries": char_state.get("injuries", []),
                "is_defeated": char_state.get("is_defeated", False),
                "position": pos,
            }
        )

    minor_actions = [
        "Personnel Aim",
        "Draw Item",
        "Personnel Interact",
        "Personnel Movement",
        "Personnel Prepare",
        "Stand/Drop Prone",
    ]
    major_actions = [
        "Personnel Attack",
        "First Aid",
        "Guard",
        "Sprint",
        "Personnel Assist",
        "Create Trait",
        "Personnel Direct",
        "Ready",
        "Personnel Pass",
    ]

    active_character = (
        characters[0]
        if characters
        else {
            "name": "None",
            "is_defeated": True,
            "stress": 0,
            "stress_max": 5,
            "injuries": [],
        }
    )

    tactical_map = json.loads(encounter.tactical_map_json or "{}")

    return {
        "scene_id": scene_id,
        "scene_name": scene.name,
        "turn_info": {
            "current_turn": encounter.current_turn,
            "round": encounter.round,
            "momentum": encounter.momentum,
            "threat": encounter.threat,
        },
        "characters": characters,
        "active_character_index": 0,
        "active_character": active_character,
        "minor_actions": minor_actions,
        "major_actions": major_actions,
        "tactical_map": tactical_map,
        "role": role,
    }
