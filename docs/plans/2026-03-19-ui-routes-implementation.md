# UI Routes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Wire up all HTML templates so browsing to `http://localhost:5001/` shows a graphical landing page, and all other pages (player/GM dashboards, scenes, combat, etc.) render properly.

**Architecture:** 
- Create a new `ui_router.py` with all HTML page routes using FastAPI + Starlette's `Jinja2Templates`
- Replace Flask `url_for()` calls in templates with hardcoded URLs (simpler than `url_path_for`)
- Configure `Jinja2Templates` in `app.py`
- Fix Flask-specific `get_flashed_messages()` in `base.html`

**Tech Stack:** FastAPI, Starlette `Jinja2Templates`, Jinja2

---

## Flask URL Mapping

| Flask `url_for()` | FastAPI route |
|---|---|
| `main.index` | `/` |
| `campaigns.player_home` | `/player/home` |
| `campaigns.gm_home` | `/gm` |
| `campaigns.gm_login` | `/gm/{campaign_id}/login` |
| `campaigns.new_campaign` | `/campaigns/new` |
| `campaigns.campaign_list` | `/campaigns` |
| `campaigns.join_campaign` | `/campaigns/{campaign_id}/join` |
| `campaigns.campaign_dashboard` | `/campaigns/{campaign_id}` |
| `campaigns.player_dashboard` | `/campaigns/{campaign_id}/player` |
| `campaigns.switch_character` | `/campaigns/{campaign_id}/switch-character` |
| `scenes.view_scene` | `/scenes/{scene_id}?role=gm\|player\|viewscreen` |
| `scenes.edit_scene` | `/scenes/{scene_id}/edit` |
| `scenes.new_scene` | `/scenes/new` |
| `encounters.combat` | `/encounters/{encounter_id}?role=gm\|player\|viewscreen` |
| `encounters.new_encounter` | `/encounters/new` |
| `encounters.edit_encounter` | `/encounters/{encounter_id}/edit` |
| `static` files | `/static/...` |

---

## Task 1: Configure Jinja2Templates in app.py

**Files:**
- Modify: `sta/web/app.py`

**Step 1: Add Jinja2Templates configuration**

```python
# Add near top of app.py
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="sta/web/templates")

# In create_app(), store templates on app.state
app.state.templates = templates
```

**Step 2: Mount static files**

```python
from fastapi.staticfiles import StaticFiles

# In create_app(), after router registrations:
app.mount("/static", StaticFiles(directory="sta/web/static"), name="static")
```

---

## Task 2: Replace url_for() in base.html

**Files:**
- Modify: `sta/web/templates/base.html:398-400` (sidebar nav)
- Modify: `sta/web/templates/base.html:451-453` (mobile nav)
- Modify: `sta/web/templates/base.html:429-435` (flash messages - remove Flask-specific)

**Step 1: Replace sidebar nav url_for() calls**

Replace:
```html
<a href="{{ url_for('main.index') }}" class="lcars-sidebar-btn color-1">Home</a>
<a href="{{ url_for('campaigns.player_home') }}" class="lcars-sidebar-btn color-2">Player</a>
<a href="{{ url_for('campaigns.gm_home') }}" class="lcars-sidebar-btn color-3">Game Master</a>
```

With:
```html
<a href="/" class="lcars-sidebar-btn color-1">Home</a>
<a href="/player/home" class="lcars-sidebar-btn color-2">Player</a>
<a href="/gm" class="lcars-sidebar-btn color-3">Game Master</a>
```

**Step 2: Replace mobile nav url_for() calls** (lines 451-453)

Replace:
```html
<a href="{{ url_for('main.index') }}">Home</a>
<a href="{{ url_for('campaigns.player_home') }}">Player</a>
<a href="{{ url_for('campaigns.gm_home') }}">GM</a>
```

With:
```html
<a href="/">Home</a>
<a href="/player/home">Player</a>
<a href="/gm">GM</a>
```

**Step 3: Remove Flask flash messages** (lines 429-435)

Replace:
```html
{% with messages = get_flashed_messages() %}
    {% if messages %}
        {% for message in messages %}
            <div class="lcars-alert alert-info">{{ message }}</div>
        {% endfor %}
    {% endif %}
{% endwith %}
```

With:
```html
{% if flash_message %}
    <div class="lcars-alert alert-info">{{ flash_message }}</div>
{% endif %}
```

---

## Task 3: Replace url_for() in index.html

**Files:**
- Modify: `sta/web/templates/index.html:44,58`

Replace:
```html
<a href="{{ url_for('campaigns.player_home') }}" class="role-card role-player">
```
With:
```html
<a href="/player/home" class="role-card role-player">
```

Replace:
```html
<a href="{{ url_for('campaigns.gm_home') }}" class="role-card role-gm">
```
With:
```html
<a href="/gm" class="role-card role-gm">
```

---

## Task 4: Replace url_for() in gm_home.html

**Files:**
- Modify: `sta/web/templates/gm_home.html:8,21,54,98`

