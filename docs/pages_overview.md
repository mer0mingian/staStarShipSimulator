# STA Starship Simulator - Available Pages

## Public Pages

| Route                    | Template               | Purpose                         |
| ------------------------ | ---------------------- | ------------------------------- |
| `/`                    | `index.html`         | Landing page with campaign list |
| `/campaigns/{id}/join` | `campaign_join.html` | Player character selection page |

## Player Pages

| Route                                 | Template                  | Purpose                 |
| ------------------------------------- | ------------------------- | ----------------------- |
| `/player/home`                      | `player_home.html`      | Player dashboard        |
| `/player/dashboard`                 | `player_dashboard.html` | Alternative player view |
| `/campaigns/{id}/claim/{player_id}` | Redirect                  | Claims a player slot    |

### Dice Roll Interface (M10)

| Route | Template | Purpose |
|-------|----------|---------|
| `/encounters/{id}/dice` | `dice_roll.html` | Player dice roll interface |

### Character Sheet (M10)

| Route | Template | Purpose |
|-------|----------|---------|
| `/characters/{id}/sheet` | `character_sheet.html` | Full character view with Values, Stress, Determination |
| `/characters/{id}/values` | JSON/API | Value interaction (Used/Challenged/Complied) |
| `/characters/{id}/logs` | JSON | Personal Logs, Mission Logs |

### Guided Creation (M10)

| Route | Template | Purpose |
|-------|----------|---------|
| `/characters/new/wizard` | `character_wizard.html` | 4-step creation (Foundation → Specialization → Identity → Equipment) |
| `/ships/new/wizard` | `ship_wizard.html` | Ship creation wizard |

## Game Master Pages

| Route                             | Template                    | Purpose                |
| --------------------------------- | --------------------------- | ---------------------- |
| `/gm`                           | `gm_home.html`            | GM dashboard           |
| `/gm/login`                     | `gm_login.html`           | GM authentication      |
| `/campaigns/new`                | `campaign_new.html`       | Create new campaign    |
| `/campaigns/{id}`               | `campaign_dashboard.html` | Campaign management    |
| `/campaigns/{id}/edit`          | `campaign_edit.html`      | Edit campaign settings |
| `/campaigns/{id}/new-encounter` | `new_encounter.html`      | Create new encounter   |
| `/encounters/{id}/edit`         | `edit_encounter.html`     | Edit encounter         |
| `/scenes/{id}/edit`             | `edit_scene.html`         | Edit scene             |
| `/scenes/{id}/gm`               | `scene_gm.html`           | GM scene view          |

### GM Console (M10)

| Route | Template | Purpose |
|-------|----------|---------|
| `/campaigns/{id}/gm-console` | `gm_console.html` | Threat panel, player resource feedback |
| `/encounters/{id}/traits` | JSON/Form | Manage scene Traits (Difficulty/Complication) |

### Round Tracker (M10)

| Route | Template | Purpose |
|-------|----------|---------|
| `/encounters/{id}/rounds` | `round_tracker.html` | Dynamic round tracking with Action Taken status |

## Combat Pages

| Route                           | Template                   | Purpose             |
| ------------------------------- | -------------------------- | ------------------- |
| `/encounters/{id}`            | `combat.html`            | Encounter overview  |
| `/encounters/{id}/combat`     | `combat_gm.html`         | GM combat view      |
| `/encounters/{id}/view`       | `combat_viewscreen.html` | Viewscreen (public) |
| `/encounters/{id}/player`     | `combat_player.html`     | Player combat view  |
| `/encounters/{id}/player/new` | `combat_player_new.html` | New player combat   |

## Scene Pages

| Route                 | Template                  | Purpose           |
| --------------------- | ------------------------- | ----------------- |
| `/scenes/{id}`      | `scene_player.html`     | Player scene view |
| `/scenes/{id}/view` | `scene_viewscreen.html` | Scene viewscreen  |

## Character & Ship Pages

| Route                          | Template         | Purpose              |
| ------------------------------ | ---------------- | -------------------- |
| `/characters/{id}`           | Character detail | Character sheet view |
| `/api/characters/{id}/model` | JSON             | Character model data |

| Route                     | Template | Purpose         |
| ------------------------- | -------- | --------------- |
| `/ships/{id}` | Ship detail | Ship sheet |
| `/api/ships/{id}/model` | JSON     | Ship model data |

---

## Page Structure Summary

### Sidebar Navigation Flow

