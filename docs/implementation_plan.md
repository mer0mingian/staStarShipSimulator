# Implementation Plan - STA Starship Simulator Extensions

## Design Principle: Additive Schema Changes
To maintain compatibility with the upstream branch, **create new tables** for new features instead of modifying existing schema tables.

---

## Milestone 1: Overview Screen Enhancements
**Goal:** Empower the GM to present scene context on the viewscreen.

### Database Changes (`sta/database/schema.py`)
- Create NEW table `SceneRecord`:
    - `id` (PK)
    - `encounter_id` (FK to encounters)
    - `scene_picture_url` (String, nullable)
    - `scene_traits_json` (Text, default "[]")
    - `challenges_json` (Text, default "[]") - Structure: `[{name, progress, resistance, difficulty}]`
    - `stardate` (String, nullable)
    - `characters_present_json` (Text, default "[]") - List of Character IDs

### Backend (`sta/web/routes/encounters.py`)
- Load `SceneRecord` alongside `EncounterRecord` where applicable.
- Add API endpoints for scene updates.

### Frontend
- **GM View (`combat_gm.html`):**
    - Add "Scene Settings" panel with input fields for Stardate, Picture URL.
    - Add "Scene Traits" manager (Add/Remove tags).
    - Add "Challenges" manager.
- **Viewscreen (`combat_viewscreen.html`):**
    - Add "Scene Info" panel (overlay or side tab).
    - Display Stardate prominently.
    - Display Scene Traits and Active Challenges.
    - Support "Show Picture" mode (hides map/stats, shows image).

---

## Milestone 2: Crew Manifest & Character Management
**Goal:** Manage the crew (Main, Support, NPCs) and select them for scenes.

### Database Changes (`sta/database/schema.py`)
- Create NEW table `ExtendedCharacterRecord`:
    - `id` (PK)
    - `character_id` (FK to characters, unique)
    - `type` (Enum: Main, Support, NPC)
    - `pronouns` (String)
    - `environment`, `upbringing`, `career_path` (Strings)
    - `values_json` (Text)
    - `equipment_json` (Text)
    - `avatar_url` (String)
    - `import_source` (String, nullable) - e.g., "bcholmes"

### Backend (`sta/web/routes/characters.py` - NEW)
- `index`: List all characters (filter by type).
- `create`: Form for new character.
- `edit`: Edit existing character.
- `import`: Import from JSON (BC Holmes format).
    - Reference: `~/repositories/StarTrek2d20` for format analysis.

### Frontend
- `templates/character_list.html`: Table/Card view of crew.
- `templates/character_edit.html`: Full character sheet form.
- `templates/macros/character_card.html`: Reusable component.

---

## Milestone 3: Character Conflict
**Goal:** Extend combat system to support personnel scale encounters.

### Database Changes
- Create NEW table `PersonnelEncounterRecord`:
    - `id` (PK)
    - `encounter_id` (FK to encounters, unique)
    - `combat_type` (Enum: 'starship', 'personnel')
    - `character_positions_json` (Text) - Mapped to map coords.
    - `character_states_json` (Text) - Stress, injuries per character.

### Mechanics
- Define `PersonnelActions` (Phaser Fire, Unarmed Strike, Move, Recover, Guard).
- Adapt `action_config.py` to support "Personnel" scale actions.

### Frontend
- Update `hex-map.js`: Support character tokens (smaller, different visual style).
- Update `combat.html`:
    - If `combat_type == 'personnel'`, load character actions instead of ship actions.
    - Display Character Status (Stress, Injured) instead of Ship Status (Shields, Breaches).

---

## Milestone 4: Character Sheets
**Goal:** Players can view their sheets; GM can modify them dynamically.

### Frontend
- `templates/character_sheet.html`: A digital character sheet view.
    - Responsive layout (Attributes/Disciplines on top).
    - Clickable values for rolling (future enhancement).
- Update `player_dashboard.html` to link to the sheet.

### Backend
- API endpoint for GM to add Traits/Values to a character on the fly.

---

## Milestone 5: Personal Logs
**Goal:** Players can record their mission logs.

### Database Changes
- Create NEW table `PersonalLogRecord`:
    - `id`, `character_id`, `stardate`, `content` (Markdown), `image_url`.

### Frontend
- `templates/logs/list.html`: Timeline of logs.
- `templates/logs/edit.html`: Editor with Markdown support.
- PDF Export (using a library like `weasyprint` or client-side JS).

---

## Reference Files
- Rules: See `docs/rules_reference.md` for STA 2E rule locations.
- BC Holmes Generator: `~/repositories/StarTrek2d20`
