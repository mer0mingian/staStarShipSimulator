# Implementation Plan - STA Starship Simulator Extensions

## Design Principle: Additive Schema Changes
To maintain compatibility with the upstream branch, **create new tables** for new features instead of modifying existing schema tables.

---

## Core Concept: Scene as First-Class Entity

**Design Philosophy:** A Scene is the primary container for GM narrative context. Combat (starship or personnel) is a special type of scene activation, not a separate entity.

```
Scene
├── Traits (visible to players when activated)
│   └── Each trait: {name, description} for hover/click info
├── Extended Tasks (challenges with progress tracking)
│   └── Each task: {name, progress, resistance, magnitude, breakthrough_1, breakthrough_2}
├── Picture (optional visual)
├── Stardate
├── Characters Present
└── Combat (optional)
    ├── Starship Combat
    └── Personnel/Social Combat (future)
```

**Workflow:**
1. GM creates scenes ahead of time (prep)
2. GM activates a scene → players see traits, challenges, picture
3. GM can start combat within a scene → tactical map overlay
4. Combat ends → scene continues with updated state

---

## Future Features (Documented)

### Alert Conditions for Ship Combat
- **Red Alert**: Ship in immediate danger
  - Visual: Flashing red overlay on viewscreen
  - Optional: Sound effect (klaxon)
  - Optional: Bonus to certain actions
- **Yellow Alert**: Ship at heightened readiness
  - Visual: Yellow tint on viewscreen
- **Normal/Blue**: Standard operations
- Toggle button in GM view during starship combat

---

## Milestone 1: Overview Screen Enhancements (IN PROGRESS)
**Goal:** Empower the GM to present scene context on the viewscreen.

### Database Changes (`sta/database/schema.py`)
- ✅ Create NEW table `SceneRecord`:
    - `id` (PK)
    - `encounter_id` (FK to encounters, nullable - scene can exist without active combat)
    - `campaign_id` (FK to campaigns - for pre-generated scenes)
    - `scene_picture_url` (String, nullable)
    - `scene_traits_json` (Text, default "[]") - Format: `[{name, description}]`
    - `challenges_json` (Text, default "[]") - Format: `[{name, progress, resistance, magnitude, breakthrough_1, breakthrough_2}]`
    - `stardate` (String, nullable)
    - `characters_present_json` (Text, default "[]") - List of Character IDs
    - `is_active` (Boolean) - Scene activation state
    - `name` (String) - Scene name for GM reference

### Backend
- ✅ Load `SceneRecord` alongside `EncounterRecord` where applicable.
- ✅ Add API endpoints for scene updates.
- ✅ Add API endpoints for scene CRUD (create, activate, convert, delete).
- ✅ Validation for scene conversion (requires player ship + NPCs for combat).

### Frontend
- ✅ Combined "Draft Scenes & Encounters" section in campaign dashboard
- ✅ Scene type indicators (🎬 narrative, 🚀 starship combat, etc.)
- ✅ Scene settings panel with stardate, traits, challenges
- ✅ Extended Tasks with breakthroughs
- ✅ Traits with descriptions
- ✅ Narrative scene GM view (reuses combat_gm.html)
- ✅ Narrative scene viewscreen (reuses combat_viewscreen.html)
- ✅ Narrative scene player view (reuses combat.html)
- ✅ Extended Tasks section in narrative GM view
- ✅ NPC visibility toggles in narrative scenes
- ✅ Add NPC button and modal for narrative scenes
- ⬜ Picture gallery/upload system

### Remaining Work
- [ ] Add picture gallery/upload system

---

## Milestone 2: Crew Manifest & Character Management

### Lessons Learned from Milestone 1 Discussion

#### NPC System Design
- **NPC Types** (from STA 2E Ch 11.1):
  - **Major NPCs**: Full stats, important characters
  - **Notable NPCs**: Simplified stats, recurring characters
  - **Minor NPCs**: Basic info, one-scene characters
  - **NPC Crew**: Ship crew members (minimal stats)

