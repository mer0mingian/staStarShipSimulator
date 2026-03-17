# Milestone 7: Export/Import Features

## Overview
Export/Import functionality for VTT characters, ships, and campaign backups.

## Branch Information
- **Branch**: `feature/m7-import-export`
- **Base**: `vtt-scope` (after M6 merge)
- **Model**: `opencode/minimax-m2.5-free`

---

## Current Status
- M6 PR merged to vtt-scope
- M7 ready to begin

---

## Tasks

### M7.1: VTT Character Export/Import
**Endpoint**: `/api/vtt/characters/import` and `/api/vtt/characters/{id}/export`

Export individual VTT character as JSON:
```json
{
  "name": "Captain Janeway",
  "species": "Human",
  "rank": "Captain",
  "role": "Command",
  "pronouns": "she/her",
  "description": "Captain of Voyager",
  "attributes": {
    "control": 9,
    "fitness": 8,
    "daring": 10,
    "insight": 9,
    "presence": 11,
    "reason": 10
  },
  "disciplines": {
    "command": 4,
    "conn": 2,
    "engineering": 2,
    "medicine": 1,
    "science": 2,
    "security": 2
  },
  "stress": 4,
  "stress_max": 5,
  "determination": 2,
  "determination_max": 3,
  "talents": ["Command Presence", "Resolve"],
  "focuses": ["Astrophysics", "Photonics"],
  "values": ["Integrity", "Discovery"],
  "equipment": ["Commbadge", "Tricorder"],
  "environment": "Indiana",
  "upbringing": "Military Academy",
  "career_path": "Starfleet"
}
```

Import accepts either a single character object or a container with `characters` key:
```json
{
  "characters": [
    {
      "name": "New Character",
      "species": "Vulcan",
      ...
    }
  ]
}
```

**Validation rules**:
- Attributes: 7-12
- Disciplines: 0-5
- Stress: 0 to stress_max
- Required: name, species, attributes, disciplines

---

### M7.2: VTT Ship Export/Import
**Endpoint**: `/api/vtt/ships/import` and `/api/vtt/ships/{id}/export`

Export individual VTT ship as JSON (see full spec in overview section above).

Import accepts either a single ship object or container with `ships` key. Also accepts `registry` as alias for `ship_registry`.

**Validation rules**:
- Systems: 7-12
- Departments: 0-5
- Scale: 1-7
- Shields: 0 to shields_max

---

### M7.3: Full Campaign Backup
**Endpoint**: `/api/backup`

Export all campaign data including characters, NPCs, ships:
```json
{
  "version": "1.0",
  "exported_at": "2025-01-15T10:30:00Z",
  "characters": [...],
  "npcs": [...],
  "ships": [...],
  "campaigns": [...]
}
```

---

## Implementation Notes
- Implement import validation similar to creation validation
- Support both single-object and container formats for imports
- Provide clear error messages for invalid data
- Preserve existing IDs where applicable for updates

---

## Parallel Execution Strategy

All three tasks are independent and can run in parallel:

| Task | Dependencies | Can Run In Parallel With |
|------|--------------|--------------------------|
| M7.1 Character Export/Import | None | M7.2, M7.3 |
| M7.2 Ship Export/Import | None | M7.1, M7.3 |
| M7.3 Campaign Backup | None | M7.1, M7.2 |

**Recommended Agent Allocation**:
- **Agent 1**: M7.1 (Character Export/Import)
- **Agent 2**: M7.2 (Ship Export/Import)
- **Agent 3**: M7.3 (Campaign Backup)

---

## Agent Prompts

### Prompt for Agent 1: Character Export/Import

