# Milestone 4: Character/Ship CRUD - Implementation Tasks

## Overview
Complete character and ship creation, management, and library integration. Database schema already exists (VTTCharacterRecord, VTTShipRecord), need to create API endpoints.

## Branch Information
- **Branch**: `feature/m4-char-ship-crud`
- **Base**: `vtt-scope` (after M3 merge)
- **Model**: `opencode/minimax-m2.5-free`
- **Worktree**: Separate worktrees per agent after initial setup

---

## Current State Assessment

### Existing
- `VTTCharacterRecord` database model (sta/database/vtt_schema.py:15-183)
- `VTTShipRecord` database model (sta/database/vtt_schema.py:185-376)
- `UniverseLibraryRecord` and `UniverseItemRecord` for library system
- `TraitRecord`, `TalentRecord`, `WeaponRecord` for game elements
- Campaign routes exist (campaigns.py)
- Scene routes exist (scenes.py)

### Missing (M4 Scope)
- Character CRUD API endpoints (`/api/characters/*`)
- Ship CRUD API endpoints (`/api/ships/*`)
- Library integration endpoints
- Import/export functionality
- Template system for quick creation

---

## Task 4.1: Character Management API

**Agent**: python-dev
**Estimated Time**: 3-4 hours

### Endpoints to create in `sta/web/routes/characters.py` (NEW FILE)

1. `GET /api/characters`
   - List all characters (with optional filters: campaign_id, type)
   - Returns: `[{"id": ..., "name": ..., "character_type": ..., "species": ...}]`

2. `GET /api/characters/<int:id>`
   - Get single character with full details
   - Returns full VTTCharacterRecord data as JSON

3. `POST /api/characters`
   - Create new character
   - Body: `{name, species, role, rank, attributes_json, disciplines_json, ...}`
   - Validates: attributes 7-12, disciplines 0-5, stress 0-max
   - Returns created character

4. `PUT /api/characters/<int:id>`
   - Update character
   - Validates constraints on update
   - Returns updated character

5. `DELETE /api/characters/<int:id>`
   - Delete character (GM only, check campaign association)

6. `GET /api/characters/<int:id>/model`
   - Return as legacy Character model (for compatibility)
   - Uses `VTTCharacterRecord.to_model()`

### Character-Specific Endpoints

7. `PUT /api/characters/<int:id>/stress`
   - Adjust stress value
   - Body: `{adjustment: int}` (positive or negative)
   - Validates bounds (0 to stress_max)

8. `PUT /api/characters/<int:id>/determination`
   - Adjust determination
   - Body: `{adjustment: int}`

9. `PUT /api/characters/<int:id>/state`
   - Update character state (Ok, Fatigued, Injured, Dead)
   - Body: `{state: string}`

10. `GET /api/characters/<int:id>/talents`
    - List available talents for character

11. `POST /api/characters/<int:id>/talents`
    - Add talent to character
    - Body: `{talent_name: string}`

### Tests (`tests/test_characters_api.py`)
- CRUD operations
- Validation (attribute/discipline ranges)
- Stress/determination adjustment bounds
- State transitions
- GM authorization

### Verification
```bash
.venv/bin/python -m pytest tests/test_characters_api.py -v
```

---

## Task 4.2: Ship Management API

**Agent**: python-dev
**Estimated Time**: 3-4 hours

### Endpoints to create in `sta/web/routes/ships.py` (NEW FILE)

1. `GET /api/ships`
   - List all ships (with optional filters: campaign_id)
   - Returns: `[{"id": ..., "name": ..., "ship_class": ..., "scale": ...}]`

2. `GET /api/ships/<int:id>`
   - Get single ship with full details
   - Returns full VTTShipRecord data

3. `POST /api/ships`
   - Create new ship
   - Body: `{name, ship_class, scale, systems_json, departments_json, ...}`
   - Validates: systems 7-12, departments 0-5, scale 1-7

4. `PUT /api/ships/<int:id>`
   - Update ship
   - Validates constraints
   - Returns updated ship

5. `DELETE /api/ships/<int:id>`
   - Delete ship (GM only)

6. `GET /api/ships/<int:id>/model`
   - Return as legacy Starship model

### Ship-Specific Endpoints

7. `PUT /api/ships/<int:id>/shields`
   - Adjust shields
   - Body: `{shields: int, raised: bool}`
   - Validates bounds (0 to shields_max)

8. `PUT /api/ships/<int:id>/power`
   - Adjust power
   - Body: `{current: int, reserve: bool}`

9. `PUT /api/ships/<int:id>/breach`
   - Add/remove system breach
   - Body: `{system: string, potency: int, action: "add"|"remove"}`