- **NPC Fields**:
  - `name`, `npc_type`
  - `appearance`, `motivation`, `affiliation`, `location`
  - `picture_url`
  - For Major/Notable: `attributes_json`, `disciplines_json`, `stress`, `stress_max`
  - For NPC Crew: `ship_id` (FK to starships)

- **NPC Archive** (global pool):
  - NPCs created once, reusable across campaigns
  - GM can create on-the-fly during scenes
  - Copy existing NPCs to create variants

- **Campaign Manifest** (`CampaignNPCRecord`):
  - Links NPCs from archive to specific campaign
  - Default `is_visible_to_players = False`

- **Scene NPCs** (`SceneNPCRecord`):
  - Links NPCs to active scene
  - Can reference archive NPC OR have quick on-the-fly fields
  - Visibility toggle per scene

#### Character Import
- **BC Holmes Generator**: Located at `~/repositories/StarTrek2d20`
- Export format: JSON-based (need to analyze format from source code)
- Import should handle: attributes, disciplines, talents, traits
- Consider: field mapping between BC Holmes and our schema

#### Extended Character Fields
- Main/Support characters need:
  - `type` (Main, Support, NPC)
  - `pronouns`
  - `environment`, `upbringing`, `career_path`
  - `values_json`
  - `equipment_json`
  - `avatar_url`

#### Integration Points
- Scene activation: GM selects characters from manifest to be "present"
- Narrative scenes: NPCs listed with visibility toggles
- Combat conversion: NPCs required before converting to combat types
- Character traits: GM can add traits that persist on character

### Database Changes
- ✅ `NPCRecord` - Global NPC archive
- ✅ `CampaignNPCRecord` - NPCs assigned to campaigns
- ✅ `SceneNPCRecord` - NPCs in scenes
- ✅ `CharacterTraitRecord` - Persistent character traits

### Implementation Tasks
1. [ ] Analyze BC Holmes export format (check `~/repositories/StarTrek2d20`)
2. [ ] Create NPC management UI (archive, campaign manifest)
3. [ ] Add "Add NPC" button to narrative scene GM view
4. [ ] Create character list/edit pages
5. [ ] Implement BC Holmes import

---

## Milestone 3: Character Conflict
**Goal:** Extend combat system to support personnel scale encounters.

### Database Changes
- Create NEW table `PersonnelEncounterRecord`:
    - `id` (PK)
    - `scene_id` (FK to scenes) - Combat lives within a scene
    - `combat_type` (Enum: 'starship', 'personnel', 'social')
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

## Feature Ideas (Future)
- **Pictures for Starships and Characters:** Add `picture_url` field to both for visual display on sheets/viewscreen
- **Quickstart Presets:** Seed data for quick demo/development (restore after DB reset)


### Frontend
- ✅ **GM View:** Stardate, Picture URL, Scene Traits inputs
- ✅ **Viewscreen:** Display Stardate, Scene Traits, Challenges
- ⬜ **Picture overlay mode** (show_picture toggle)
- ⬜ **Challenges UI** with progress tracking

### Remaining Work
- [ ] Add `campaign_id` and `is_active` to SceneRecord
- [ ] Scene management in campaign dashboard (create/edit scenes before encounter)
- [ ] Scene activation notification to players
- [ ] Picture overlay on viewscreen

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
    - `scene_id` (FK to scenes) - Combat lives within a scene
    - `combat_type` (Enum: 'starship', 'personnel', 'social')
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

## Feature Ideas (Future)
- **Pictures for Starships and Characters:** Add `picture_url` field to both for visual display on sheets/viewscreen
- **Quickstart Presets:** Seed data for quick demo/development (restore after DB reset)

---

## Reference Files
- Rules: See `docs/rules_reference.md` for STA 2E rule locations.
- BC Holmes Generator: `~/repositories/StarTrek2d20`
