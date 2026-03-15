# Milestone 5: Combat Integration - Task List

## Overview
Integrate the existing combat system with the new VTT architecture. This milestone bridges the gap between the character/ship CRUD and the tactical combat mechanics.

## Branch Information
- **Branch**: `feature/m5-combat-integration`
- **Base**: `develop` (after M4 merge)
- **Model**: `opencode/minimax-m2.5-free`

---

## Technical Foundations (Decisions)
1. **Full Persistence**: All combat state (round, turn order, active effects, map data) is stored in `EncounterRecord`.
2. **Native Record Handlers**: Action logic operates directly on `VTTCharacterRecord` and `VTTShipRecord` to ensure transaction safety and real-time updates.
3. **Map Authority**: `EncounterRecord` is the source of truth for participant coordinates on the tactical map.
4. **Campaign Pools**: Combat actions directly modify the shared `CampaignRecord` momentum/threat pools.
5. **Real-time Sync**: Implementation of Server-Sent Events (SSE) for live updates to all clients.
6. **NPC Handling**: NPCs are instantiated as full VTT records (`character_type="npc"`) for a unified API.

---

## Task 5.1: Database Schema & Persistence Enhancement

**Agent**: python-dev
**Skills**: modern-python, databases

### Objectives
- Update `EncounterRecord` and `PersonnelEncounterRecord` to support VTT entities.
- Ensure all combat state is serializable and persisted.

### Implementation Steps
1. Modify `sta/database/schema.py`:
   - Add `vtt_player_ship_id` and `vtt_player_character_id` to `EncounterRecord` (FKs to `vtt_ships` and `vtt_characters`).
   - Enhance `ship_positions_json` and `character_positions_json` to be the definitive mapping for the current combat.
   - Add `turn_order_json` to track the sequence of actors.
2. Update `sta/database/vtt_schema.py` (if needed):
   - Ensure `VTTCharacterRecord` and `VTTShipRecord` can be flagged as temporary "Encounter-only" instances if created for generic NPCs.
3. Create migration script for these changes.

### Verification
- `pytest tests/test_combat_persistence.py`
- Verify state survives application restart.

---

## Task 5.2: Unified VTT Combat Manager

**Agent**: python-dev
**Skills**: modern-python, python-verification

### Objectives
- Create a central logic hub for combat operations using VTT records.
- Implement turn management and pool integration.

### Implementation Steps
1. Create `sta/mechanics/vtt_combat.py` (NEW):
   - `VTTCombatManager` class.
   - Methods for `start_combat`, `end_turn`, `next_round`.
   - Logic to pull/push Momentum and Threat directly from `CampaignRecord`.
   - Helper to instantiate NPCs as VTT records from library templates.
2. Update `sta/web/routes/scenes.py`:
   - Connect "Start Combat" action to the `VTTCombatManager`.

### Verification
- Unit tests for turn sequence logic.
- Verify campaign pools are updated after actions.

---

## Task 5.3: Native VTT Action System Refactoring

**Agent**: python-dev
**Skills**: python-code-quality, python-verification

### Objectives
- Refactor the declarative action system to operate directly on database records.

### Implementation Steps
1. Refactor `sta/mechanics/action_handlers.py`:
   - Update handlers to accept VTT record IDs.
   - Use SQLAlchemy sessions to modify `stress`, `shields`, `breaches`, etc. directly on the records.
   - Eliminate the need for `to_model()` conversion during mechanical resolution.
2. Update `sta/mechanics/action_config.py`:
   - Verify all existing action configurations map correctly to VTT record fields.

### Verification
- Test `Fire` action against a `VTTShipRecord` and verify `shields` update in DB.
- Test `Rally` action and verify `campaign.momentum` update.

---

## Task 5.4: Combat API & Real-time Sync (SSE)

**Agent**: python-dev
**Skills**: modern-python, async-python-patterns

### Objectives
- Provide endpoints for the UI and implement SSE for broadcast.