10. `PUT /api/ships/<int:id>/weapons`
    - Update weapons list
    - Body: `{weapons_json: string}`

11. `POST /api/ships/<int:id>/weapons/<weapon_name>/arm`
    - Arm/disarm weapon
    - Body: `{armed: bool}`

### NPC Ship Endpoints

12. `GET /api/ships/<int:id>/crew-quality`
    - Get/set crew quality (NPC only)
    - Body: `{quality: "elite"|"veteran"|"seasoned"|"green"|null}`

### Tests (`tests/test_ships_api.py`)
- CRUD operations
- Validation (scale, systems, departments)
- Shield/power adjustments
- Breach management
- GM authorization

### Verification
```bash
.venv/bin/python -m pytest tests/test_ships_api.py -v
```

---

## Task 4.3: Library Integration

**Agent**: python-dev
**Estimated Time**: 2-3 hours

### Endpoints in `sta/web/routes/universe.py` (EXTEND EXISTING)

1. `GET /api/universe/characters`
   - List characters in universe library
   - Filters: category (pcs, npcs, creatures)

2. `POST /api/universe/characters`
   - Add character to universe library
   - Body: `{name, category, data_json, description, image_url}`

3. `GET /api/universe/ships`
   - List ships in universe library

4. `POST /api/universe/ships`
   - Add ship to universe library

5. `POST /api/universe/import/character/<int:universe_item_id>`
   - Import character from library to campaign
   - Creates VTTCharacterRecord with copied data
   - Body: `{campaign_id: int, name_override: string|null}`

6. `POST /api/universe/import/ship/<int:universe_item_id>`
   - Import ship from library to campaign
   - Creates VTTShipRecord with copied data

7. `GET /api/universe/templates/characters`
   - List pre-built character templates

8. `GET /api/universe/templates/ships`
   - List pre-built ship templates

### Helper Endpoints

9. `GET /api/campaigns/<int:campaign_id>/characters/available`
   - Characters available to add to campaign
   - Union of: campaign PCs, campaign NPCs, universe library items

10. `GET /api/campaigns/<int:campaign_id>/ships/available`
    - Ships available to add to campaign

### Tests (`tests/test_universe_integration.py`)
- Library CRUD
- Import to campaign
- Template listing
- Available character/ship filtering
- GM authorization

### Verification
```bash
.venv/bin/python -m pytest tests/test_universe_integration.py -v
```

---

## Task 4.4: Import/Export Functionality

**Agent**: python-dev
**Estimated Time**: 1-2 hours

### Endpoints

1. `GET /api/characters/<int:id>/export`
   - Export character as JSON
   - Returns full character data for backup/transfer

2. `POST /api/characters/import`
   - Import character from JSON
   - Body: `{character_json: object, campaign_id: int|null}`

3. `GET /api/ships/<int:id>/export`
   - Export ship as JSON

4. `POST /api/ships/import`
   - Import ship from JSON

### Tests (`tests/test_import_export.py`)
- Round-trip export/import
- Validation on import
- Campaign association on import

### Verification
```bash
.venv/bin/python -m pytest tests/test_import_export.py -v
```

---

## Acceptance Criteria

- [ ] Character CRUD API functional with all endpoints
- [ ] Ship CRUD API functional with all endpoints
- [ ] All validation constraints enforced
- [ ] Stress/determination/shield adjustments work correctly
- [ ] Library integration allows import from universe
- [ ] Import/export functionality works
- [ ] All tests pass
- [ ] GM authorization enforced where required

---

## Testing Strategy

- **Unit Tests**: Model validation, serialization
- **API Tests**: Endpoint validation, error handling
- **Integration Tests**: Full CRUD workflows
- **Import/Export Tests**: Data serialization round-trips

---

## Parallel Agent Workflow

After Task 4.1 (character API) is started:

1. Create separate git worktrees for agents from `feature/m4-char-ship-crud`:
   ```bash
   git worktree add ../m4-worktree -b feature/m4-char-ship-crud
   ```

2. Agents work in parallel:
   - Agent A: Task 4.1 (Character API)
   - Agent B: Task 4.2 (Ship API)

3. After Tasks 4.1 & 4.2 complete, Task 4.3 can proceed

4. After all tasks:
   - Run full test suite: `.venv/bin/python -m pytest tests/ -v`
   - Update `docs/delivery_plan.md`
   - Create PR

---

## Timeline Estimate

- Task 4.1: 3-4 hrs
- Task 4.2: 3-4 hrs
- Task 4.3: 2-3 hrs
- Task 4.4: 1-2 hrs
- Total: ~10-13 hours

---

## Questions

None - all clarifications provided.
