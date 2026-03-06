# Milestone 3: Scene Management - Implementation Tasks

## Overview
Complete scene lifecycle with narrative, combat (starship/personal/social) support, focusing on scene connections, participant management, and activation/termination flows.

## Branch Information
- **Branch**: `feature/m3-scene-management`
- **Base**: `vtt-scope` (after M2 merge)
- **Model**: `opencode/minimax-m2.5-free`
- **Worktree**: Separate worktrees per agent after Task 3.1

---

## Current State Assessment

### Existing
- `SceneRecord` (draft/active/completed, scene_type: narrative/starship_encounter/personal_encounter/social_encounter)
- Basic scene routes (`/new`, `<scene_id>`, `<scene_id>/edit`, NPC management)
- API endpoints in `campaigns.py` (status update, delete, convert)
- `PersonnelEncounterRecord` (personal combat tracking)
- `EncountersRecord` (starship combat)
- Campaign resource pools (momentum/threat) from M2

### Missing (M3 Scope)
- Scene connection management (previous/next scenes)
- Scene participant & ship assignment with visibility
- Scene activation logic per type (create encounters, initialize state)
- Scene termination (momentum reduction, encounter deactivation, closing options)
- Encounter configuration storage (npc_turn_mode, gm_spends_threat_to_start)
- Personal encounter turn tracking (deferred to M5)

---

## Task 3.1: Database Schema Changes

**Agent**: python-dev (single-threaded first)
**Estimated Time**: 2-3 hours

### Changes to `sta/database/schema.py`

1. **SceneRecord additions**:
   ```python
   next_scene_ids_json: Mapped[str] = mapped_column(Text, default="[]")
   previous_scene_ids_json: Mapped[str] = mapped_column(Text, default="[]")
   encounter_config_json: Mapped[str] = mapped_column(Text, default="{}")
   ```

2. **Create `scene_participants` table**:
   ```python
   class SceneParticipantRecord(Base):
       __tablename__ = "scene_participants"
       id: Mapped[int] = mapped_column(primary_key=True)
       scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), nullable=False)
       character_id: Mapped[int] = mapped_column(ForeignKey("vtt_characters.id"), nullable=False)
       player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaign_players.id"), nullable=True)
       is_visible_to_players: Mapped[bool] = mapped_column(default=False)
   ```
   - `player_id` nullable: PC can be assigned to a player, NPCs leave null.
   - Unique constraint: (`scene_id`, `character_id`)

3. **Create `scene_ships` table**:
   ```python
   class SceneShipRecord(Base):
       __tablename__ = "scene_ships"
       id: Mapped[int] = mapped_column(primary_key=True)
       scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), nullable=False)
       ship_id: Mapped[int] = mapped_column(ForeignKey("vtt_ships.id"), nullable=False)
       is_visible_to_players: Mapped[bool] = mapped_column(default=False)
   ```
   - Unique constraint: (`scene_id`, `ship_id`)

4. **Mark legacy fields as deprecated** (add comments):
   - `SceneRecord.characters_present_json` – "Deprecated: use scene_participants table"
   - `SceneRecord.enemy_ships_json` – "Deprecated: use scene_ships table"

### Migration: `004_scene_m3_changes.py`
- Add new columns to `scenes`
- Create `scene_participants` and `scene_ships`
- Set default empty arrays for connection JSONs

### Tests (`tests/test_scene_m3_schema.py`)
- Verify new columns exist with defaults
- Verify tables created, foreign keys
- Check deprecation comments (optional)

### Verification
```bash
.venv/bin/python -m pytest tests/test_scene_m3_schema.py -v
```

---

## Task 3.2: Scene Connections & Closing Dialog

**Agent**: python-dev
**Estimated Time**: 3-4 hours

### Endpoints in `sta/web/routes/scenes.py`

1. `GET /api/scenes/<int:scene_id>/connections`
   - Returns: `{"next_scenes": [{"id": ..., "name": ..., "status": ...}], "previous_scenes": [...]}`
   - Load next IDs from `next_scene_ids_json`, fetch those scenes (id/name/status).
   - Same for previous.

2. `POST /api/scenes/<int:scene_id>/connect/<int:target_id>`
   - Adds `target_id` to `next_scene_ids_json` of `scene_id`.
   - Reciprocal: adds `scene_id` to `previous_scene_ids_json` of `target_id`.
   - Validate: both scenes in same campaign, target not already connected, target not completed? (Allow connecting to draft/active; disallow to completed.)
   - GM auth required.

3. `POST /api/scenes/<int:scene_id>/disconnect/<int:target_id>`
   - Removes from both sides.
   - GM auth.

4. `GET /api/scenes/<int:scene_id>/closing-options`
   - For closing scene dialog.
   - Returns:
     ```json
     {
       "next_scene_candidates": [
         {"id": ..., "name": ..., "status": "draft"}
       ]  // scenes that are connected via next_scene_ids and are still draft
       ,
       "allow_create_new": true,
       "allow_return_overview": true
     }
     ```
   - GM auth required.

