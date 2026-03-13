# Milestone 5: Combat Integration - Task List

## Overview
Integrate the existing combat system with the new VTT architecture. This milestone bridges the gap between the character/ship CRUD and the tactical combat mechanics.

## Branch Information
- **Branch**: `feature/m5-combat-integration`
- **Base**: `develop` (after M4 merge)
- **Model**: `opencode/minimax-m2.5-free`

---

## Task 5.1: Combat Scene Logic & State

**Agent**: python-dev
**Skills**: python-debugging, python-verification

### Objectives
- Create a unified combat manager for VTT entities.
- Handle turn order and round transitions for campaigns.
- Integrate momentum/threat pools with VTT characters and ships.

### Implementation Steps
1. Create `sta/mechanics/vtt_combat.py` (NEW FILE):
   - Implement `VTTCombatManager` class.
   - Add methods: `start_combat(scene_id)`, `end_turn(encounter_id)`, `next_round(encounter_id)`.
   - Implement turn tracking logic for multiple players and NPC ships.
2. Modify `sta/database/schema.py`:
   - Add any missing fields to `EncounterRecord` for VTT support (e.g., links to `VTTCharacterRecord` and `VTTShipRecord`).
3. Update `sta/web/routes/scenes.py`:
   - Implement "Start Combat" logic that creates an `EncounterRecord` linked to the `SceneRecord`.

### Verification
- Unit tests for `VTTCombatManager` turn logic.
- Integration tests for scene-to-encounter transition.

---

## Task 5.2: VTT Action System Integration

**Agent**: python-dev
**Skills**: python-code-quality, python-verification

### Objectives
- Adapt the declarative action system to work with `VTTCharacterRecord` and `VTTShipRecord`.
- Ensure all starship and personnel actions correctly update VTT state.

### Implementation Steps
1. Modify `sta/mechanics/action_handlers.py`:
   - Update handlers to accept VTT record IDs and fetch them via ORM.
   - Ensure `apply_results` correctly updates `VTTCharacterRecord.stress`, `VTTShipRecord.shields`, etc.
2. Update `sta/mechanics/actions.py`:
   - Ensure the `Action` model can be instantiated from VTT records.
3. Update `sta/mechanics/action_config.py`:
   - Verify all 10-line action configs are compatible with VTT attributes.

### Verification
- Test action execution against VTT character/ship records.
- Verify stress/shields are correctly subtracted/added.

---

## Task 5.3: Combat API Endpoints

**Agent**: python-dev
**Skills**: python-environment, python-verification

### Objectives
- Provide a robust API for the combat UI to interact with.

### Endpoints to create in `sta/web/routes/combat_api.py` (NEW FILE)
1. `GET /api/combat/<encounter_id>/state`
   - Returns full combat state (participants, positions, momentum, threat, current turn).
2. `POST /api/combat/<encounter_id>/action`
   - Executes an action for a specific participant.
   - Body: `{participant_id, action_id, target_id, bonus_dice}`.
3. `POST /api/combat/<encounter_id>/turn/end`
   - Ends the current actor's turn.
4. `PUT /api/combat/<encounter_id>/map/position`
   - Updates participant position on the hex grid.

### Verification
- `pytest tests/test_combat_api.py`

---

## Task 5.4: Combat UI Integration

**Agent**: python-dev
**Skills**: python-code-quality, python-verification

### Objectives
- Update the front-end to use the new VTT combat APIs.
- Ensure the tactical map reflects VTT positions.

### Implementation Steps
1. Update `sta/web/templates/combat.html` and `combat_gm.html`:
   - Replace legacy data bindings with VTT API calls.
2. Modify `sta/static/js/combat.js` (or equivalent):
   - Implement API polling for state updates.
   - Update map rendering logic for hex grid.

### Verification
- Manual verification of combat flow in browser.
- Browser automation tests if feasible.

---

## Acceptance Criteria
- [ ] Combat can be started from any scene (starship or personnel).
- [ ] Turn management correctly handles multiple players and NPC groups.
- [ ] Actions correctly modify VTT character/ship stress, shields, and breaches.
- [ ] Momentum and Threat pools are shared across the campaign during combat.
- [ ] All tests pass with 90%+ coverage for new logic.

---

## Timeline Estimate
- Task 5.1: 4-6 hrs
- Task 5.2: 6-8 hrs
- Task 5.3: 4-6 hrs
- Task 5.4: 8-10 hrs
- Total: ~22-30 hours
