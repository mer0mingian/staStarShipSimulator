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
| Failed Tests | 187 | 130 |
| Passed Tests | 227 | 284 |
| Total Tests | 414 | 414 |
| Improvement | - | 30% |

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

#### Remaining:
- [ ] Scene validation/logic fixes (~41 tests)
- [ ] Import/Export field validation (~30 tests)
- [ ] Personnel validation (~10 tests)
- [ ] Session token Flask redirects (~8 tests)
- [ ] Various async SQLAlchemy issues

### Verification
- `uv run pytest tests/` → 130 failed, 284 passed
- Core routing infrastructure complete

---

## Timeline Estimate
- Task 5.1: 4 hrs
- Task 5.2: 6 hrs
- Task 5.3: 8 hrs
- Task 5.4: 6 hrs
- Task 5.5: 8 hrs
- Total: ~32 hours