5. `POST /api/scenes/quick`
   - Create a new draft scene connected to a given scene.
   - Body: `{"campaign_id": int, "name": str, "connected_from": int (scene_id)}`
   - Creates scene with status `draft`, sets `next_scene_ids_json` to include `connected_from` as previous? Actually just connect forward: new scene is `next` of `connected_from`. So also update `connected_from`'s `next_scene_ids_json`.
   - Return new scene id.

6. Extend `POST /api/scenes/<id>/end` to return the closing options payload after reducing momentum.

### Tests (`tests/test_scene_connections.py`)
- Connect/disconnect mutual linking
- Closing options list only draft next scenes
- Quick scene creation and linking
- GM auth enforcement

---

## Task 3.3: Participant & Ship Management

**Agent**: python-dev
**Estimated Time**: 4-5 hours

### Endpoints in `sta/web/routes/scenes.py`

**Participants**

1. `GET /api/scenes/<int:scene_id>/participants`
   - Returns list:
     ```json
     [
       {
         "id": participant.id,
         "character_id": char.id,
         "name": char.name,
         "type": "pc"|"npc",
         "is_visible_to_players": bool,
         "player_id": player.id or null,
         "player_name": player.name or null
       }
     ]
     ```
   - Join `scene_participants` with `vtt_characters` and optional `campaign_players`.

2. `POST /api/scenes/<int:scene_id>/participants`
   - Body: `{"character_id": int, "is_visible_to_players": bool, "player_id": int|null}`
   - Validate: character exists in campaign's universe library or campaign_npcs; if `player_id` provided, that player belongs to campaign and has no other character assigned in this scene yet.
   - Create `SceneParticipantRecord`.

3. `PUT /api/scenes/<int:scene_id>/participants/<int:participant_id>`
   - Body: `{"is_visible_to_players": bool, "player_id": int|null}`
   - Allow updating visibility and player assignment.
   - If clearing `player_id`, the player's character is unassigned.

4. `DELETE /api/scenes/<int:scene_id>/participants/<int:participant_id>`
   - Remove participant.

**Ships**

5. `GET /api/scenes/<int:scene_id>/ships`
   - Returns list of ships with visibility: `[{ship_id, name, is_visible_to_players}]`

6. `POST /api/scenes/<int:scene_id>/ships`
   - Body: `{"ship_id": int, "is_visible_to_players": bool}`
   - Validate ship exists in campaign's ship pool.
   - Create `SceneShipRecord`.

7. `PUT /api/scenes/<int:scene_id>/ships/<int:ship_id>`
   - Body: `{"is_visible_to_players": bool}`
   - Update visibility.

8. `DELETE /api/scenes/<int:scene_id>/ships/<int:ship_id>`
   - Remove ship from scene.

**Helper endpoints**

9. `GET /api/campaigns/<int:campaign_id>/characters/available`
   - Returns characters that can be added: union of campaign's PCs (from `campaign_players` linking to `vtt_characters`) and campaign NPCs (from `campaign_npcs` linking to `vtt_characters`). Include id, name, type (pc/npc).

10. `GET /api/campaigns/<int:campaign_id>/ships/available`
    - Returns ships from `campaign_ships` joined with `vtt_ships`.

**Tests** (`tests/test_scene_participants.py`, `tests/test_scene_ships.py`):
- CRUD operations
- Visibility toggles
- Player assignment uniqueness (one char per player per scene)
- Availability helpers filter correctly
- Authorization (GM only)

---

## Task 3.4: Scene Activation, Termination & Config

**Agent**: python-dev
**Estimated Time**: 4-5 hours

### Endpoints in `sta/web/routes/scenes.py`

1. `POST /api/scenes/<int:scene_id>/activate`
   - **Preconditions**:
     - Scene status is `draft`.
     - GM auth.
   - **Validation per `scene_type`**:
     - `starship_encounter`: campaign must have `active_ship_id`; scene must have at least one ship in `scene_ships` (player ship will be that `active_ship_id`). NPC ships are those in `scene_ships` excluding the player ship.
     - `personal_encounter`: scene must have at least one participant with a character assigned (`player_id` not null) or at least one NPC participant.
     - `narrative`: no extra validation.
   - **Actions**:
     - Set scene `status = 'active'`.
     - If starship: create `EncountersRecord` (or reuse existing?) with:
       - `campaign_id` from scene's campaign
       - `player_ship_id` = campaign.active_ship_id
       - `npcs_json` = list of NPC ship IDs from `scene_ships`
       - `is_active = True`
       - Store `encounter_config` from scene's `encounter_config_json`.
       - Link `scene.encounter_id` to this encounter (SceneRecord already has `encounter_id` FK).
     - If personal: create `PersonnelEncounterRecord`:
       - `scene_id`
       - `momentum = campaign.momentum`, `threat = campaign.threat`
       - `character_positions_json = "{}"`
       - `character_states_json`: for each participant PC/NPC, load current stress/stats from `vtt_characters` (stress, determination, state). Build array.
       - `characters_turns_used_json = "{}"`
       - `npc_turn_mode` from scene config (default "all_npcs")
       - `is_active = True`
       - Link `scene.personnel_encounter_id`? PersonnelEncounter has `scene_id` FK unique; use that.
     - Return scene with `encounter_id` if created.

