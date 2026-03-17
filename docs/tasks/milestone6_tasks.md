# Milestone 6: UI/UX Overhaul - Task List

## Overview
Complete UI/UX redesign for mobile-responsive VTT experience. This milestone focuses on improving the frontend experience while maintaining all existing functionality.

## Branch Information
- **Branch**: `feature/m6-ui-ux-overhaul`
- **Base**: `vtt-scope` (after M5 merge)
- **Model**: `opencode/minimax-m2.5-free`

---

## Technical Foundations (Decisions)
1. **Template-First Approach**: Improve existing Jinja2 templates before considering JS frameworks
2. **Mobile-First**: Design for mobile/tablet first, then enhance for desktop
3. **CSS Variables**: Use design tokens for consistent theming
4. **Progressive Enhancement**: Ensure core functionality works without JS
5. **FastAPI Integration**: Leverage existing FastAPI endpoints (M5 work)

---

## Task 6.1: Campaign Dashboard Redesign

**Agent**: python-dev
**Skills**: responsive-design, python-code-quality
**Priority**: P0
**Status**: TODO

### Objectives
Redesign campaign selection interface and campaign overview dashboard.

### Implementation Steps
1. Update `campaign_list.html`:
   - Mobile-friendly campaign cards
   - Quick stats preview (players, scenes, active encounters)
   - Search/filter functionality
2. Update `campaign_dashboard.html`:
   - Responsive grid layout
   - Quick action buttons
   - Campaign statistics display
3. Add GM/player view toggles
4. Improve navigation between sections

### Files to Modify
- `sta/web/templates/campaign_list.html`
- `sta/web/templates/campaign_dashboard.html`
- `sta/web/static/css/` (create if needed)

### Verification
- `pytest tests/test_scene*.py tests/test_campaign*.py` - all pass
- Mobile viewport test: campaign_list renders at 320px width
- Search input exists and has placeholder text

---

## Task 6.2: Scene Management UI

**Agent**: python-dev
**Skills**: responsive-design, python-code-quality
**Priority**: P0
**Status**: TODO

### Objectives
Improve scene creation, navigation, and transition interfaces.

### Implementation Steps
1. Update `new_scene.html`:
   - Better scene type selection (visual cards)
   - Form validation feedback
   - Mobile-friendly input controls
2. Update `edit_scene.html`:
   - Participant management UI
   - Ship assignment interface
   - Scene traits/challenges editor
3. Update `scene_gm.html`:
   - GM controls for scene activation
   - Scene transition dialogue
   - Participant visibility controls
4. Add scene type icons and visual indicators

### Files to Modify
- `sta/web/templates/new_scene.html`
- `sta/web/templates/edit_scene.html`
- `sta/web/templates/scene_gm.html`
- `sta/web/templates/scene_player.html`

### Verification
- `pytest tests/test_scene*.py` - all pass
- new_scene.html has scene_type selection with visible labels
- edit_scene.html has form inputs with labels

---

## Task 6.3: Character/Ship Builder UI

**Agent**: python-dev
**Skills**: responsive-design, python-code-quality
**Priority**: P1
**Status**: TODO

### Objectives
Create intuitive interfaces for character and ship creation/management.

### Implementation Steps
1. Character creation interface:
   - Step-by-step wizard or tabbed interface
   - Visual attribute/discipline inputs
   - Species/role selection with previews
   - Talent assignment interface
2. Ship configuration UI:
   - Ship class selection
   - System/department configuration
   - Weapon assignment
   - Visual ship stats display
3. Library browser:
   - Search and filter
   - Template selection
   - Duplicate detection UI

### Files to Modify
- Character templates (check `sta/web/templates/characters*.html`)
- Ship templates (check `sta/web/templates/ships*.html`)
- May need to create new templates

### Verification
- Character CRUD tests pass: `pytest tests/test_characters_api.py -v`
- Ship CRUD tests pass: `pytest tests/test_ships_api.py -v`
- All character/ship form inputs have `<label>` tags

---

## Task 6.4: Mobile Responsiveness

**Agent**: python-dev
**Skills**: responsive-design
**Priority**: P1
**Status**: TODO

### Objectives
Ensure all pages work on mobile and tablet devices.

### Implementation Steps
1. Add responsive CSS:
   - Mobile-first breakpoints
   - Touch-friendly button sizes (min 44px)
   - Scrollable content areas
   - Collapsible sections
2. Test all major pages:
   - Campaign list/dashboard
   - Scene views (GM, player, viewscreen)
   - Combat interface
   - Character/ship forms
3. Fix navigation:
   - Hamburger menu for mobile
   - Bottom navigation for mobile
   - Responsive tables