Replace lines 8, 54, 98:
```html
{{ url_for('campaigns.gm_home') }} → /gm
{{ url_for('main.index') }} → /
{{ url_for('campaigns.new_campaign') }} → /campaigns/new
```

Replace line 21:
```html
{{ url_for('campaigns.campaign_dashboard', campaign_id=campaign.campaign_id, role='gm') }}
```
With:
```html
/campaigns/{{ campaign.campaign_id }}
```

---

## Task 5: Replace url_for() in player_home.html

**Files:**
- Modify: `sta/web/templates/player_home.html:8,21,63,79`

Replace:
```html
{{ url_for('main.index') }} → /
{{ url_for('campaigns.player_dashboard', campaign_id=campaign.campaign_id) }} → /campaigns/{{ campaign.campaign_id }}/player
{{ url_for('campaigns.join_campaign', campaign_id=campaign.campaign_id) }} → /campaigns/{{ campaign.campaign_id }}/join
```

---

## Task 6: Replace url_for() in gm_login.html

**Files:**
- Modify: `sta/web/templates/gm_login.html:8,32,40`

Replace:
```html
{{ url_for('campaigns.campaign_list') }} → /campaigns
{{ url_for('campaigns.gm_login', campaign_id=campaign.campaign_id) }} → /gm/{{ campaign.campaign_id }}/login
{{ url_for('campaigns.join_campaign', campaign_id=campaign.campaign_id) }} → /campaigns/{{ campaign.campaign_id }}/join
```

---

## Task 7: Replace url_for() in campaign_new.html

**Files:**
- Modify: `sta/web/templates/campaign_new.html:8,20,45`

Replace:
```html
{{ url_for('campaigns.gm_home') }} → /gm
{{ url_for('campaigns.new_campaign') }} → /campaigns/new
```

---

## Task 8: Replace url_for() in campaign_list.html

**Files:**
- Modify: `sta/web/templates/campaign_list.html:22,61,71,74`

Replace:
```html
{{ url_for('campaigns.campaign_dashboard', campaign_id=campaign.campaign_id) }} → /campaigns/{{ campaign.campaign_id }}
{{ url_for('campaigns.new_campaign') }} → /campaigns/new
{{ url_for('encounters.new_encounter') }} → /encounters/new
{{ url_for('main.index') }} → /
```

---

## Task 9: Replace url_for() in campaign_join.html

**Files:**
- Modify: `sta/web/templates/campaign_join.html:8,24,40`

Replace:
```html
{{ url_for('campaigns.player_home') }} → /player/home
{{ url_for('campaigns.join_campaign', campaign_id=campaign.campaign_id) }} → /campaigns/{{ campaign.campaign_id }}/join
```

---

## Task 10: Replace url_for() in campaign_dashboard.html

**Files:**
- Modify: `sta/web/templates/campaign_dashboard.html:28,78,82,96,126,130,147,522`

Replace all `url_for('campaigns.campaign_dashboard', campaign_id=...)` → `/campaigns/{{ campaign.campaign_id }}`
Replace `url_for('encounters.combat', encounter_id=..., role=...)` → `/encounters/{{ encounter_id }}?role=...`
Replace `url_for('scenes.view_scene', scene_id=..., role=...)` → `/scenes/{{ scene_id }}?role=...`

---

## Task 11: Replace url_for() in player_dashboard.html

**Files:**
- Modify: `sta/web/templates/player_dashboard.html:15,150,193`

Replace:
```html
{{ url_for('campaigns.switch_character', campaign_id=...) }} → /campaigns/{{ campaign.campaign_id }}/switch-character
{{ url_for('encounters.combat', encounter_id=..., role='player') }} → /encounters/{{ encounter_id }}?role=player
{{ url_for('campaigns.player_home') }} → /player/home
```

---

## Task 12: Replace url_for() in scene and combat templates

**Files:**
- `sta/web/templates/scene_player.html:67`
- `sta/web/templates/scene_gm.html:114,117,132`
- `sta/web/templates/edit_scene.html:17,268,271`
- `sta/web/templates/new_scene.html:14,233`
- `sta/web/templates/combat_player.html:11,907`
- `sta/web/templates/combat_player_new.html:994`
- `sta/web/templates/combat_gm.html:915,917`
- `sta/web/templates/combat_viewscreen.html:7,8,1003,1004`
- `sta/web/templates/new_encounter.html:14,207`
- `sta/web/templates/edit_encounter.html:17,199`
- `sta/web/templates/personnel_combat.html:374`

For each, replace:
- `{{ url_for('campaigns.campaign_dashboard', campaign_id=...) }}` → `/campaigns/{{ campaign.campaign_id }}`
- `{{ url_for('scenes.view_scene', scene_id=..., role=...) }}` → `/scenes/{{ scene_id }}?role=...`
- `{{ url_for('scenes.edit_scene', scene_id=...) }}` → `/scenes/{{ scene_id }}/edit`
- `{{ url_for('encounters.combat', encounter_id=..., role=...) }}` → `/encounters/{{ encounter_id }}?role=...`
- `{{ url_for('main.index') }}` → `/`
- `{{ url_for('static', filename='...') }}` → `/static/...`