### Implementation Steps
1. Create `sta/web/routes/combat_api.py`:
   - `GET /api/combat/<id>/state`
   - `POST /api/combat/<id>/action`
   - `GET /api/combat/<id>/stream` (The SSE endpoint).
2. Implement an SSE broadcast helper in `sta/web/sse.py`:
   - Use a simple Pub/Sub pattern to notify clients when `EncounterRecord` is updated.
3. Integrate SSE trigger in `VTTCombatManager`.

### Verification
- `pytest tests/test_combat_api.py`
- Verify multiple browser tabs update simultaneously when an action is taken.

---

## Task 5.5: Combat UI Integration

**Agent**: python-dev
**Skills**: python-code-quality, responsive-design

### Objectives
- Update the front-end to use the new API and SSE stream.

### Implementation Steps
1. Update `sta/web/templates/combat.html`:
   - Switch from polling to `EventSource` (SSE).
   - Update data bindings to reflect the full VTT record state.
2. Update `sta/static/js/combat.js`:
   - Handle incoming SSE events.
   - Refresh tactical map based on `EncounterRecord` positions.

### Verification
- Manual browser test with two characters in the same encounter.

---

## Acceptance Criteria
- [ ] Combat state persists across server restarts.
- [ ] Actions modify VTT database records and Campaign pools directly.
- [ ] All participants (including NPCs) use the VTT record system.
- [ ] UI updates in real-time for all connected players via SSE.
- [ ] 90%+ test coverage for new combat logic.

---

## Task 5.0: Flask to FastAPI Migration

**Agent**: python-dev
**Status**: IN_PROGRESS
**Skills**: fastapi-templates, async-python-patterns

### Objectives
- Replace Flask with FastAPI for better async support (required for SSE).
- Maintain 100% feature parity with existing routes.

### Implementation Steps
1. Create a separate git worktree from `develop`.
2. Initialize `.venv` and install dependencies via `uv`.
3. Convert `sta/web/app.py` to a FastAPI app factory.
4. Convert all Blueprints in `sta/web/routes/*.py` to FastAPI APIRouters.
5. Ensure all database sessions and route handlers are async-compatible.
6. Verify using `uv run pytest`.

### Progress (as of 2026-03-15)

| Metric | Before | After |
|--------|--------|-------|
| Failed Tests | 187 | 122 |
| Passed Tests | 227 | 292 |
| Total Tests | 414 | 414 |
| Improvement | - | 35% |

#### Completed:
- [x] FastAPI app factory in `sta/web/app.py`
- [x] All routers converted to FastAPI:
  - `campaigns_router.py`
  - `universe_router.py`
  - `api_router.py`
  - `scenes_router.py`
  - `characters_router.py`
  - `ships_router.py`
  - `encounters_router.py`
- [x] Test infrastructure updated (`tests/conftest.py`)
- [x] Action endpoints: claim-turn, release-turn, next-turn, fire, ram
- [x] Import/Export endpoints
- [x] Scene endpoints: participants, ships, activation
- [x] Minor action enforcement (prevents 2nd minor action)
- [x] Model attribute fixes (sensors)

#### Remaining (Priority Order):

---

## Task 5.6: Fix FastAPI Routing Issues

**Priority**: P0 - Blocking
**Status**: ✅ COMPLETE

### Problem
~30 tests fail with 404 errors, indicating routes aren't properly registered.

### Fix Applied
Added missing routes to FastAPI routers:
- `api_router.py`: GET/PUT /api/scene/{scene_id}
- `campaigns_router.py`: NPC management, token refresh, player dashboard
- `scenes_router.py`: View scene page, edit scene page

### Results
| Metric | Before | After |
|--------|--------|-------|
| Failed Tests | 122 | 110 |
| Passed Tests | 292 | 304 |
| 404 Errors | ~25 | 0 |

---

## Task 5.7: Fix Flask Remainders in Tests

**Priority**: P0 - Blocking
**Status**: ✅ COMPLETE