2. `POST /api/scenes/<int:scene_id>/end`
   - **Preconditions**: scene status is `active`.
   - **Actions**:
     - Reduce `campaign.momentum` by 1 (min 0). Commit.
     - Set scene `status = 'completed'`.
     - Deactivate linked encounter:
       - Starship: set `EncountersRecord.is_active = False`
       - Personal: set `PersonnelEncounterRecord.is_active = False`
     - Return payload:
       ```json
       {
         "momentum_remaining": campaign.momentum,
         "closing_options": {
           "next_scene_candidates": [...],  // from GET /closing-options
           "allow_create_new": true,
           "allow_return_overview": true
         }
       }
       ```

3. `GET /api/scenes/<int:scene_id>/config` and `PUT /api/scenes/<int:scene_id>/config`
   - Get/Set `encounter_config_json` (validate JSON structure).
   - Expected config schema:
     ```json
     {
       "npc_turn_mode": "all_npcs" | "num_pcs",
       "gm_spends_threat_to_start": boolean
     }
     ```
   - Starship encounters: only `npc_turn_mode` used.
   - Personal/social: both used (gm_spends_threat_to_start affects who takes first round).

4. **Turn advancement for personal encounters** (defer to M5? Optional)
   - If we include basic version: `POST /api/personnel/<scene_id>/next-turn`
     - Determine which side (player vs npc) is current.
     - If player: find next unacted PC (not yet in `characters_turns_used`), mark acted, record timestamp.
     - If npc: based on `npc_turn_mode`, choose an NPC that hasn't acted this round, mark acted; if `num_pcs`, decrement remaining NPC turn count.
     - When all PCs have acted and all NPC turns consumed, increment `round`, reset acted flags, reset npc turn count.
   - **Recommendation**: Defer to M5 to keep M3 focused. We'll add minimal stub now if needed.

### Tests (`tests/test_scene_activation.py`, `tests/test_scene_termination.py`)
- Activation fails for draft scene? Actually only draft can activate.
- Starship activation creates encounter with correct npcs, links to scene.
- Personal activation creates personnel encounter with correct participant states.
- Narrative activation just changes status.
- End reduces campaign momentum, deactivates encounter, returns closing options.
- Config get/set validates schema.
- GM auth required.

---

## Legacy Cleanup Documentation

Add to `docs/legacy_index.md`:

- `SceneRecord.characters_present_json` – deprecated, replaced by `scene_participants`
- `SceneRecord.enemy_ships_json` – deprecated, replaced by `scene_ships`
- Any scene-related endpoints that become obsolete after M3 (identify later)

---

## Acceptance Criteria

- [ ] New database tables (`scene_participants`, `scene_ships`) exist with FKs
- [ ] Scene connection endpoints work (mutual linking)
- [ ] Scene participants CRUD with visibility and player assignment
- [ ] Scene ships CRUD with visibility
- [ ] Activation creates appropriate encounter record per type
- [ ] End reduces campaign momentum and deactivates encounter
- [ ] Closing options dialog payload includes connected drafts + create/return options
- [ ] Encounter configuration storage and retrieval
- [ ] All tests pass (including existing 257 from M2)
- [ ] Legacy fields untouched, marked deprecated in code comments and docs

---

## Testing Strategy

- **Schema tests**: new columns/tables
- **Integration tests**: Full scene lifecycle: create → add participants/ships → activate → play → end → closing options
- **Authorization tests**: GM-only endpoints enforce session token
- **Validation tests**: duplicate assignments, invalid character/ship references
- **Regression tests**: ensure existing scene routes still work

---

## Parallel Agent Workflow

After Task 3.1 completes:

1. Create separate git worktrees for Agents B, C, D from `feature/m3-scene-management` branch:
   ```bash
   git worktree add ../m3B-worktree feature/m3-scene-management
   git worktree add ../m3C-worktree feature/m3-scene-management
   git worktree add ../m3D-worktree feature/m3-scene-management
   ```

2. Each agent:
   - Works in its own worktree
   - Implements assigned tasks
   - Runs tests after each change
   - Commits to **the same branch** (`feature/m3-scene-management`) regularly
   - Pushes to origin

3. Coordination:
   - Agents B/C/D should not modify the database schema (Task 3.1 domain)
   - If conflicts arise (unlikely but possible on routes file), resolve manually
   - All agents run tests before pushing to avoid breaking others

4. After all tasks complete:
   - Run full test suite: `.venv/bin/python -m pytest tests/ -v`
   - Update `docs/delivery_plan.md` with M3 completion
   - Update `docs/learnings_and_decisions.md`
   - Create PR from `feature/m3-scene-management` to `vtt-scope` (or to main if preferred)

---

## Timeline Estimate

- Task 3.1: 2-3 hrs
- Task 3.2: 3-4 hrs
- Task 3.3: 4-5 hrs
- Task 3.4: 4-5 hrs
- Total: ~15-17 hours (about 2 days with parallel execution)

---

## Questions for User (None Remaining)

All clarifications provided. Proceeding with this plan.
