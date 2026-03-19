# STA Starship Simulator - Available Pages

## Public Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `/` | `index.html` | Landing page with campaign list |
| `/campaigns/{id}/join` | `campaign_join.html` | Player character selection page |

## Player Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `/player/home` | `player_home.html` | Player dashboard |
| `/player/dashboard` | `player_dashboard.html` | Alternative player view |
| `/campaigns/{id}/claim/{player_id}` | Redirect | Claims a player slot |

## Game Master Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `/gm` | `gm_home.html` | GM dashboard |
| `/gm/login` | `gm_login.html` | GM authentication |
| `/campaigns/new` | `campaign_new.html` | Create new campaign |
| `/campaigns/{id}` | `campaign_dashboard.html` | Campaign management |
| `/campaigns/{id}/edit` | `campaign_edit.html` | Edit campaign settings |
| `/campaigns/{id}/new-encounter` | `new_encounter.html` | Create new encounter |
| `/encounters/{id}/edit` | `edit_encounter.html` | Edit encounter |
| `/scenes/{id}/edit` | `edit_scene.html` | Edit scene |
| `/scenes/{id}/gm` | `scene_gm.html` | GM scene view |

## Combat Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `/encounters/{id}` | `combat.html` | Encounter overview |
| `/encounters/{id}/combat` | `combat_gm.html` | GM combat view |
| `/encounters/{id}/view` | `combat_viewscreen.html` | Viewscreen (public) |
| `/encounters/{id}/player` | `combat_player.html` | Player combat view |
| `/encounters/{id}/player/new` | `combat_player_new.html` | New player combat |

## Scene Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `/scenes/{id}` | `scene_player.html` | Player scene view |
| `/scenes/{id}/view` | `scene_viewscreen.html` | Scene viewscreen |

## Character Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `/characters/{id}` | Character detail | Character sheet view |
| `/api/characters/{id}/model` | JSON | Character model data |

## Ship Pages

| Route | Template | Purpose |
|-------|----------|---------|
| `/api/ships/{id}/model` | JSON | Ship model data |

---

## Page Structure Summary

### Sidebar Navigation Flow

```
Home
├── / (Public landing)
├── /campaigns/{id}/join (Join campaign)

Player
├── /player/home (Player dashboard)
│   └── Links to active encounters/scenes

Game Master
├── /gm (GM dashboard)
├── Campaign Management
│   ├── /campaigns/new (Create)
│   ├── /campaigns/{id} (View/Edit)
│   └── /campaigns/{id}/new-encounter
├── Encounter Management
│   ├── /encounters/{id}
│   ├── /encounters/{id}/edit
│   └── /encounters/{id}/combat (GM view)
└── Scene Management
    ├── /scenes/{id}/edit
    └── /scenes/{id}/gm
```

### Data Flow

1. **Landing Page** (`/`) → Select campaign → **Join Campaign** (`/campaigns/{id}/join`)
2. **Join Campaign** → Select character → **Player Home** (`/player/home`)
3. **Player Home** → Join encounter → **Combat View** (`/encounters/{id}/player`)
4. **GM Dashboard** (`/gm`) → Select campaign → **Campaign Dashboard**
5. **Campaign Dashboard** → Manage encounters/scenes

---

## API Endpoints (JSON)

### Campaigns
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign
- `PUT /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign

### Characters
- `GET /api/characters` - List characters
- `POST /api/characters` - Create character
- `GET /api/characters/{id}` - Get character
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character

### Ships
- `GET /api/ships` - List ships
- `POST /api/ships` - Create ship
- `GET /api/ships/{id}` - Get ship
- `PUT /api/ships/{id}` - Update ship
- `DELETE /api/ships/{id}` - Delete ship

### Encounters
- `GET /api/encounters` - List encounters
- `POST /api/encounters` - Create encounter
- `GET /api/encounters/{id}` - Get encounter
- `PUT /api/encounters/{id}` - Update encounter
- `POST /api/encounters/{id}/start` - Start encounter
- `POST /api/encounters/{id}/next-turn` - Next turn

### Universe Library
- `GET /api/universe/characters` - Universe character templates
- `GET /api/universe/ships` - Universe ship templates
- `POST /api/universe/import` - Import to campaign
