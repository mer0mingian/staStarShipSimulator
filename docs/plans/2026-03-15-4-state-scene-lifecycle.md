# 4-State Scene Lifecycle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the 4-state scene lifecycle (draft → ready → active → completed) with state transition validation and multi-active scene support.

**Architecture:** Add new database fields for scene state management, update the SceneStatus enum, add state transition endpoints, and support multiple active scenes for split-party.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic

---

### Task 1: Update SceneStatus Enum

**Files:**
- Modify: `sta/models/vtt/types.py:46-49`

**Step 1: Add READY to SceneStatus enum**

Edit `sta/models/vtt/types.py`:
```python
class SceneStatus(str, Enum):
    ACTIVE = "Active"
    ARCHIVED = "Archived"
    CONNECTED = "Connected"
    READY = "Ready"  # NEW
```

**Step 2: Verify it works**

Run: `python -c "from sta.models.vtt.types import SceneStatus; print([s.value for s in SceneStatus])"`
Expected: List includes "Ready"

---

### Task 2: Add New Fields to SceneRecord

**Files:**
- Modify: `sta/database/schema.py:500-551`

**Step 1: Add new columns to SceneRecord**

Edit `SceneRecord` class, add after `status` field (line ~519):
```python
# Scene lifecycle fields
gm_short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
player_character_list: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of PC IDs
```

**Step 2: Add impersonated_by_id to SceneParticipantRecord**

Edit `SceneParticipantRecord` class (line ~567):
```python
impersonated_by_id: Mapped[Optional[int]] = mapped_column(
    ForeignKey("campaign_players.id"), nullable=True
)
```

---

### Task 3: Add State Transition Validation Helper

**Files:**
- Create: `sta/models/vtt/scene_validation.py` (new file)
- Modify: `sta/models/vtt/__init__.py`

**Step 1: Create scene validation module**

Create `sta/models/vtt/scene_validation.py`:
```python
"""Scene lifecycle validation logic."""
from typing import List, Optional


class SceneValidationError(Exception):
    """Raised when scene validation fails."""
    pass


def validate_scene_for_ready(scene: dict) -> List[str]:
    """Validate scene has required fields for 'ready' status."""
    errors = []
    if not scene.get("name"):
        errors.append("Scene must have a name (title)")
    if not scene.get("gm_short_description"):
        errors.append("Scene must have a GM short description")
    player_chars = scene.get("player_character_list", [])
    if not player_chars or player_chars == "[]":
        errors.append("Scene must have at least one player character")
    return errors


def validate_scene_for_active(scene: dict) -> List[str]:
    """Validate scene can be activated."""
    errors = []
    # Currently no additional requirements - just needs to be 'ready'
    return errors


def validate_state_transition(current_status: str, new_status: str, scene: dict) -> List[str]:
    """Validate state transition is allowed."""
    errors = []
    
    valid_transitions = {
        "draft": ["ready"],
        "ready": ["active"],
        "active": ["completed"],
        "completed": ["ready"],  # re-activate
    }
    
    if current_status == new_status:
        return []  # No change, always OK
    
    allowed = valid_transitions.get(current_status, [])
    if new_status not in allowed:
        errors.append(f"Cannot transition from '{current_status}' to '{new_status}'")
        return errors
    
    # Validate target state requirements
    if new_status == "ready":
        errors.extend(validate_scene_for_ready(scene))
    elif new_status == "active":
        errors.extend(validate_scene_for_active(scene))
    
    return errors
```

**Step 2: Update __init__.py**

Add to `sta/models/vtt/__init__.py`:
```python
from sta.models.vtt.scene_validation import (
    SceneValidationError,
    validate_state_transition,
    validate_scene_for_ready,
    validate_scene_for_active,
)
```

---

### Task 4: Add Scene Transition Endpoints

**Files:**
- Modify: `sta/web/routes/scenes_router.py`

**Step 1: Add transition-to-ready endpoint**

Add to `scenes_router.py` (around line 1058):
```python
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
            detail=f"Scene must be in 'draft' status to transition to ready, currently '{scene.status}'"
        )

    # Validate required fields
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
```

