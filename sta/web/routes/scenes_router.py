"""Scene routes for scene management (FastAPI)."""

import json
import uuid
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Body,
    Form,
    Query,
    Cookie,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from sta.database.async_db import get_db
from sta.database.schema import (
    SceneRecord,
    CampaignRecord,
    CampaignPlayerRecord,
    SceneNPCRecord,
    NPCRecord,
    CampaignNPCRecord,
    StarshipRecord,
    CampaignShipRecord,
    EncounterRecord,
    PersonnelEncounterRecord,
    SceneParticipantRecord,
    SceneShipRecord,
)
from sta.database.vtt_schema import (
    VTTCharacterRecord,
    VTTShipRecord,
)
from sta.models.enums import Position

scenes_router = APIRouter(prefix="/scenes", tags=["scenes"])


async def _require_gm_auth(
    campaign_id: int,
    sta_session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
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
# Scene NPCs API
# =============================================================================


@scenes_router.get("/{scene_id}/npcs")
async def get_scene_npcs(scene_id: int, db: AsyncSession = Depends(get_db)):
    """Get NPCs for a scene."""
    stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    result = await db.execute(stmt)
    scene = result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene_npcs_stmt = (
        select(SceneNPCRecord)
        .filter(SceneNPCRecord.scene_id == scene_id)
        .order_by(SceneNPCRecord.order_index)
    )
    scene_npcs_result = await db.execute(scene_npcs_stmt)
    scene_npcs = scene_npcs_result.scalars().all()

    npcs = []
    for sn in scene_npcs:
        npc_data = {
            "id": sn.id,
            "is_visible": sn.is_visible_to_players,
        }
        if sn.npc_id:
            npc_stmt = select(NPCRecord).filter(NPCRecord.id == sn.npc_id)
            npc_result = await db.execute(npc_stmt)
            npc = npc_result.scalars().first()
            if npc:
                npc_data["name"] = npc.name
                npc_data["npc_type"] = npc.npc_type
                npc_data["npc_id"] = npc.id
        elif sn.quick_name:
            npc_data["name"] = sn.quick_name
            npc_data["npc_type"] = "quick"
        npcs.append(npc_data)

    return {"npcs": npcs}


@scenes_router.put("/{scene_id}/npcs/{npc_id}/visibility")
async def toggle_npc_visibility(
    scene_id: int,
    npc_id: int,
    is_visible: bool = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Toggle NPC visibility."""
    stmt = select(SceneNPCRecord).filter(
        SceneNPCRecord.id == npc_id,
        SceneNPCRecord.scene_id == scene_id,
    )
    result = await db.execute(stmt)
    scene_npc = result.scalars().first()

    if not scene_npc:
        raise HTTPException(status_code=404, detail="NPC not found in scene")

    scene_npc.is_visible_to_players = is_visible
    await db.commit()

    return {"success": True, "is_visible": scene_npc.is_visible_to_players}


@scenes_router.get("/{scene_id}/npcs/available")
async def get_available_npcs(scene_id: int, db: AsyncSession = Depends(get_db)):
    """Get NPCs available to add to scene (from campaign manifest + archive)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    campaign_id = scene.campaign_id

    available = []

    campaign_npcs_stmt = select(CampaignNPCRecord).filter(
        CampaignNPCRecord.campaign_id == campaign_id
    )
    campaign_npcs_result = await db.execute(campaign_npcs_stmt)
    campaign_npcs = campaign_npcs_result.scalars().all()

    for cn in campaign_npcs:
        npc_stmt = select(NPCRecord).filter(NPCRecord.id == cn.npc_id)
        npc_result = await db.execute(npc_stmt)
        npc = npc_result.scalars().first()
        if npc:
            existing_stmt = select(SceneNPCRecord).filter(
                SceneNPCRecord.scene_id == scene_id,
                SceneNPCRecord.npc_id == npc.id,
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalars().first()
            if not existing:
                available.append(
                    {
                        "id": npc.id,
                        "name": npc.name,
                        "npc_type": npc.npc_type,
                        "source": "campaign",
                    }
                )

    return {"npcs": available}


@scenes_router.post("/{scene_id}/npcs")
async def add_npc_to_scene(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    npc_id: Optional[int] = Body(None, embed=True),
    quick_name: Optional[str] = Body(None, embed=True),
    quick_description: Optional[str] = Body("", embed=True),
    is_visible: bool = Body(False, embed=True),
):
    """Add an NPC to a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_stmt.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    count_stmt = select(func.count(SceneNPCRecord.id)).filter(
        SceneNPCRecord.scene_id == scene_id
    )
    count_result = await db.execute(count_stmt)
    max_order = count_result.scalar() or 0

    if npc_id:
        npc_stmt = select(NPCRecord).filter(NPCRecord.id == npc_id)
        npc_result = await db.execute(npc_stmt)
        npc = npc_result.scalars().first()

        if not npc:
            raise HTTPException(status_code=404, detail="NPC not found")

        existing_stmt = select(SceneNPCRecord).filter(
            SceneNPCRecord.scene_id == scene_id,
            SceneNPCRecord.npc_id == npc_id,
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalars().first()

        if existing:
            raise HTTPException(status_code=400, detail="NPC already in scene")

        scene_npc = SceneNPCRecord(
            scene_id=scene_id,
            npc_id=npc_id,
            is_visible_to_players=is_visible,
            order_index=max_order,
        )
        db.add(scene_npc)
        await db.commit()

        return {
            "success": True,
            "scene_npc_id": scene_npc.id,
            "name": npc.name,
            "npc_type": npc.npc_type,
            "is_visible": scene_npc.is_visible_to_players,
        }

    elif quick_name:
        quick_name = quick_name.strip()
        if not quick_name:
            raise HTTPException(status_code=400, detail="Name is required")

        scene_npc = SceneNPCRecord(
            scene_id=scene_id,
            quick_name=quick_name,
            quick_description=quick_description,
            is_visible_to_players=is_visible,
            order_index=max_order,
        )
        db.add(scene_npc)
        await db.commit()

        return {
            "success": True,
            "scene_npc_id": scene_npc.id,
            "name": quick_name,
            "npc_type": "quick",
            "is_visible": scene_npc.is_visible_to_players,
        }

    raise HTTPException(status_code=400, detail="npc_id or quick_name required")


@scenes_router.delete("/{scene_id}/npcs/{scene_npc_id}")
async def remove_npc_from_scene(
    scene_id: int, scene_npc_id: int, db: AsyncSession = Depends(get_db)
):
    """Remove an NPC from a scene."""
    stmt = select(SceneNPCRecord).filter(
        SceneNPCRecord.id == scene_npc_id,
        SceneNPCRecord.scene_id == scene_id,
    )
    result = await db.execute(stmt)
    scene_npc = result.scalars().first()

    if not scene_npc:
        raise HTTPException(status_code=404, detail="NPC not found in scene")

    await db.delete(scene_npc)
    await db.commit()

    return {"success": True}


# =============================================================================
# Scene Connections API
# =============================================================================


@scenes_router.get("/{scene_id}/connections")
async def get_scene_connections(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get scene connections (next and previous scene IDs)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    next_ids = json.loads(scene.next_scene_ids_json or "[]")
    previous_ids = json.loads(scene.previous_scene_ids_json or "[]")
    return {"next_scene_ids": next_ids, "previous_scene_ids": previous_ids}


@scenes_router.put("/{scene_id}/connections")
async def update_scene_connections(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
    next_scene_ids: Optional[list] = Body(None, embed=True),
    previous_scene_ids: Optional[list] = Body(None, embed=True),
):
    """Update scene connections (replace with given lists)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    current_next_ids = json.loads(scene.next_scene_ids_json or "[]")
    current_previous_ids = json.loads(scene.previous_scene_ids_json or "[]")

    if next_scene_ids is not None:
        try:
            next_ids_input = [int(i) for i in next_scene_ids]
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="next_scene_ids must be integers"
            )

        valid_next_ids = []
        for nid in next_ids_input:
            target_stmt = select(SceneRecord).filter(
                SceneRecord.id == nid,
                SceneRecord.campaign_id == scene.campaign_id,
            )
            target_result = await db.execute(target_stmt)
            target = target_result.scalars().first()
            if target:
                valid_next_ids.append(nid)
        next_ids = valid_next_ids
    else:
        next_ids = current_next_ids

    if previous_scene_ids is not None:
        try:
            prev_ids_input = [int(i) for i in previous_scene_ids]
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="previous_scene_ids must be integers"
            )

        valid_prev_ids = []
        for pid in prev_ids_input:
            target_stmt = select(SceneRecord).filter(
                SceneRecord.id == pid,
                SceneRecord.campaign_id == scene.campaign_id,
            )
            target_result = await db.execute(target_stmt)
            target = target_result.scalars().first()
            if target:
                valid_prev_ids.append(pid)
        previous_ids = valid_prev_ids
    else:
        previous_ids = current_previous_ids

    scene.next_scene_ids_json = json.dumps(next_ids)
    scene.previous_scene_ids_json = json.dumps(previous_ids)
    await db.commit()

    return {
        "success": True,
        "next_scene_ids": next_ids,
        "previous_scene_ids": previous_ids,
    }


@scenes_router.post("/{scene_id}/connections/next")
async def add_next_connection(
    scene_id: int,
    target_scene_id: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Add a next scene connection (bidirectional)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if target_scene_id == scene_id:
        raise HTTPException(status_code=400, detail="Cannot connect scene to itself")

    next_ids = json.loads(scene.next_scene_ids_json or "[]")
    if target_scene_id in next_ids:
        raise HTTPException(status_code=400, detail="Scenes already connected")

    target_stmt = select(SceneRecord).filter(SceneRecord.id == target_scene_id)
    target_result = await db.execute(target_stmt)
    target = target_result.scalars().first()

    if not target:
        raise HTTPException(status_code=400, detail="Target scene not found")

    if target.campaign_id != scene.campaign_id:
        raise HTTPException(
            status_code=400, detail="Target scene must be in same campaign"
        )

    next_ids.append(target_scene_id)
    scene.next_scene_ids_json = json.dumps(next_ids)

    previous_ids = json.loads(target.previous_scene_ids_json or "[]")
    if scene_id not in previous_ids:
        previous_ids.append(scene_id)
        target.previous_scene_ids_json = json.dumps(previous_ids)

    await db.commit()

    updated_next = json.loads(scene.next_scene_ids_json or "[]")
    updated_previous = json.loads(scene.previous_scene_ids_json or "[]")
    return {
        "success": True,
        "next_scene_ids": updated_next,
        "previous_scene_ids": updated_previous,
    }


@scenes_router.post("/{scene_id}/connections/previous")
async def add_previous_connection(
    scene_id: int,
    target_scene_id: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Add a previous scene connection."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if target_scene_id == scene_id:
        raise HTTPException(status_code=400, detail="Cannot connect scene to itself")

    previous_ids = json.loads(scene.previous_scene_ids_json or "[]")
    if target_scene_id in previous_ids:
        raise HTTPException(status_code=400, detail="Connection already exists")

    target_stmt = select(SceneRecord).filter(SceneRecord.id == target_scene_id)
    target_result = await db.execute(target_stmt)
    target = target_result.scalars().first()

    if not target:
        raise HTTPException(status_code=400, detail="Target scene not found")

    if target.campaign_id != scene.campaign_id:
        raise HTTPException(
            status_code=400, detail="Target scene must be in same campaign"
        )

    previous_ids.append(target_scene_id)
    scene.previous_scene_ids_json = json.dumps(previous_ids)

    target_next_ids = json.loads(target.next_scene_ids_json or "[]")
    if scene_id not in target_next_ids:
        target_next_ids.append(scene_id)
        target.next_scene_ids_json = json.dumps(target_next_ids)

    await db.commit()

    updated_next = json.loads(scene.next_scene_ids_json or "[]")
    updated_previous = previous_ids
    return {
        "success": True,
        "next_scene_ids": updated_next,
        "previous_scene_ids": updated_previous,
    }


@scenes_router.delete("/{scene_id}/connections/next/{target_id}")
async def remove_next_connection(
    scene_id: int,
    target_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Remove a next scene connection (bidirectional)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    next_ids = json.loads(scene.next_scene_ids_json or "[]")
    if target_id not in next_ids:
        updated_next = next_ids
        updated_previous = json.loads(scene.previous_scene_ids_json or "[]")
        return {
            "success": True,
            "next_scene_ids": updated_next,
            "previous_scene_ids": updated_previous,
        }

    new_next = [i for i in next_ids if i != target_id]
    scene.next_scene_ids_json = json.dumps(new_next)

    target_stmt = select(SceneRecord).filter(SceneRecord.id == target_id)
    target_result = await db.execute(target_stmt)
    target = target_result.scalars().first()

    if target:
        previous_ids = json.loads(target.previous_scene_ids_json or "[]")
        new_previous = [i for i in previous_ids if i != scene_id]
        target.previous_scene_ids_json = json.dumps(new_previous)

    await db.commit()

    updated_next = new_next
    updated_previous = json.loads(scene.previous_scene_ids_json or "[]")
    return {
        "success": True,
        "next_scene_ids": updated_next,
        "previous_scene_ids": updated_previous,
    }


@scenes_router.delete("/{scene_id}/connections/previous/{target_id}")
async def remove_previous_connection(
    scene_id: int,
    target_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Remove a previous scene connection."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    previous_ids = json.loads(scene.previous_scene_ids_json or "[]")
    if target_id not in previous_ids:
        updated_next = json.loads(scene.next_scene_ids_json or "[]")
        updated_previous = previous_ids
        return {
            "success": True,
            "next_scene_ids": updated_next,
            "previous_scene_ids": updated_previous,
        }

    new_previous = [i for i in previous_ids if i != target_id]
    scene.previous_scene_ids_json = json.dumps(new_previous)

    target_stmt = select(SceneRecord).filter(SceneRecord.id == target_id)
    target_result = await db.execute(target_stmt)
    target = target_result.scalars().first()

    if target:
        target_next_ids = json.loads(target.next_scene_ids_json or "[]")
        new_target_next = [i for i in target_next_ids if i != scene_id]
        target.next_scene_ids_json = json.dumps(new_target_next)

    await db.commit()

    updated_next = json.loads(scene.next_scene_ids_json or "[]")
    updated_previous = new_previous
    return {
        "success": True,
        "next_scene_ids": updated_next,
        "previous_scene_ids": updated_previous,
    }


# =============================================================================
# Scene Participants API
# =============================================================================


@scenes_router.get("/{scene_id}/participants")
async def get_scene_participants(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get all participants (characters) for a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    participants_stmt = select(SceneParticipantRecord).filter(
        SceneParticipantRecord.scene_id == scene_id
    )
    participants_result = await db.execute(participants_stmt)
    participants = participants_result.scalars().all()

    result = []
    for p in participants:
        char_stmt = select(VTTCharacterRecord).filter(
            VTTCharacterRecord.id == p.character_id
        )
        char_result = await db.execute(char_stmt)
        char = char_result.scalars().first()
        if not char:
            continue

        player_name = None
        if p.player_id:
            player_stmt = select(CampaignPlayerRecord).filter(
                CampaignPlayerRecord.id == p.player_id
            )
            player_result = await db.execute(player_stmt)
            player = player_result.scalars().first()
            if player:
                player_name = player.player_name

        result.append(
            {
                "id": p.id,
                "character_id": char.id,
                "name": char.name,
                "type": "pc" if p.player_id else "npc",
                "is_visible_to_players": p.is_visible_to_players,
                "player_id": p.player_id,
                "player_name": player_name,
            }
        )

    return result


@scenes_router.post("/{scene_id}/participants")
async def add_scene_participant(
    scene_id: int,
    character_id: int = Body(..., embed=True),
    is_visible_to_players: bool = Body(False, embed=True),
    player_id: Optional[int] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Add a participant (character) to a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    char_stmt = select(VTTCharacterRecord).filter(VTTCharacterRecord.id == character_id)
    char_result = await db.execute(char_stmt)
    char = char_result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    if char.campaign_id != scene.campaign_id:
        raise HTTPException(
            status_code=400, detail="Character does not belong to this campaign"
        )

    if player_id is not None:
        player_stmt = select(CampaignPlayerRecord).filter(
            CampaignPlayerRecord.id == player_id,
            CampaignPlayerRecord.campaign_id == scene.campaign_id,
        )
        player_result = await db.execute(player_stmt)
        player = player_result.scalars().first()

        if not player:
            raise HTTPException(status_code=400, detail="Player not found in campaign")

        existing_player_stmt = select(SceneParticipantRecord).filter(
            SceneParticipantRecord.scene_id == scene_id,
            SceneParticipantRecord.player_id == player_id,
        )
        existing_player_result = await db.execute(existing_player_stmt)
        existing_player = existing_player_result.scalars().first()

        if existing_player:
            raise HTTPException(
                status_code=400,
                detail="Player already assigned to a character in this scene",
            )

        if player.vtt_character_id and player.vtt_character_id != character_id:
            raise HTTPException(
                status_code=400, detail="Player is not assigned to this character"
            )

    existing_char_stmt = select(SceneParticipantRecord).filter(
        SceneParticipantRecord.scene_id == scene_id,
        SceneParticipantRecord.character_id == character_id,
    )
    existing_char_result = await db.execute(existing_char_stmt)
    existing_char = existing_char_result.scalars().first()

    if existing_char:
        raise HTTPException(status_code=400, detail="Character already in scene")

    participant = SceneParticipantRecord(
        scene_id=scene_id,
        character_id=character_id,
        player_id=player_id,
        is_visible_to_players=is_visible_to_players,
    )
    db.add(participant)
    await db.commit()
    await db.refresh(participant)

    return {"success": True, "participant_id": participant.id}


@scenes_router.put("/{scene_id}/participants/{participant_id}")
async def update_scene_participant(
    scene_id: int,
    participant_id: int,
    is_visible_to_players: Optional[bool] = Body(None, embed=True),
    player_id: Optional[int] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Update a scene participant."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    participant_stmt = select(SceneParticipantRecord).filter(
        SceneParticipantRecord.id == participant_id,
        SceneParticipantRecord.scene_id == scene_id,
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalars().first()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if is_visible_to_players is not None:
        participant.is_visible_to_players = is_visible_to_players

    if player_id is not None:
        if player_id is not None:
            player_stmt = select(CampaignPlayerRecord).filter(
                CampaignPlayerRecord.id == player_id,
                CampaignPlayerRecord.campaign_id == scene.campaign_id,
            )
            player_result = await db.execute(player_stmt)
            player = player_result.scalars().first()

            if not player:
                raise HTTPException(
                    status_code=400, detail="Player not found in campaign"
                )

            existing_stmt = (
                select(SceneParticipantRecord)
                .filter(
                    SceneParticipantRecord.scene_id == scene_id,
                    SceneParticipantRecord.player_id == player_id,
                )
                .filter(SceneParticipantRecord.id != participant_id)
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalars().first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Player already assigned to another character in this scene",
                )

            if (
                player.vtt_character_id
                and player.vtt_character_id != participant.character_id
            ):
                raise HTTPException(
                    status_code=400, detail="Player is not assigned to this character"
                )

        participant.player_id = player_id

    await db.commit()

    return {"success": True}


@scenes_router.delete("/{scene_id}/participants/{participant_id}")
async def remove_scene_participant(
    scene_id: int,
    participant_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Remove a participant from a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    participant_stmt = select(SceneParticipantRecord).filter(
        SceneParticipantRecord.id == participant_id,
        SceneParticipantRecord.scene_id == scene_id,
    )
    participant_result = await db.execute(participant_stmt)
    participant = participant_result.scalars().first()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    await db.delete(participant)
    await db.commit()

    return {"success": True}


# =============================================================================
# Scene Ships API
# =============================================================================


@scenes_router.get("/{scene_id}/ships")
async def get_scene_ships(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get all ships for a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    scene_ships_stmt = select(SceneShipRecord).filter(
        SceneShipRecord.scene_id == scene_id
    )
    scene_ships_result = await db.execute(scene_ships_stmt)
    scene_ships = scene_ships_result.scalars().all()

    result = []
    for ss in scene_ships:
        ship_stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ss.ship_id)
        ship_result = await db.execute(ship_stmt)
        ship = ship_result.scalars().first()
        if ship:
            result.append(
                {
                    "ship_id": ship.id,
                    "name": ship.name,
                    "is_visible_to_players": ss.is_visible_to_players,
                }
            )

    return result


@scenes_router.post("/{scene_id}/ships")
async def add_scene_ship(
    scene_id: int,
    ship_id: int = Body(..., embed=True),
    is_visible_to_players: bool = Body(False, embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Add a ship to a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    ship_stmt = select(VTTShipRecord).filter(VTTShipRecord.id == ship_id)
    ship_result = await db.execute(ship_stmt)
    ship = ship_result.scalars().first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    campaign_ship_stmt = select(CampaignShipRecord).filter(
        CampaignShipRecord.campaign_id == scene.campaign_id,
        CampaignShipRecord.ship_id == ship_id,
    )
    campaign_ship_result = await db.execute(campaign_ship_stmt)
    campaign_ship = campaign_ship_result.scalars().first()

    if not campaign_ship:
        raise HTTPException(status_code=400, detail="Ship not in campaign")

    existing_stmt = select(SceneShipRecord).filter(
        SceneShipRecord.scene_id == scene_id,
        SceneShipRecord.ship_id == ship_id,
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalars().first()

    if existing:
        raise HTTPException(status_code=400, detail="Ship already in scene")

    scene_ship = SceneShipRecord(
        scene_id=scene_id,
        ship_id=ship_id,
        is_visible_to_players=is_visible_to_players,
    )
    db.add(scene_ship)
    await db.commit()

    return {"success": True}


@scenes_router.put("/{scene_id}/ships/{ship_id}")
async def update_scene_ship(
    scene_id: int,
    ship_id: int,
    is_visible_to_players: Optional[bool] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Update a ship in a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    scene_ship_stmt = select(SceneShipRecord).filter(
        SceneShipRecord.scene_id == scene_id,
        SceneShipRecord.ship_id == ship_id,
    )
    scene_ship_result = await db.execute(scene_ship_stmt)
    scene_ship = scene_ship_result.scalars().first()

    if not scene_ship:
        raise HTTPException(status_code=404, detail="Ship not found in scene")

    if is_visible_to_players is not None:
        scene_ship.is_visible_to_players = is_visible_to_players

    await db.commit()

    return {"success": True}


@scenes_router.delete("/{scene_id}/ships/{ship_id}")
async def remove_scene_ship(
    scene_id: int,
    ship_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Remove a ship from a scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    scene_ship_stmt = select(SceneShipRecord).filter(
        SceneShipRecord.scene_id == scene_id,
        SceneShipRecord.ship_id == ship_id,
    )
    scene_ship_result = await db.execute(scene_ship_stmt)
    scene_ship = scene_ship_result.scalars().first()

    if not scene_ship:
        raise HTTPException(status_code=404, detail="Ship not found in scene")

    await db.delete(scene_ship)
    await db.commit()

    return {"success": True}


# =============================================================================
# Scene Activation & Config
# =============================================================================


@scenes_router.get("/{scene_id}/closing-options")
async def get_closing_options(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get closing options for a scene (candidate next scenes, etc.)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    next_ids = json.loads(scene.next_scene_ids_json or "[]")
    draft_next_stmt = select(SceneRecord).filter(
        SceneRecord.id.in_(next_ids),
        SceneRecord.status == "draft",
    )
    draft_next_result = await db.execute(draft_next_stmt)
    draft_next = draft_next_result.scalars().all()

    return {
        "next_scene_candidates": [
            {"id": s.id, "name": s.name, "status": s.status} for s in draft_next
        ],
        "allow_create_new": True,
        "allow_return_overview": True,
    }


@scenes_router.post("/{scene_id}/transition-to-ready")
async def transition_scene_to_ready(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Transition scene from draft to ready status."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if scene.status not in ("draft",):
        raise HTTPException(
            status_code=400,
            detail=f"Scene must be in 'draft' status to transition to ready, currently '{scene.status}'",
        )

    errors = []
    if not scene.name or scene.name == "New Scene":
        errors.append("Scene must have a name (title)")
    if not scene.gm_short_description:
        errors.append("Scene must have a GM short description")

    player_chars = json.loads(scene.player_character_list or "[]")
    if not player_chars:
        errors.append("Scene must have at least one player character")

    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    scene.status = "ready"
    await db.commit()

    return {"success": True, "scene_id": scene.id, "status": scene.status}


@scenes_router.post("/{scene_id}/activate")
async def activate_scene(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Activate a scene, creating appropriate encounter records."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if scene.status not in ("ready", "draft"):
        raise HTTPException(
            status_code=400,
            detail=f"Scene must be in 'ready' or 'draft' status to activate, currently '{scene.status}'",
        )

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.id == scene.campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.momentum = max(0, campaign.momentum - 1)

    response_data = {"success": True, "scene_id": scene.id, "status": scene.status}

    if scene.scene_type == "starship_encounter":
        if not campaign.active_ship_id:
            raise HTTPException(
                status_code=400, detail="Campaign has no active ship assigned"
            )

        scene_ships_stmt = select(SceneShipRecord).filter(
            SceneShipRecord.scene_id == scene.id
        )
        scene_ships_result = await db.execute(scene_ships_stmt)
        scene_ships = scene_ships_result.scalars().all()

        if not scene_ships:
            raise HTTPException(
                status_code=400,
                detail="Starship encounter must have at least one ship in scene",
            )

        ship_ids = [ss.ship_id for ss in scene_ships]
        if campaign.active_ship_id not in ship_ids:
            raise HTTPException(
                status_code=400, detail="Player ship must be included in scene ships"
            )

        npc_ship_ids = [sid for sid in ship_ids if sid != campaign.active_ship_id]

        encounter = EncounterRecord(
            encounter_id=str(uuid.uuid4()),
            name=scene.name,
            campaign_id=campaign.id,
            player_ship_id=campaign.active_ship_id,
            player_position=scene.scene_position or "captain",
            enemy_ship_ids_json=json.dumps(npc_ship_ids),
            tactical_map_json=scene.tactical_map_json or "{}",
            is_active=True,
        )
        db.add(encounter)
        await db.flush()
        scene.encounter_id = encounter.id
        response_data["encounter_id"] = encounter.id

    elif scene.scene_type == "personal_encounter":
        participants_stmt = select(SceneParticipantRecord).filter(
            SceneParticipantRecord.scene_id == scene.id
        )
        participants_result = await db.execute(participants_stmt)
        participants = participants_result.scalars().all()

        if not participants:
            raise HTTPException(
                status_code=400,
                detail="Personal encounter must have at least one participant",
            )

        character_states = []
        for p in participants:
            char_stmt = select(VTTCharacterRecord).filter(
                VTTCharacterRecord.id == p.character_id
            )
            char_result = await db.execute(char_stmt)
            char = char_result.scalars().first()
            if not char:
                continue

            is_player = p.player_id is not None
            char_state = {
                "character_id": char.id,
                "name": char.name,
                "is_player": is_player,
                "stress": char.stress,
                "determination": char.determination,
                "stress_max": char.stress_max,
                "determination_max": char.determination_max,
                "is_defeated": char.stress >= char.stress_max,
                "injuries": [],
                "protection": 0,
            }
            character_states.append(char_state)

        encounter = PersonnelEncounterRecord(
            scene_id=scene.id,
            momentum=campaign.momentum,
            threat=campaign.threat,
            character_states_json=json.dumps(character_states),
            tactical_map_json=scene.tactical_map_json or "{}",
            is_active=True,
        )
        db.add(encounter)
        await db.flush()
        response_data["personnel_encounter_id"] = encounter.id

    scene.status = "active"
    await db.commit()

    response_data["status"] = scene.status
    return response_data


@scenes_router.get("/campaign/{campaign_id}/active-scenes")
async def get_active_scenes(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get all active scenes for a campaign (supports split-party)."""
    await _require_gm_auth(campaign_id, sta_session_token, db)

    stmt = select(SceneRecord).filter(
        SceneRecord.campaign_id == campaign_id, SceneRecord.status == "active"
    )
    result = await db.execute(stmt)
    scenes = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "scene_type": s.scene_type,
            "status": s.status,
            "is_focused": s.is_focused,
            "gm_short_description": s.gm_short_description,
        }
        for s in scenes
    ]


@scenes_router.put("/{scene_id}/focus")
async def set_scene_focus(
    scene_id: int,
    is_focused: bool = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Set GM focus on a scene (for split-party management)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    scene.is_focused = is_focused
    await db.commit()

    return {"success": True, "scene_id": scene.id, "is_focused": scene.is_focused}


@scenes_router.post("/{scene_id}/end")
async def end_scene(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """End an active scene, reducing momentum and deactivating encounter."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if scene.status != "active":
        raise HTTPException(status_code=400, detail="Scene must be active to end")

    campaign_stmt = select(CampaignRecord).filter(
        CampaignRecord.id == scene.campaign_id
    )
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.momentum = max(0, min(campaign.momentum, 6) - 1)
    scene.status = "completed"

    if scene.encounter_id:
        encounter_stmt = select(EncounterRecord).filter(
            EncounterRecord.id == scene.encounter_id
        )
        encounter_result = await db.execute(encounter_stmt)
        encounter = encounter_result.scalars().first()
        if encounter:
            encounter.is_active = False
    else:
        personnel_enc_stmt = select(PersonnelEncounterRecord).filter(
            PersonnelEncounterRecord.scene_id == scene.id
        )
        personnel_enc_result = await db.execute(personnel_enc_stmt)
        personnel_encounter = personnel_enc_result.scalars().first()
        if personnel_encounter:
            personnel_encounter.is_active = False

    await db.commit()

    next_ids = json.loads(scene.next_scene_ids_json or "[]")
    draft_next_stmt = select(SceneRecord).filter(
        SceneRecord.id.in_(next_ids),
        SceneRecord.status == "draft",
    )
    draft_next_result = await db.execute(draft_next_stmt)
    draft_next = draft_next_result.scalars().all()

    closing_opts = {
        "next_scene_candidates": [
            {"id": s.id, "name": s.name, "status": s.status} for s in draft_next
        ],
        "allow_create_new": True,
        "allow_return_overview": True,
    }

    return {
        "success": True,
        "momentum_remaining": campaign.momentum,
        "closing_options": closing_opts,
    }


@scenes_router.post("/{scene_id}/reactivate")
async def reactivate_scene(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Reactivate a completed scene (completed → ready → active)."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if scene.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Only completed scenes can be reactivated, currently '{scene.status}'",
        )

    scene.status = "ready"
    await db.commit()

    scene.status = "active"
    await db.commit()

    return {"success": True, "scene_id": scene.id, "status": scene.status}


@scenes_router.post("/{scene_id}/copy")
async def copy_scene_as_new(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Create a copy of a completed scene as a new ready scene."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if scene.status != "completed":
        raise HTTPException(
            status_code=400, detail="Only completed scenes can be copied"
        )

    new_scene = SceneRecord(
        campaign_id=scene.campaign_id,
        name=scene.name + " (Copy)",
        description=scene.description,
        scene_type=scene.scene_type,
        status="ready",
        gm_short_description=scene.gm_short_description,
        player_character_list=scene.player_character_list,
        scene_traits_json=scene.scene_traits_json,
        challenges_json=scene.challenges_json,
        tactical_map_json=scene.tactical_map_json,
    )
    db.add(new_scene)
    await db.commit()
    await db.refresh(new_scene)

    return {
        "success": True,
        "scene_id": new_scene.id,
        "name": new_scene.name,
        "status": new_scene.status,
    }


@scenes_router.get("/{scene_id}/config")
async def get_scene_config(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get scene encounter configuration."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    if scene.encounter_config_json:
        try:
            config = json.loads(scene.encounter_config_json)
            return config
        except json.JSONDecodeError:
            return {}
    return {}


@scenes_router.put("/{scene_id}/config")
async def update_scene_config(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
    body: dict = Body(...),
):
    """Update scene encounter configuration."""
    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await _require_gm_auth(scene.campaign_id, sta_session_token, db)

    allowed_keys = {"npc_turn_mode", "gm_spends_threat_to_start"}
    unknown_keys = set(body.keys()) - allowed_keys
    if unknown_keys:
        raise HTTPException(
            status_code=400,
            detail="Invalid config keys: " + ", ".join(sorted(unknown_keys)),
        )

    data = {}
    npc_turn_mode = body.get("npc_turn_mode")
    gm_spends_threat_to_start = body.get("gm_spends_threat_to_start")

    if npc_turn_mode is not None:
        if npc_turn_mode not in ("all_npcs", "num_pcs"):
            raise HTTPException(
                status_code=400,
                detail="Invalid npc_turn_mode; must be 'all_npcs' or 'num_pcs'",
            )
        data["npc_turn_mode"] = npc_turn_mode

    if gm_spends_threat_to_start is not None:
        if not isinstance(gm_spends_threat_to_start, bool):
            raise HTTPException(
                status_code=400, detail="gm_spends_threat_to_start must be a boolean"
            )
        data["gm_spends_threat_to_start"] = gm_spends_threat_to_start

    scene.encounter_config_json = json.dumps(data)
    await db.commit()

    return {"success": True}


@scenes_router.get("/{scene_id}")
async def view_scene(
    scene_id: int,
    role: str = Query("player"),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """View a scene (narrative scene page)."""
    from sta.database.schema import SceneRecord

    scene_stmt = select(SceneRecord).filter(SceneRecord.id == scene_id)
    scene_result = await db.execute(scene_stmt)
    scene = scene_result.scalars().first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if role == "gm":
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
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url="/", status_code=302)

    html = f"<html><body><h1>{scene.name}</h1>"
    html += f"<p>Type: {scene.scene_type}</p>"
    html += f"<p>Status: {scene.status}</p>"

    if scene.description:
        html += f"<p>{scene.description}</p>"

    scene_traits = json.loads(scene.scene_traits_json or "[]")
    if scene_traits:
        html += "<h2>Scene Traits</h2><ul>"
        for trait in scene_traits:
            if isinstance(trait, dict):
                html += f"<li>{trait.get('name', 'Unknown')}</li>"
            else:
                html += f"<li>{trait}</li>"
        html += "</ul>"

    challenges = json.loads(scene.challenges_json or "[]")
    if challenges:
        html += "<h2>Extended Tasks</h2><ul>"
        for challenge in challenges:
            html += f"<li>{challenge.get('name', 'Unknown')}</li>"
        html += "</ul>"

    html += "</body></html>"

    return {"content": html, "content_type": "text/html"}


@scenes_router.get("/{scene_id}/edit")
async def edit_scene_page(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Render the edit scene page."""
    from sta.database.schema import SceneRecord

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

    html = f"<html><body>"
    html += f"<h1>Edit Scene</h1>"
    html += f"<h2>{scene.name}</h2>"
    html += "<h3>Scene Details</h3>"
    html += f"<p>Type: {scene.scene_type}</p>"
    html += f"<p>Status: {scene.status}</p>"

    if scene.description:
        html += f"<p>{scene.description}</p>"

    html += "<h3>NPCs and NP Ships</h3>"
    html += "<h3>Scene Traits</h3>"
    html += "<h3>Extended Tasks</h3>"
    html += "</body></html>"

    return {"content": html, "content_type": "text/html"}