### Problem
Flask 3.x removed/changed TestClient APIs:
- `response.get_data()` removed
- `client.delete_cookie()` not available

### Fix Applied
- Replaced `response.get_data(as_text=True)` with `response.content.decode('utf-8')` (13 occurrences)
- Replaced `client.delete_cookie()` with `client.cookies.clear()` (5 occurrences)
- Fixed in: test_scene.py, test_session_tokens.py, test_scene_participants.py, test_scene_ships.py, test_character_claiming.py

### Results
| Metric | Before | After |
|--------|--------|-------|
| Failed Tests | 110 | 102 |
| Passed Tests | 304 | 312 |

---

## Task 5.8: Fix Async/SQLAlchemy Issues

**Priority**: P1 - Important
**Status**: ✅ COMPLETE

### Problem
- `sqlalchemy.exc.MissingGreenlet` - sync in async context
- `sqlalchemy.exc.NoInspectionAvailable` - AsyncEngine inspection

### Fix Applied
- Added `get_table_inspector()` helper using `await conn.run_sync()` for schema inspection
- Fixed session expire patterns - store IDs before expiring objects
- Updated all 8 schema tests to use async inspection pattern

### Results
| Metric | Before | After |
|--------|--------|-------|
| Failed Tests | 102 | ~81 |
| Passed Tests | 312 | ~333 |
| Async Errors | 21 | 0 |

---

## Task 5.9: Fix Scene Activation Logic

**Priority**: P2 - Fix
**Status**: ✅ COMPLETE

### Problem
Tests expect 'active' but code returns 'draft' status.

### Fix Applied
- Scene activation: Fixed response to return updated status
- Ship update: Changed Form to Body parameters for JSON support
- Turn enforcement: Moved "mark player as acted" before enemy turn switch

### Results
| Metric | Before | After |
|--------|--------|-------|
| Failed Tests | 93 | 86 |
| Passed Tests | 321 | 328 |
| Scene Activation | 0/11 | 11/11 passing |

---

## Task 5.10: Implement 4-State Scene Lifecycle

**Priority**: P0 - New Feature
**Status**: TODO

### Objectives
Implement the new 4-state scene lifecycle: draft → ready → active → completed

### State Definitions

| State | Required Fields | Notes |
|-------|-----------------|-------|
| **draft** | (none) | No title, no player list. Never visible to players. |
| **ready** | title, gm_short_description | Title + GM description visible in transition dialogue |
| **active** | (in progress) | Multiple can be active for split-party |
| **completed** | (archived) | Can be re-activated or copied |

### Implementation Steps
1. Update Scene model status enum:
   - Add `ready` and `completed` states
   - Validate required fields per state
2. Update scene validation:
   - Draft: no title required, no participants required
   - Ready: requires `title` and `gm_short_description`
   - Active: requires at least one participant (?)
   - Completed: auto-terminate connections
3. Add state transition validation:
   - Draft → Ready: requires title + gm_short_description
   - Ready → Active: requires at least title (?)
   - Active → Completed: trigger connection termination
   - Completed → Ready: re-activation
   - Completed → Ready: copy-as-new

### Files to Modify
- `sta/models/vtt/models.py` - SceneStatus enum
- `sta/database/vtt_schema.py` - SceneRecord
- `sta/web/routes/scenes.py` - state transition endpoints

---

## Task 5.11: Scene Transition Dialogue

**Priority**: P0 - New Feature
**Status**: TODO

### Objectives
Implement scene transition UI logic for ending/starting scenes

### Implementation Steps
1. Create endpoint to get transition options:
   - `GET /api/campaigns/{id}/scenes/transition-options`
   - Returns: connected_scenes[], ready_scenes[], can_create_new
2. Update "end scene" endpoint to accept next_scene_id:
   - End current scene
   - Optionally activate next scene
   - Terminate connections
3. Support "create new scene" option:
   - Create draft scene directly from transition

### Files to Modify
- `sta/web/routes/scenes.py` - transition endpoints

---

## Task 5.12: Multi-Active Scene Support