```
Home
├── / (Public landing)
├── /campaigns/{id}/join (Join campaign)

Player
├── /player/home (Player dashboard)
│   ├── /characters/{id}/sheet (Character Sheet)
│   │   └── /characters/{id}/values (Manage Values)
│   ├── /characters/new/wizard (Character Creation)
│   ├── /scenes/{id} (View scene)
│   └── Links to active encounters/scenes

Game Master
├── /gm (GM dashboard)
├── Campaign Management
│   ├── /campaigns/new (Create)
│   ├── /campaigns/{id} (View/Edit)
│   ├── /campaigns/{id}/new-encounter
│   └── /campaigns/{id}/gm-console (M10 - Threat/Resources)
├── Encounter Management
│   ├── /encounters/{id}
│   ├── /encounters/{id}/edit
│   ├── /encounters/{id}/combat (GM view)
│   ├── /encounters/{id}/rounds (M10 - Round Tracker)
│   └── /encounters/{id}/dice (M10 - Dice Interface)
└── Scene Management
    ├── /scenes/{id}/edit
    │   └── /scenes/{id}/traits (M10 - Manage Traits)
    └── /scenes/{id}/gm
```

### M10/M11 Key Features

| Feature | Location | Description |
|---------|----------|-------------|
| **Dice Roll Interface** | `/encounters/{id}/dice` | LCARS-styled dice with Target Number, rolled dice display |
| **Character Sheet** | `/characters/{id}/sheet` | Full view with Values, Stress, Determination |
| **Value Interaction** | `/api/characters/{id}/values` | Use/Challenge/Comply endpoints |
| **GM Console** | `/campaigns/{id}/gm-console` | Threat spending, player resource tracking |
| **Round Tracker** | `/encounters/{id}/rounds` | Action Taken status, no fixed turn order |
| **Scene Traits** | `/scenes/{id}/traits` | Modify Difficulty/Complication Range |
| **Character Wizard** | `/characters/new/wizard` | Foundation→Specialization→Identity→Equipment |
| **Logging** | Console output | sta.requests, sta.dice, sta.game, sta.gm loggers |

### Data Flow

1. **Landing Page** (`/`) → Select campaign → **Join Campaign** (`/campaigns/{id}/join`)
2. **Join Campaign** → Select character → **Player Home** (`/player/home`)
3. **Player Home** → 
   - Character Sheet (`/characters/{id}/sheet`) to manage Values
   - Dice Roll (`/encounters/{id}/dice`) for actions
   - Scene View (`/scenes/{id}`) to participate
4. **GM Dashboard** (`/gm`) → Select campaign → **Campaign Dashboard**
5. **Campaign Dashboard** → 
   - GM Console (`/campaigns/{id}/gm-console`) to manage resources
   - Manage encounters/scenes

---

## API Endpoints (JSON)

### Campaigns

- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign
- `PUT /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign

### Characters

- `GET /ap i/characters` - List characters
- `POST /api/characters` - Create character
- `GET /api/characters/{id}` - Get character
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character
- `POST /api/characters/{id}/roll` - **M10**: Dice roll
- `POST /api/characters/{id}/value-interaction` - **M10**: Use/Challenge/Comply Value
- `POST /api/characters/{id}/spend-determination` - **M10**: Spend Determination

### Ships

- `GET /api/ships` - List ships
- `POST /api/ships` - Create ship
- `GET /api/ships/{id}` - Get ship
- `PUT /api/ships/{id}` - Update ship
- `DELETE /api/ships/{id}` - Delete ship

### Encounters

- `GET /api/encounters` - List encounters
- `POST /api/encounters` - Create encounter (deprecated M10 - use scenes)
- `GET /api/encounters/{id}` - Get encounter
- `PUT /api/encounters/{id}` - Update encounter
- `POST /api/encounters/{id}/start` - Start encounter
- `POST /api/encounters/{id}/next-turn` - Next turn

### Scenes (M10)

- `GET /api/scenes` - List scenes
- `POST /api/scenes` - Create scene
- `GET /api/scenes/{id}` - Get scene
- `PUT /api/scenes/{id}` - Update scene
- `POST /api/scenes/{id}/activate` - Activate scene
- `GET /api/scenes/{id}/traits` - **M10**: Get scene traits
- `PUT /api/scenes/{id}/traits` - **M10**: Update scene traits

### Threat (GM - M10)

- `POST /api/campaigns/{id}/threat/spend` - Spend threat
- `POST /api/campaigns/{id}/threat/claim` - Claim momentum to threat
- `GET /api/campaigns/{id}/resources` - Get player resource status

### Round Tracker (M10)

- `POST /api/encounters/{id}/round/start` - Start new round
- `GET /api/encounters/{id}/round/status` - Get round status
- `PUT /api/encounters/{id}/round/participant/{id}/action` - Toggle action taken

### Universe Library

- `GET /api/universe/characters` - Universe character templates
- `GET /api/universe/ships` - Universe ship templates
- `POST /api/universe/import` - Import to campaign