```markdown
## Task: Implement VTT Character Export/Import (M7.1)

### Context
You are working on the m7-branch. M5 (FastAPI) and M6 (UI/UX) are complete. Now implementing import/export features.

### IMPORTANT: Worktree Setup
1. Create a NEW git worktree for this task:
   ```bash
   cd /home/mer0/repositories/staStarShipSimulator
   git worktree add -b feature/m7-character-import-export ../m7-character-import-export m7-branch
   cd ../m7-character-import-export
   uv venv
   uv pip install -r requirements.txt -r requirements-dev.txt
   ```

### Read These Files First
- README.md - understand project structure and test commands
- docs/README.md - understand documentation structure
- docs/tasks/milestone7_tasks.md - understand M7 requirements

### Objectives
Implement Character Export/Import endpoints:

1. **Export**: `GET /api/vtt/characters/{id}/export`
   - Returns character as JSON with all fields
   - Includes: name, species, rank, role, pronouns, description, attributes, disciplines, stress, determination, talents, focuses, values, equipment, environment, upbringing, career_path

2. **Import**: `POST /api/vtt/characters/import`
   - Accepts single character object OR container with `characters` key
   - Validates: attributes (7-12), disciplines (0-5), stress (0 to stress_max)
   - Required fields: name, species, attributes, disciplines
   - Returns created character IDs or error messages

### Implementation Location
Add endpoints to `sta/web/routes/characters_router.py` or create new `sta/web/routes/import_export_router.py`

### Measurable Success Criteria
- [ ] GET /api/vtt/characters/{id}/export returns valid JSON with all character fields
- [ ] POST /api/vtt/characters/import accepts single character object
- [ ] POST /api/vtt/characters/import accepts {"characters": [...]} format
- [ ] Import validates attributes 7-12, disciplines 0-5
- [ ] Import returns 400 with clear error for invalid data
- [ ] Import returns 201 with character IDs on success
- [ ] `pytest tests/test_characters_api.py` passes (0 failed)

### Implementation Guidelines
- Use FastAPI patterns (async, Body parameters, Pydantic models)
- Follow existing route patterns in characters_router.py
- Use uv for dependency management

### Verification Command
```bash
cd /home/mer0/repositories/m7-character-import-export
uv run pytest tests/test_characters_api.py -v
```

### Model
Use `opencode/minimax-m2.5-free`

### When Complete
1. Run verification tests
2. Commit all changes
3. Push your branch: `git push -u origin feature/m7-character-import-export`
4. Report back: tests passed/failed count
```

---

### Prompt for Agent 2: Ship Export/Import

```markdown
## Task: Implement VTT Ship Export/Import (M7.2)

### Context
You are working on the m7-branch. M5 (FastAPI) and M6 (UI/UX) are complete.

### IMPORTANT: Worktree Setup
1. Create a NEW git worktree for this task:
   ```bash
   cd /home/mer0/repositories/staStarShipSimulator
   git worktree add -b feature/m7-ship-import-export ../m7-ship-import-export m7-branch
   cd ../m7-ship-import-export
   uv venv
   uv pip install -r requirements.txt -r requirements-dev.txt
   ```

### Read These Files First
- README.md - understand project structure and test commands
- docs/README.md - understand documentation structure
- docs/tasks/milestone7_tasks.md - understand M7 requirements

### Objectives
Implement Ship Export/Import endpoints:

1. **Export**: `GET /api/vtt/ships/{id}/export`
   - Returns ship as JSON with all fields
   - Includes: name, ship_class, ship_registry, scale, systems, departments, weapons, talents, traits, shields, resistance, etc.
   - Accepts `registry` as alias for `ship_registry`

2. **Import**: `POST /api/vtt/ships/import`
   - Accepts single ship object OR container with `ships` key
   - Validates: systems (7-12), departments (0-5), scale (1-7), shields (0 to shields_max)
   - Required fields: name, ship_class, systems, departments

### Implementation Location
Add endpoints to `sta/web/routes/ships_router.py` or create new `sta/web/routes/import_export_router.py`

### Measurable Success Criteria
- [ ] GET /api/vtt/ships/{id}/export returns valid JSON with all ship fields
- [ ] POST /api/vtt/ships/import accepts single ship object
- [ ] POST /api/vtt/ships/import accepts {"ships": [...]} format
- [ ] POST /api/vtt/ships/import accepts "registry" as alias for "ship_registry"
- [ ] Import validates systems 7-12, departments 0-5, scale 1-7
- [ ] Import returns 400 with clear error for invalid data
- [ ] Import returns 201 with ship IDs on success
- [ ] `pytest tests/test_ships_api.py` passes (0 failed)

### Implementation Guidelines
- Use FastAPI patterns (async, Body parameters)
- Follow existing route patterns in ships_router.py
- Use uv for dependency management

### Verification Command
```bash
cd /home/mer0/repositories/m7-ship-import-export
uv run pytest tests/test_ships_api.py -v
```

### Model
Use `opencode/minimax-m2.5-free`

### When Complete
1. Run verification tests
2. Commit all changes
3. Push your branch: `git push -u origin feature/m7-ship-import-export`
4. Report back: tests passed/failed count
```

---

### Prompt for Agent 3: Campaign Backup