### Files to Modify
- `sta/web/templates/base.html` (add responsive CSS)
- All page templates

### Verification
- base.html has `@media` queries for responsive breakpoints
- Buttons have min-height: 44px in CSS
- Form inputs have proper labels

---

## Task 6.5: Combat UI Improvements

**Agent**: python-dev
**Skills**: responsive-design, async-python-patterns
**Priority**: P2
**Status**: TODO

### Objectives
Enhance combat interface with better UX.

### Implementation Steps
1. Update `combat_gm.html`:
   - Better action buttons
   - Turn order visualization
   - Quick threat/momentum controls
2. Update `combat_player.html`:
   - Streamlined action selection
   - Clear turn indicator
   - Dice roll interface
3. Improve `hex-map.js`:
   - Touch-friendly map controls
   - Better positioning UI
4. Add SSE support for real-time updates (if not done in M5)

### Files to Modify
- `sta/web/templates/combat_gm.html`
- `sta/web/templates/combat_player.html`
- `sta/web/static/js/hex-map.js`

### Verification
- `pytest tests/test_combat*.py` - all pass
- Combat forms have labels for all inputs

---

## Task 6.6: Design System Foundation

**Agent**: python-dev
**Skills**: design-system-patterns
**Priority**: P3
**Status**: TODO

### Objectives
Establish design tokens and consistent styling.

### Implementation Steps
1. Create CSS custom properties:
   - Colors (primary, secondary, success, danger, etc.)
   - Typography (font sizes, weights)
   - Spacing (margins, paddings)
   - Border radius
2. Standardize components:
   - Buttons (primary, secondary, danger)
   - Cards
   - Forms
   - Modals
3. Add to `base.html`:
   - CSS variables
   - Base component classes

### Files to Modify
- `sta/web/templates/base.html`
- Create `sta/web/static/css/variables.css`

### Verification
- base.html or variables.css contains `:root {` with CSS custom properties
- At least 3 color variables defined (e.g., --primary-color, --secondary-color)
- At least 2 spacing variables defined

---

## Parallel Execution Strategy

These tasks can be executed in parallel with independent agents:

| Task | Dependencies | Can Run In Parallel With |
|------|--------------|--------------------------|
| 6.1 Campaign Dashboard | None | 6.2, 6.3, 6.4 |
| 6.2 Scene Management | None | 6.1, 6.3, 6.4 |
| 6.3 Character/Ship UI | None | 6.1, 6.2, 6.4 |
| 6.4 Mobile Responsive | None | 6.1, 6.2, 6.3 |
| 6.5 Combat UI | None | 6.4 |
| 6.6 Design System | None | Any |

**Recommended Agent Allocation**:
- **Agent 1**: Task 6.1 + 6.2 (Campaign + Scene)
- **Agent 2**: Task 6.3 + 6.4 (Builders + Mobile)
- **Agent 3**: Task 6.5 + 6.6 (Combat + Design)

---

## Agent Prompts

### Prompt for Agent 1: Campaign & Scene UI

```markdown
## Task: Implement Campaign Dashboard & Scene Management UI (Tasks 6.1, 6.2)

### Context
You are working on the vtt-scope branch. M5 is complete (FastAPI migration, scene lifecycle). Now we need to improve the UI/UX.

### Branch
Create a new branch from vtt-scope: `feature/m6-campaign-scene-ui`

### Objectives
1. **Task 6.1**: Redesign campaign dashboard
   - Improve campaign_list.html for mobile
   - Enhance campaign_dashboard.html with better layout
   
2. **Task 6.2**: Improve scene management UI  
   - Enhance new_scene.html with visual scene type selection
   - Improve edit_scene.html participant management
   - Update scene_gm.html with better controls

### Implementation Guidelines
- Use responsive CSS (flexbox/grid)
- Keep existing functionality
- Match existing code style
- Use uv for dependency management

### Files to Focus On
- sta/web/templates/campaign_list.html
- sta/web/templates/campaign_dashboard.html
- sta/web/templates/new_scene.html
- sta/web/templates/edit_scene.html
- sta/web/templates/scene_gm.html

### Verification
Run tests: `uv run pytest tests/test_scene.py tests/test_campaign*.py -v`

### Model
Use `opencode/minimax-m2.5-free`
```

### Prompt for Agent 2: Character/Ship & Mobile UI