**Step 2: Update activate endpoint for 'ready' status**

Modify existing `activate_scene` endpoint (line ~1074):
```python
# Change from: if scene.status != "draft":
# To:
if scene.status not in ("ready",):
    raise HTTPException(
        status_code=400,
        detail=f"Scene must be in 'ready' status to activate, currently '{scene.status}'"
    )
```

**Step 3: Update end scene endpoint to accept next_scene_id**

Modify existing `end_scene` endpoint (around line 1190) - add optional next_scene_id parameter:
```python
async def end_scene(
    scene_id: int,
    next_scene_id: Optional[int] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
```

And update transition to completed:
```python
# Currently ends to "completed" - that's correct
scene.status = "completed"
```

---

### Task 5: Add Scene Transition Dialogue Endpoint

**Files:**
- Modify: `sta/web/routes/scenes_router.py`

**Step 1: Add GET /campaigns/{id}/scenes/transition-options endpoint**

Add to `campaigns_router.py` or create in scenes_router:
```python
@scenes_router.get("/campaigns/{campaign_id}/scenes/transition-options")
async def get_scene_transition_options(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    sta_session_token: Optional[str] = Cookie(None),
):
    """Get scene transition options for a campaign."""
    # Get campaign
    campaign_stmt = select(CampaignRecord).filter(CampaignRecord.id == campaign_id)
    campaign_result = await db.execute(campaign_stmt)
    campaign = campaign_result.scalars().first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await _require_gm_auth(campaign_id, sta_session_token, db)

    # Get connected scenes (draft status)
    connected_stmt = select(SceneRecord).filter(
        SceneRecord.campaign_id == campaign_id,
        SceneRecord.status == "draft",
    )
    connected_result = await db.execute(connected_stmt)
    connected_scenes = [
        {"id": s.id, "name": s.name, "status": s.status}
        for s in connected_result.scalars().all()
    ]

    # Get ready scenes
    ready_stmt = select(SceneRecord).filter(
        SceneRecord.campaign_id == campaign_id,
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
```

**Note:** Need to add this to the router registration in api_router.py or campaigns_router.py.

---

### Task 6: Add Re-activation and Copy Endpoints

**Files:**
- Modify: `sta/web/routes/scenes_router.py`

**Step 1: Add reactivate endpoint**

Add after end_scene endpoint:
```python
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
            detail=f"Only completed scenes can be reactivated, currently '{scene.status}'"
        )

    # Transition to ready first
    scene.status = "ready"
    await db.commit()

    # Then activate
    scene.status = "active"
    await db.commit()

    return {"success": True, "scene_id": scene.id, "status": scene.status}
```

**Step 2: Add copy-as-new endpoint**

```python
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
            status_code=400,
            detail="Only completed scenes can be copied"
        )

    # Create new scene with copied content
    new_scene = SceneRecord(
        campaign_id=scene.campaign_id,
        name=scene.name + " (Copy)",
        description=scene.description,
        scene_type=scene.scene_type,
        status="ready",  # Start as ready
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
```

---

### Task 7: Update Scene Creation to Default to 'draft'

**Files:**
- Modify: `sta/web/routes/campaigns_router.py:995-1012`

**Step 1: Ensure new scenes default to draft**

The current code already sets `status="draft"` - verify this is still correct.

---

### Task 8: Run Tests and Verify

**Step 1: Run all scene tests**

```bash
uv run pytest tests/test_scene.py -v --tb=short 2>&1 | tail -40
```

**Step 2: Run scene activation tests**

```bash
uv run pytest tests/test_scene_activation.py -v --tb=short 2>&1 | tail -20
```

**Step 3: Run scene termination tests**

```bash
uv run pytest tests/test_scene_termination.py -v --tb=short 2>&1 | tail -20
```

---

### Task 9: Commit Changes

**Step 1: Check git status**

```bash
git status
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: implement 4-state scene lifecycle (draft/ready/active/completed)"
```