```markdown
## Task: Implement Full Campaign Backup (M7.3)

### Context
You are working on the m7-branch. M5 (FastAPI) and M6 (UI/UX) are complete.

### IMPORTANT: Worktree Setup
1. Create a NEW git worktree for this task:
   ```bash
   cd /home/mer0/repositories/staStarShipSimulator
   git worktree add -b feature/m7-campaign-backup ../m7-campaign-backup m7-branch
   cd ../m7-campaign-backup
   uv venv
   uv pip install -r requirements.txt -r requirements-dev.txt
   ```

### Read These Files First
- README.md - understand project structure and test commands
- docs/README.md - understand documentation structure
- docs/tasks/milestone7_tasks.md - understand M7 requirements

### Objectives
Implement Campaign Backup endpoints:

1. **Export Campaign**: `GET /api/backup/{campaign_id}`
   - Returns full campaign data as JSON
   - Includes: version, exported_at, characters, npcs, ships, campaigns
   - Version format: "1.0"

2. **Import Campaign**: `POST /api/backup/import`
   - Accepts backup JSON
   - Creates new campaign with all linked data
   - Returns created campaign ID

### Implementation Location
Create or extend `sta/web/routes/import_export_router.py`

### Measurable Success Criteria
- [ ] GET /api/backup/{campaign_id} returns JSON with version, exported_at, characters, npcs, ships, campaigns
- [ ] Exported JSON includes all campaign characters
- [ ] Exported JSON includes all campaign NPCs
- [ ] Exported JSON includes all campaign ships
- [ ] POST /api/backup/import accepts valid backup JSON
- [ ] POST /api/backup/import creates new campaign with linked data
- [ ] `pytest tests/test_vtt_campaign_integration.py` passes (0 failed)

### Implementation Guidelines
- Use FastAPI patterns (async, Body parameters)
- Query all related data: characters, NPCs, ships linked to campaign
- Use uv for dependency management

### Verification Command
```bash
cd /home/mer0/repositories/m7-campaign-backup
uv run pytest tests/test_vtt_campaign_integration.py -v
```

### Model
Use `opencode/minimax-m2.5-free`

### When Complete
1. Run verification tests
2. Commit all changes
3. Push your branch: `git push -u origin feature/m7-campaign-backup`
4. Report back: tests passed/failed count
```

---

## Acceptance Criteria (Measurable)

### Character Export/Import
- [ ] GET /api/vtt/characters/{id}/export returns valid JSON with all character fields
- [ ] POST /api/vtt/characters/import accepts single character and array format
- [ ] Import validates attributes (7-12), disciplines (0-5), stress (0-max)
- [ ] Import returns 400 with error message for invalid data
- [ ] Import returns 201 with created character IDs
- [ ] tests/test_characters_api.py: 0 failed

### Ship Export/Import
- [ ] GET /api/vtt/ships/{id}/export returns valid JSON with all ship fields
- [ ] POST /api/vtt/ships/import accepts single ship and array format
- [ ] Import validates systems (7-12), departments (0-5), scale (1-7)
- [ ] Import accepts "registry" as alias for "ship_registry"
- [ ] Import returns 400 with error message for invalid data
- [ ] tests/test_ships_api.py: 0 failed

### Campaign Backup
- [ ] GET /api/backup/{campaign_id} returns complete backup JSON
- [ ] Backup includes version, exported_at, characters, npcs, ships
- [ ] POST /api/backup/import creates new campaign with all data
- [ ] tests/test_vtt_campaign_integration.py: 0 failed

### Overall
- [ ] All tests pass: `uv run pytest` (0 failed, allow skipped)
- [ ] No breaking changes to existing functionality

---

## Timeline Estimate
- M7.1: 2-3 hrs
- M7.2: 2-3 hrs
- M7.3: 2-3 hrs
- Total: ~9 hours (can be parallelized)

---

## Current Agent Status (2026-03-17)

### Status: TODO - Ready for Agent Deployment

M7 is ready to begin. Three python-dev agents can be deployed in parallel:
- Agent 1: M7.1 Character Export/Import
- Agent 2: M7.2 Ship Export/Import  
- Agent 3: M7.3 Campaign Backup

---

## Next Steps

1. **Deploy agents** in parallel for M7 tasks
2. **Track progress** in this document
3. **Verify tests** after each task
4. **Merge** to vtt-scope when complete
5. **Create PR** to vtt-scope