---

## Task 13: Create ui_router.py with all page routes

**Files:**
- Create: `sta/web/routes/ui_router.py`

Create a new router file with these routes:

### Landing Page
```python
@ui_router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

### Player Routes
```python
@ui_router.get("/player/home", response_class=HTMLResponse)
async def player_home(request: Request, ...):
    # Render player_home.html with campaigns list
```

### GM Routes
```python
@ui_router.get("/gm", response_class=HTMLResponse)
async def gm_home(request: Request, ...):
    # Render gm_home.html with GM's campaigns

@ui_router.get("/gm/{campaign_id}/login", response_class=HTMLResponse)
async def gm_login_page(request: Request, campaign_id: str, ...):
    # Render gm_login.html

@ui_router.post("/gm/{campaign_id}/login")
async def gm_login_submit(...):
    # Handle password form submission
```

### Campaign Routes
```python
@ui_router.get("/campaigns", response_class=HTMLResponse)
async def campaign_list(request: Request, ...):
    # Render campaign_list.html

@ui_router.get("/campaigns/new", response_class=HTMLResponse)
async def new_campaign_page(...):
    # Render campaign_new.html

@ui_router.post("/campaigns/new")
async def create_campaign(...):
    # Handle campaign creation form

@ui_router.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
async def campaign_dashboard(...):
    # Render campaign_dashboard.html with full context (players, scenes, encounters)

@ui_router.get("/campaigns/{campaign_id}/join", response_class=HTMLResponse)
async def join_campaign_page(...):
    # Render campaign_join.html

@ui_router.post("/campaigns/{campaign_id}/join")
async def join_campaign_submit(...):
    # Handle character claiming

@ui_router.get("/campaigns/{campaign_id}/player", response_class=HTMLResponse)
async def player_dashboard(...):
    # Render player_dashboard.html

@ui_router.get("/campaigns/{campaign_id}/switch-character", response_class=HTMLResponse)
async def switch_character(...):
    # Render switch character page
```

### Scene Routes
```python
@ui_router.get("/scenes/new", response_class=HTMLResponse)
async def new_scene_page(...):
    # Render new_scene.html

@ui_router.post("/scenes/new")
async def create_scene(...):
    # Handle scene creation

@ui_router.get("/scenes/{scene_id}", response_class=HTMLResponse)
async def view_scene(...):
    # Render scene_gm.html, scene_player.html, or scene_viewscreen.html based on role param

@ui_router.get("/scenes/{scene_id}/edit", response_class=HTMLResponse)
async def edit_scene_page(...):
    # Render edit_scene.html
```

### Encounter Routes
```python
@ui_router.get("/encounters/new", response_class=HTMLResponse)
async def new_encounter_page(...):
    # Render new_encounter.html

@ui_router.get("/encounters/{encounter_id}", response_class=HTMLResponse)
async def combat_view(...):
    # Render combat_gm.html, combat_player.html, or combat_viewscreen.html based on role param

@ui_router.get("/encounters/{encounter_id}/edit", response_class=HTMLResponse)
async def edit_encounter_page(...):
    # Render edit_encounter.html
```

---

## Task 14: Wire ui_router into app.py

**Files:**
- Modify: `sta/web/app.py`

Add to router imports and registration:
```python
from sta.web.routes.ui_router import ui_router

app.include_router(ui_router)
```

---

## Task 15: Add /api/server-info endpoint

**Files:**
- Modify: `sta/web/routes/api_router.py` or create inline in `ui_router.py`

The `index.html` template fetches `/api/server-info` to get the server URL. Add this to `ui_router.py`:

```python
@ui_router.get("/api/server-info")
async def get_server_info(request: Request):
    return {
        "url": str(request.base_url).rstrip("/"),
        "version": "1.0.0",
    }
```

---

## Task 16: Verify the app loads

**Step 1: Start the app**

```bash
cd /home/mer0/repositories/staStarShipSimulator
uv run uvicorn sta.web.app:app --host 0.0.0.0 --port 5001 --reload
```

**Step 2: Browse to http://localhost:5001/**

Expected: Landing page with Player/GM role selection cards

**Step 3: Click "Player" → should go to /player/home**

**Step 4: Click "Game Master" → should go to /gm**

---

## Notes

- Templates use `{{ url_for('campaigns.join_campaign', campaign_id=campaign.campaign_id) }}` which in Flask generates `/campaigns/{campaign_id}/join`. In FastAPI we replace with `/campaigns/{{ campaign.campaign_id }}/join`.
- The `campaign_dashboard.html` template references `is_gm`, `players`, `ships`, `draft_scenes`, `active_scene_data`, `active_encounter`, `draft_encounters`, `completed_encounters`, `completed_scenes` - the route must provide all these context variables.
- `base.html` uses `{% with messages = get_flashed_messages() %}` which is Flask-only. Replace with a `flash_message` template variable.
- Templates use Flask's `url_for('static', filename='css/lcars.css')` → replace with `/static/css/lcars.css`.
- The `index.html` uses inline `<script>` to fetch `/api/server-info` - this endpoint must exist.