```markdown
## Task: Implement Character/Ship Builders & Mobile Responsiveness (Tasks 6.3, 6.4)

### Context
You are working on the vtt-scope branch. M5 is complete. Focus on UI improvements.

### Branch
Create a new branch from vtt-scope: `feature/m6-builders-mobile`

### Objectives
1. **Task 6.3**: Character/Ship Builder UI
   - Find existing character/ship templates
   - Improve form layouts
   - Add visual feedback for inputs
   
2. **Task 6.4**: Mobile Responsiveness
   - Add responsive CSS to base.html
   - Test all pages on mobile viewport
   - Fix navigation for mobile

### Implementation Guidelines
- Add responsive breakpoints (min 768px for tablet, 1024px for desktop)
- Make touch targets minimum 44px
- Use CSS flexbox/grid for layouts

### Files to Focus On
- sta/web/templates/base.html (add responsive CSS)
- sta/web/templates/characters*.html
- sta/web/templates/ships*.html (if exist)
- All form templates

### Verification
Run tests: `uv run pytest tests/test_characters_api.py tests/test_ships_api.py -v`

### Model
Use `opencode/minimax-m2.5-free`
```

### Prompt for Agent 3: Combat UI & Design System

```markdown
## Task: Combat UI Improvements & Design System (Tasks 6.5, 6.6)

### Context
You are working on the vtt-scope branch. M5 is complete.

### Branch
Create a new branch from vtt-scope: `feature/m6-combat-design`

### Objectives
1. **Task 6.5**: Combat UI Improvements
   - Enhance combat_gm.html with better controls
   - Improve combat_player.html action interface
   - Review hex-map.js for touch support
   
2. **Task 6.6**: Design System Foundation
   - Add CSS custom properties to base.html
   - Define color palette, typography, spacing
   - Create button/component classes

### Implementation Guidelines
- Keep existing functionality
- Don't break existing tests

### Files to Focus On
- sta/web/templates/combat_gm.html
- sta/web/templates/combat_player.html
- sta/web/static/js/hex-map.js
- sta/web/templates/base.html

### Verification
Run tests: `uv run pytest tests/test_combat*.py -v`

### Model
Use `opencode/minimax-m2.5-free`
```

---

## Timeline Estimate
- Task 6.1: 4 hrs
- Task 6.2: 4 hrs
- Task 6.3: 4 hrs
- Task 6.4: 3 hrs
- Task 6.5: 3 hrs
- Task 6.6: 2 hrs
- Total: ~20 hours (can be parallelized)

---

## Current Agent Status (2026-03-17)

### Status: TODO - Ready for Agent Deployment

M6 is ready to begin. Three python-dev agents can be deployed in parallel:
- Agent 1: Campaign + Scene UI (Tasks 6.1, 6.2)
- Agent 2: Builders + Mobile (Tasks 6.3, 6.4)
- Agent 3: Combat + Design (Tasks 6.5, 6.6)

### Dependencies
- Requires: vtt-scope branch (M5 complete)
- Enables: M7 (Import/Export)

---

## Milestone 7: Import/Export (Planned)

Following M6, M7 will focus on import/export functionality:

### Task 7.1: VTT Character Export/Import
- Export characters to JSON
- Import characters from JSON
- Handle updates to existing characters

### Task 7.2: VTT Ship Export/Import  
- Export ships to JSON
- Import ships from JSON

### Task 7.3: Full Campaign Backup
- Export entire campaign
- Import full backup
- Validate backup structure

Reference: `docs/tasks/milestone7_tasks.md`

---

## Acceptance Criteria
- [ ] Campaign dashboard renders without errors on mobile (320px width)
- [ ] campaign_list.html has working search/filter input
- [ ] campaign_dashboard.html displays campaign stats (players, scenes count)
- [ ] new_scene.html has visual scene type selection (cards or radio buttons with labels)
- [ ] edit_scene.html has participant management section
- [ ] scene_gm.html has activation controls visible
- [ ] All existing scene tests pass: `pytest tests/test_scene*.py`
- [ ] All existing campaign tests pass: `pytest tests/test_campaign*.py`
- [ ] Character forms have labels for all inputs
- [ ] Ship forms have labels for all inputs  
- [ ] base.html has responsive CSS with @media breakpoints
- [ ] Touch targets (buttons, links) are minimum 44px height
- [ ] All existing character/ship tests pass: `pytest tests/test_characters_api.py tests/test_ships_api.py`
- [ ] Combat forms have proper labels
- [ ] All existing combat tests pass: `pytest tests/test_combat*.py`
- [ ] CSS variables defined in base.html for: primary-color, secondary-color, font-family, spacing-unit
- [ ] Test suite: 0 failed tests (allow skipped)

---

## Next Steps

1. **Deploy agents** in parallel for M6 tasks
2. **Track progress** in this document
3. **Verify tests** after each task
4. **Merge** to vtt-scope when complete
5. **Begin M7** (Import/Export)