**Priority**: P1 - New Feature
**Status**: TODO

### Objectives
Support multiple active scenes for split-party situations

### Implementation Steps
1. Update scene activation logic:
   - Don't deactivate other scenes when activating
   - Allow multiple `active` scenes per campaign
2. Add scene focus management:
   - `PUT /api/scenes/{id}/focus` - set GM focus
   - `GET /api/campaigns/{id}/active-scenes` - list all active
3. Update participant visibility:
   - All campaign participants visible regardless of active scene
   - Filter by active_scene_id for scene-specific items

### Files to Modify
- `sta/web/routes/scenes.py` - activation endpoints
- `sta/database/vtt_schema.py` - SceneRecord

---

## Task 5.13: Scene Connections

**Priority**: P1 - New Feature
**Status**: TODO

### Objectives
Implement scene connections and connection termination on completion

### Implementation Steps
1. Add scene connections model:
   - `SceneConnectionRecord`: source_scene_id, target_scene_id, connection_type
2. Update scene transition dialogue:
   - Show connected scenes first
   - Allow GM to link scenes
3. On scene completion:
   - Terminate all connections from completed scene
   - Clear bidirectional links

### Files to Modify
- `sta/database/vtt_schema.py` - new table
- `sta/web/routes/scenes.py` - connection endpoints

---

## Task 5.14: Scene Re-activation & Copy

**Priority**: P2 - New Feature
**Status**: TODO

### Objectives
Allow GM to re-activate or copy completed scenes

### Implementation Steps
1. Add re-activation endpoint:
   - `POST /api/scenes/{id}/reactivate`
   - Transitions: completed → ready → active
2. Add copy-as-new endpoint:
   - `POST /api/scenes/{id}/copy`
   - Creates new scene in `ready` status with copied content
   - Clears timestamps, resets status

### Files to Modify
- `sta/web/routes/scenes.py`

---

### Verification
- All scene lifecycle tests pass
- Multi-active scene scenarios work
- Scene transition dialogue shows correct options

---

## Timeline Estimate
- Task 5.1: 4 hrs
- Task 5.2: 6 hrs
- Task 5.3: 8 hrs
- Task 5.4: 6 hrs
- Task 5.5: 8 hrs
- Total: ~32 hours

---

## Current Agent Status (2026-03-15)

### Completed Agents
| Task | Agent | Status | Result |
|------|-------|--------|--------|
| 5.6 | python-dev | ✅ Complete | FastAPI routing fixes (122→110→102→93→86→47→39→37→38→34) |
| 5.7 | python-dev | ✅ Complete | Flask TestClient compatibility (110→102) |
| 5.8 | python-dev | ✅ Complete | Async/SQLAlchemy fixes (102→81→34) |
| 5.9 | python-dev | ✅ Complete | Scene activation logic fixes (93→86) |
| 5.10 | python-dev | ✅ Complete | 4-State Scene Lifecycle implementation + tests |
| Test Restructuring | code-reviewer | ✅ Complete | Added pytest markers, created TEST_MARKERS.md |

### Currently Running Agents
| Task | Agent | Model | Purpose |
|------|-------|-------|---------|
| Final Test Fixes | python-dev | openrouter/step-3.5-flash:free | Fixing remaining ~34 failures |
| M5 Analysis | code-reviewer | openrouter/step-3.5-flash:free | Analyzing test failures, providing fix plan |

### Current Test State
- **Failed**: 34 tests
- **Passed**: 347 tests
- **Total**: 381 tests (after export/import moved to M7)
- **Progress**: ~91% passing

### Model Update (2026-03-15)
Changed default model from `opencode/minimax-m2.5-free` to `openrouter/step-3.5-flash:free` in both agent configs to avoid potential blocking.

---

## Next Steps

1. **Complete final test fixes** (python-dev agent running)
2. **Code review analysis** (code-reviewer agent)
3. **Address remaining issues** based on review recommendations
4. **Finalize M5** with all tests passing (or document acceptable failures)

