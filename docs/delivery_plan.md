# VTT Transition Delivery Plan
## Executive Summary
This document outlines the comprehensive plan for transitioning the Star Trek Adventures Starship Simulator from a dedicated combat encounter tool to a minimal Virtual Tabletop (VTT) experience. The plan covers all milestones with detailed task breakdowns, parallel work assignments, testing strategies, and acceptance criteria.
**Status**: M1-M10 **COMPLETE**. M11 **IN PROGRESS** - Logging & Observability.

## Milestone 10: Page Structure Rework & UX Enhancements
### Status: ✅ Complete — PR #24 merged

## Milestone 11: Logging & Observability (Planned)
### Overview
Add comprehensive logging infrastructure to trace user-observed behavior during testing and production debugging.

### Design Decisions (Planned)
- **Centralized Logger**: Create `sta/logging.py` with structured logging config
- **Request Middleware**: Auto-log all HTTP requests with timing
- **Game Action Loggers**: Track dice rolls, value interactions, combat actions
- **GM Action Loggers**: Track threat spends, scene changes, NPC spawns
- **Error Logging**: Capture exceptions with full context

### Status: 📋 PLANNED
### Tasks
| Task | Description |
|---|---|
| M11.1 | Create centralized logging module (`sta/logging.py`) |
| M11.2 | Add request/response middleware to FastAPI app |
| M11.3 | Implement game action loggers (dice, values, combat) |
| M11.4 | Add GM action logging (threat, scenes, NPCs) |
| M11.5 | Configure log levels for dev vs production |
| M11.6 | Tests and verification |

**Branch:** `feature/m11-logging` from `main`
**Tasks doc:** `docs/tasks/milestone11_tasks.md`

## Acceptance Criteria
- ✅ All M10 tasks complete
## Milestone 8.2: Rules Understanding &amp; Documentation Sync
### Overview
Analyze core rulebook chapters (Ch 4, 5, 6, 7, 8, 9, 11) against VTT mechanics reference. Agent reports are synthesized into the **Acceptance Criteria** section below and the new file `docs/m8.2-open-questions.md`.
### Status: 📊 IN PROGRESS (Implementation Complete, Cleanup in Progress)
### Findings Synthesis
- **Key Conflict**: The generic Stress mechanic from Ch 8/11 conflicts with NPC rules (Ch 11) and is missing from the core mechanics reference (`game_mechanics_full.md`).

- **Key Extension**: Threat Spends (Ch 9) must be added to `game_mechanics_full.md` for Starship Combat.

### Implementation Completed
- [X] `ThreatManager` class (`sta/mechanics/threat_manager.py`) - 9 unit tests
- [X] `MomentumManager` class (`sta/mechanics/momentum_manager.py`) - 11 unit tests
- [X] Game mechanics documentation extended (`docs/references/game_mechanics.md`)
- [X] Campaign Resource Pools section documenting Momentum/Threat per Ch 4/9

### Cleanup Log (2026-03-18)
The following files were removed but can be restored from git history if needed:
- `CLAUDE.md`, `build_mac.sh`, `star_mac_logo.png`, `dev.sh` - Legacy/project files
- `requirements.txt` / `requirements-dev.txt` - pyproject.toml handles deps
- `SKILLS_SIMPLIFICATION_REPORT.md` - Report file
- `migrate*.py` / `scripts/migrate*.py` - One-off migration scripts (5 files)

To restore: `git checkout  -- `
## Milestone 9: Web UI &amp; Theme Support (Future)
## Table of Contents

- [Project Overview](#project-overview)
- [Model Configuration](#model-configuration)
- [Git Workflow](#git-workflow)
- [Milestone 1: Database Schema Migration](#milestone-1-database-schema-migration)
- [Milestone 2: Campaign Management](#milestone-2-campaign-management)
- [Milestone 3: Scene Management](#milestone-3-scene-management)
- [Milestone 4: Character/Ship CRUD](#milestone-4-charactership-crud)
- [Milestone 5: Combat Integration](#milestone-5-combat-integration)
- [Milestone 6: UI/UX Overhaul](#milestone-6-uiux-overhaul)
- [Milestone 7: Import/Export &amp; Final Integration](#milestone-7-importexport--final-integration)
- [Milestone 8.2: Rules Understanding](#milestone-82-rules-understanding)
- [Parallel Work Strategy](#parallel-work-strategy)
- [Testing Strategy](#testing-strategy)
- [Code Review Process](#code-review-process)
- [Acceptance Criteria](#acceptance-criteria)
- [Risk Management](#risk-management)

## Project Overview

### Current State
- ✅ Working combat encounter system (legacy)
- ✅ VTT data models defined (Pydantic schemas)
- ✅ Partial campaign/scene implementation
- ✅ SQLAlchemy database with legacy schema
- ✅ Declarative action system (10-line configs)

### Target State
- ✅ Full VTT experience with campaigns, scenes, characters
- ✅ Integrated combat system
- ✅ Mobile-responsive UI
- ✅ Real-time synchronization
- ✅ GM and player workflows

### Key Constraints
- **Model Budget**: Use free models (MiniMax M2.5 Free, Big Pickle) for development
- **Code Quality**: All changes must pass code auditor review
- **Testing**: Comprehensive test coverage required
- **Legacy**: Clean break from legacy system (no data migration needed)

## Model Configuration

### Development Models
`json { "model": "opencode/minimax-m2.5-free", "provider": { "opencode": {} } } `

### Code Review Models
`json { "model": "opencode/claude-sonnet-4-5", "provider": { "opencode": {} } } `

**Agent Configuration**:
- **python-dev agents**: Use `opencode/minimax-m2.5-free` (free tier)
- **code-reviewer agents**: Use `opencode/claude-sonnet-4-5` (high quality)
- **All agents**: Use `modern-python` skill for best practices

## Git Workflow

### Branch Structure
`main (protected) ├── develop (integration branch) │ ├── feature/m1-database-schema │ ├── feature/m2-campaign-mgmt │ ├── feature/m3-scene-mgmt │ ├── feature/m4-char-ship-crud │ ├── feature/m5-combat-integration │ └── feature/m6-ui-ux-overhaul`

### Workflow Rules
1. **Never commit directly to **`main`
2. **Feature branches** created from `main`
3. **Git worktrees** for isolation (managed by agents)
4. **PR to **`develop` for integration testing
5. **PR to **`main` after milestone validation
6. **Code auditor review** before user review
7. **User approval** required for all merges

### Worktree Management
`bash # Create worktree for feature git worktree add ../feature-m1-database develop # Work in isolated directory cd ../feature-m1-database # Create feature branch git checkout -b feature/m1-database-schema # Work, commit, push # ... # Cleanup when done git worktree remove ../feature-m1-database `

## Milestone 1: Database Schema Migration

### Overview
Create new VTT database schema alongside legacy tables, prepare for clean migration.

### Status: ✅ COMPLETE (2026-03-06)

### Tasks

#### Task 1.1: Create VTT Database Schema
**Agent**: python-dev
**Skills**: modern-python, databases
**Model**: `opencode/minimax-m2.5-free`

- [x] Create SQLAlchemy models for VTT entities:
- `VTTCharacterRecord` (VTT version)
- `VTTShipRecord` (VTT version)
- `UniverseLibraryRecord`
- `TraitRecord`, `TalentRecord`, `WeaponRecord`
- [x] Create migration in `sta/database/migrations/versions/`
- [x] Add indexes for performance

**Files**: `sta/database/vtt_schema.py`, `sta/database/migrations/versions/001_create_vtt_tables.py`

#### Task 1.2: Implement VTT Model ORM
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [x] Create `to_model()` and `from_model()` methods
- [x] Add validation for VTT-specific constraints
- [x] Test fixtures verified working

**Files**: `sta/database/vtt_schema.py`

#### Task 1.3: Legacy Inventory &amp; Documentation
**Agent**: code-reviewer
**Skills**: documentation, analysis
**Model**: `opencode/claude-sonnet-4-5`

- [x] Complete `docs/legacy_index.md`
- [x] Document all legacy components

**Files**: `docs/legacy_index.md`

### Verification Results
- ✅ 6 VTT tables exist in database
- ✅ ORM conversion methods tested (Character and Ship)
- ✅ 203 tests passing
- ✅ Documentation complete

### Timeline: COMPLETE

### Testing Strategy
- **Unit Tests**: Model validation, serialization
- **Integration Tests**: Database operations, transactions
- **Regression Tests**: Ensure legacy still works
- **Migration Tests**: Data conversion scripts

### Acceptance Criteria
- ✅ New VTT tables created in database
- ✅ All models pass validation tests
- ✅ Legacy system still functional
- ✅ Migration scripts tested
- ✅ Documentation complete

### Timeline: 3-5 days

## Milestone 2: Campaign Management

### Overview
Full campaign lifecycle management with GM controls and player access.

### Status: ✅ COMPLETE (2026-03-06)

### Detailed Tasks
See `docs/tasks/milestone2_tasks.md` for specific implementation steps.

### Current State (as of M2 completion)
- Campaign resource pools (Momentum/Threat) exist
- Universe Library API functional
- VTT character/ship integration with campaigns
- Session token system with expiration

---

#### Task 2.1: Campaign CRUD API
**Agent**: python-dev
**Skills**: modern-python, fastapi-pro
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement `/api/campaigns/*` endpoints:
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign
- `PUT /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign
- `GET /api/campaigns` - List campaigns
- [ ] Add GM authentication middleware
- [ ] Implement resource pool management (Momentum/Threat)

**Files**: `sta/web/routes/campaigns.py`, `sta/web/routes/api.py`

#### Task 2.2: Universe Library
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement `/api/universe/*` endpoints:
- Character library management
- Ship library management
- Item/equipment library
- Document templates
- [ ] Add category filtering (PCs, NPCs, Creatures, Ships)
- [ ] Implement GM-only access controls

**Files**: `sta/web/routes/universe.py` (new)

#### Task 2.3: Player Management
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement `/api/campaigns/{id}/players` endpoints
- [ ] Add character assignment workflow
- [ ] Implement session token system
- [ ] Add position assignment (Captain, Helm, etc.)

**Files**: `sta/web/routes/campaigns.py`

### Testing Strategy
- **Unit Tests**: API endpoint validation
- **Integration Tests**: Campaign lifecycle workflows
- **Security Tests**: Authentication and authorization
- **Concurrency Tests**: Multiple players joining

### Acceptance Criteria
- ✅ Campaign CRUD fully functional
- ✅ Universe library with categories
- ✅ Player management with character assignment
- ✅ GM authentication working
- ✅ All tests passing

### Status: ✅ COMPLETE

### Detailed Tasks
See `docs/tasks/milestone2_tasks.md` for implementation details and test results.

### Completed Features
- Campaign resource pools (Momentum/Threat)
- Universe Library API (characters/ships with categories)
- VTT character/ship integration (linking tables, endpoints)
- Session token enhancement (expiration, refresh)

All 257 tests passing (including 54 new M2 tests).

---

## Milestone 3: Scene Management

### Overview
Complete scene lifecycle with narrative and combat support.

### Status: ✅ COMPLETE

### Testing Strategy
See `docs/tasks/milestone3_tasks.md` for complete task breakdown.

---

## Milestone 5: VTT Scene Lifecycle &amp; Combat Integration

### Overview
Complete migration from Flask to FastAPI and implement new 4-state scene lifecycle with multi-scene support.

### Status: ✅ COMPLETE (2026-03-17)

### Scene Lifecycle (NEW - 2026-03-15)

The VTT now supports a 4-state scene lifecycle:

| State | Description | Visibility |
|-------|-------------|------------|
| **draft** | No title or player character list | GM only, never visible to players |
| **ready** | Has title + GM-short-description | Available in scene-transition dialogue |
| **active** | Currently in progress | All participants, can have multiple |
| **completed** | Archived | Can be re-activated or copied |

#### State Transitions

`draft ──(GM adds title+PCs)──► ready ──(GM activates)──► active ──(GM ends)──► completed ▲ │ │ ▼ └────(re-activate)─────┘ └────(copy)──────────► ready (new) 328:`

#### Scene Transition Dialogue

When completing a scene, GM sees:
1. **Connected scenes** (first) - scenes linked to current
2. **Ready scenes** (dropdown last) - available to activate
3. **Create new scene** - on-the-fly creation

#### Split-Party Support (NEW)

- Multiple scenes can be **active** simultaneously
- GM can **switch focus** between parallel active scenes
- **All party members visible** even when not in active scene

#### Connection Termination

- Completing a scene **terminates its connections**
- Connected scenes must be re-linked after re-activation

### Tasks

#### Task 5.1: FastAPI App Factory
**Agent**: python-dev
**Model**: `opencode/minimax-m2.5-free`

- [x] Create FastAPI application factory in `sta/web/app.py`
- [x] Implement router registration for all endpoints
- [x] Add async database session handling
- [x] Configure CORS and middleware

**Files**: `sta/web/app.py`

#### Task 5.2: Route Migration
**Agent**: python-dev
**Model**: `opencode/minimax-m2.5-free`

- [x] Migrate campaigns_router.py to FastAPI
- [x] Migrate universe_router.py to FastAPI
- [x] Migrate api_router.py to FastAPI
- [x] Migrate scenes_router.py to FastAPI
- [x] Migrate characters_router.py to FastAPI
- [x] Migrate ships_router.py to FastAPI
- [x] Migrate encounters_router.py to FastAPI

**Files**: `sta/web/routes/*.py`

#### Task 5.3: Test Infrastructure Update
**Agent**: python-dev
**Model**: `opencode/minimax-m2.5-free`

- [x] Update [conftest.py](http://conftest.py) for FastAPI TestClient
- [x] Fix async database fixtures
- [x] Add session token cookie handling

**Files**: `tests/conftest.py`

### Test Progress

| Metric | Before | After |
|--------|--------|-------|
| Failed Tests | N/A | 130 |
| Passed Tests | N/A | 284 |
| Total Tests | 414 | 414 |

### Key Accomplishments

1. **Router infrastructure** - All major routes now registered in FastAPI
2. **Action endpoints** - claim-turn, release-turn, next-turn, fire, ram
3. **Import/Export** - characters, ships, NPCs, backup endpoints
4. **Scene endpoints** - participants, ships, activation
5. **Minor action enforcement** - prevents 2nd minor action (403)
6. **Model fixes** - sensors attribute access

### Remaining Issues (130 failures)

| Category | Count | Issue |
|----------|-------|-------|
| Scene tests | 41 | Validation/logic |
| Import/Export | 30 | Specific fields |
| Personnel | 10 | Validation |
| Session Tokens | 8 | Flask redirects |
| Other | 41 | Various |

### Current Test State (2026-03-15)

| Metric | Value |
|--------|-------|
| Failed Tests | 122 → 110 → 102 → 93 → 86 → 47 → 39 → 37 → 38 → 34 |
| Passed Tests | 292 → 304 → 312 → 321 → 328 → 334 → 342 → 344 → 343 → 347 |
| Total Tests | 414 → 370 → 381 |

### Key Issues Identified

| Category | Count | Examples |
|----------|-------|----------|
| **404 Route Errors** | ~30 | Scene API endpoints returning 404 (FastAPI routing issues) |
| **Flask 3.x API Changes** | ~15 | `get_data()` removed, `delete_cookie` missing |
| **Async/SQLAlchemy Issues** | ~10 | MissingGreenlet, AsyncEngine inspection errors |
| **Status Code Mismatches** | ~15 | 422 vs 400, 200 vs 400, 404 vs 302 |
| **Logic Errors** | ~5 | Scene activation returns 'draft' instead of 'active' |

### Proposed Fix Order

1. **Fix FastAPI Routing** - Routes not properly registered (likely `/api/` prefix issues)
2. **Fix/Remove Flask Remainders** - Update tests for Flask 3.x TestClient API changes
3. **Fix Async Issues** - Use `run_sync` for SQLAlchemy inspection in async context
4. **Fix Scene Activation** - Clarify logic bug returning wrong status

### Acceptance Criteria

- [ ] Core routing migration complete
- [ ] All endpoints return non-404 responses
- [ ] Turn order logic working
- [ ] All tests passing (target: 0 failed)

---

## Milestone 4: Character/Ship CRUD

### Overview
Complete character and ship creation, management, and library integration.

### Tasks

#### Task 4.1: Character Management
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement `/api/characters/*` endpoints:
- CRUD for PCs and NPCs
- Attribute/department management
- Trait/talent assignment
- Equipment and attack management
- State tracking (Ok, Defeated, Fatigued, Dead)
- [ ] Add character import/export
- [ ] Implement species and role management

**Files**: `sta/web/routes/characters.py` (new)

#### Task 4.2: Ship Management
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement `/api/ships/*` endpoints:
- CRUD for player and NPC ships
- System/department management
- Weapon and talent assignment
- Power/shield tracking
- Trait management
- [ ] Add ship class and scale validation
- [ ] Implement crew quality for NPC ships

**Files**: `sta/web/routes/ships.py` (new)

#### Task 4.3: Library Integration
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Connect characters/ships to Universe Library
- [ ] Implement library search and filtering
- [ ] Add duplicate detection
- [ ] Create template system for quick creation
- [ ] Implement GM-only library management

**Files**: `sta/web/routes/universe.py`, `sta/web/routes/characters.py`, `sta/web/routes/ships.py`

### Testing Strategy
- **Unit Tests**: Model validation and constraints
- **Integration Tests**: CRUD workflows
- **Import/Export Tests**: Data serialization
- **Library Tests**: Search and filtering

### Acceptance Criteria
- ✅ Character CRUD with all attributes
- ✅ Ship CRUD with systems and weapons
- ✅ Library integration with templates
- ✅ Import/export functionality
- ✅ All tests passing

### Timeline: 5-7 days

## Milestone 5: Combat Integration

### Overview
Integrate existing combat system with new VTT architecture.

### Tasks

#### Task 5.1: Combat Scene Type
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Enhance Scene model for combat support
- [ ] Add tactical map integration
- [ ] Implement hex grid system
- [ ] Add terrain and visibility rules
- [ ] Create combat state tracking

**Files**: `sta/models/vtt/models.py`, `sta/mechanics/combat.py` (new)

#### Task 5.2: Action System Integration
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Adapt declarative action system for VTT
- [ ] Integrate with new Scene model
- [ ] Add range and system requirement checks
- [ ] Implement action logging
- [ ] Create combat turn management

**Files**: `sta/mechanics/action_config.py`, `sta/web/routes/api.py`

#### Task 5.3: Combat UI Integration
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Update combat templates for VTT
- [ ] Integrate with scene views
- [ ] Add GM combat controls
- [ ] Implement player action interface
- [ ] Create combat log display

**Files**: `sta/web/templates/combat.html`, `sta/web/templates/scenes.html`

### Testing Strategy
- **Unit Tests**: Combat mechanics and calculations
- **Integration Tests**: Combat workflows
- **Regression Tests**: Existing combat still works
- **Action Tests**: All actions functional

### Acceptance Criteria
- ✅ Combat scenes fully functional
- ✅ Action system integrated
- ✅ Tactical map working
- ✅ Combat UI updated
- ✅ All tests passing

### Timeline: 7-10 days

## Milestone 6: UI/UX Overhaul

### Overview
Complete UI/UX redesign for mobile-responsive VTT experience.

### Status: 🚧 IN PROGRESS

#### 6.1: Campaign Dashboard
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Redesign campaign selection interface
- [ ] Create campaign overview dashboard
- [ ] Implement mobile-responsive layout
- [ ] Add campaign statistics display
- [ ] Create GM/player view toggles

**Files**: `sta/web/templates/campaigns.html`, `sta/static/css/`

#### 6.2: Scene Management UI
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Redesign scene creation interface
- [ ] Create scene navigation system
- [ ] Implement scene type selection
- [ ] Add participant management UI
- [ ] Create scene transition controls

**Files**: `sta/web/templates/scenes.html`, `sta/static/js/scenes.js`

#### 6.3: Character/Ship Builders
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Create character builder interface
- [ ] Design ship configuration UI
- [ ] Implement library browser
- [ ] Add template selection
- [ ] Create import/export interface

**Files**: `sta/web/templates/characters.html`, `sta/web/templates/ships.html`

### Testing Strategy
- **Unit Tests**: Template rendering
- **Integration Tests**: UI workflows
- **Browser Tests**: Cross-browser compatibility
- **Mobile Tests**: Responsive design
- **Accessibility Tests**: WCAG compliance

### Acceptance Criteria
- ✅ Mobile-responsive design
- ✅ Intuitive navigation
- ✅ Character/ship builders functional
- ✅ GM and player views optimized
- ✅ All tests passing

### Timeline: 10-14 days

## Milestone 7: Import/Export &amp; Final Integration

### Overview
Implement import/export functionality and complete VTT integration.

### Status: 📋 Planned

### Tasks

#### Task 7.1: VTT Character Export/Import
- Export characters to JSON
- Import characters from JSON
- Handle updates to existing characters

#### Task 7.2: VTT Ship Export/Import
- Export ships to JSON
- Import ships from JSON
- Handle updates to existing ships

#### Task 7.3: Full Campaign Backup
- Export entire campaign to JSON
- Import full campaign backup
- Validate backup structure

### Reference
See `docs/tasks/milestone7_tasks.md` for detailed specification.

### Timeline: 3-5 days

## Parallel Work Strategy

### Agent Assignment

| Milestone | Agent 1 (Database/API) | Agent 2 (Models/Logic) | Agent 3 (Tests/Integration) |
|-----------|------------------------|------------------------|-----------------------------|
| M1 | Database schema | VTT models | Migration tests |
| M2 | Campaign API | Universe library | Campaign tests |
| M3 | Scene API | Scene transitions | Scene tests |
| M4 | Character API | Ship management | CRUD tests |
| M5 | Combat integration | Action system | Combat tests |
| M6 | UI components | UI logic | UI tests |

### Workflow

1. **Daily Standup**: Agents report progress, blockers
2. **Continuous Integration**: Merge to `develop` frequently
3. **Code Reviews**: Cross-agent reviews before PR
4. **User Demos**: Show progress after each milestone

### Communication

- **Shared Context**: All agents read `docs/learnings_and_decisions.md`
- **Blockers**: Escalate to user immediately
- **Decisions**: Document in learning log
- **Conflicts**: User arbitrates

## Testing Strategy

### Test Coverage Requirements

- **Unit Tests**: 90%+ coverage for business logic
- **Integration Tests**: All critical workflows
- **Regression Tests**: Legacy functionality preserved
- **E2E Tests**: Major user journeys

### Test Execution

`bash # Before every commit pytest # Before PR pytest --cov=sta --cov-report=term-missing # Specific tests pytest tests/test_*.py -v `

### Test Categories

1. **Model Tests**: Pydantic validation, serialization
2. **Database Tests**: CRUD operations, transactions
3. **API Tests**: Endpoint validation, error handling
4. **Integration Tests**: Workflow testing
5. **UI Tests**: Template rendering, JavaScript
6. **Regression Tests**: Legacy compatibility

## Code Review Process

### Review Workflow

1. **Agent implements feature** in feature branch
2. **Agent runs tests** and fixes issues
3. **Code auditor reviews** with `opencode/claude-sonnet-4-5`
4. **Agent fixes review issues**
5. **Agent creates PR** to `develop`
6. **User reviews and approves**
7. **Merge to develop** for integration
8. **Repeat for main** after milestone complete

### Review Checklist

- [ ] Code follows existing patterns
- [ ] Tests pass (including new tests)
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Error handling adequate
- [ ] Performance acceptable
- [ ] Security considerations addressed

## Acceptance Criteria

### Per Milestone

- ✅ All tasks completed
- ✅ All tests passing
- ✅ Code review approved
- ✅ Documentation updated
- ✅ User acceptance obtained
- ✅ No regressions introduced

### Final Delivery

- ✅ All 6 milestones completed
- ✅ Full VTT functionality working
- ✅ Legacy code removed
- ✅ Comprehensive test suite
- ✅ User documentation complete
- ✅ Production ready

## Risk Management

### Identified Risks

1. **Model Limitations**: Free models may have context limits
- **Mitigation**: Break tasks into smaller chunks

2. **Merge Conflicts**: Parallel work may cause conflicts
- **Mitigation**: Use git worktrees, frequent integration

3. **Legacy Dependencies**: Undiscovered dependencies on old code
- **Mitigation**: Comprehensive testing, gradual deprecation

4. **Performance Issues**: New VTT features may be slow
- **Mitigation**: Add indexes, optimize queries, load testing

5. **UI Complexity**: Mobile-responsive design challenges
- **Mitigation**: Use framework (Bootstrap/Tailwind), test on devices

### Contingency Plans

1. **Fallback Models**: If free models underperform, use `opencode/claude-haiku-4-5`
2. **Feature Flags**: Disable problematic features temporarily
3. **Rollback Plan**: Keep legacy system until VTT stable
4. **Performance Optimization**: Profile and optimize critical paths

## Success Metrics

### Quantitative
- ✅ 90%+ test coverage
- ✅ 0 critical bugs in production
- ✅ &lt; 2s response time for API endpoints
- ✅ &lt; 5s page load time
- ✅ 100% milestone completion

### Qualitative
- ✅ Intuitive user experience
- ✅ GM has sufficient control
- ✅ Players enjoy the interface
- ✅ Mobile-friendly on tablets
- ✅ Stable and reliable

## Immediate Next Steps (2026-03-17)

### Current State
- M6 PR #14 merged to vtt-scope
- M7 branch created: `m7-branch`
- M7 task document ready: `docs/tasks/milestone7_tasks.md`

### Pending: M7 Agent Deployment

**Three agents to deploy in parallel:**

| Agent | Task | Worktree Branch |
|-------|------|------------------|
| Agent 1 | M7.1 Character Export/Import | feature/m7-character-import-export |
| Agent 2 | M7.2 Ship Export/Import | feature/m7-ship-import-export |
| Agent 3 | M7.3 Campaign Backup | feature/m7-campaign-backup |

**Commands to create worktrees (for agents):**
`bash # Agent 1 git worktree add -b feature/m7-character-import-export ../m7-character-import-export m7-branch cd ../m7-character-import-export && uv venv && uv pip install -r requirements.txt -r requirements-dev.txt # Agent 2 git worktree add -b feature/m7-ship-import-export ../m7-ship-import-export m7-branch cd ../m7-ship-import-export && uv venv && uv pip install -r requirements.txt -r requirements-dev.txt # Agent 3 git worktree add -b feature/m7-campaign-backup ../m7-campaign-backup m7-branch cd ../m7-campaign-backup && uv venv && uv pip install -r requirements.txt -r requirements-dev.txt `

**After Agents Complete:**
1. Merge feature/m7-character-import-export → m7-branch
2. Merge feature/m7-ship-import-export → m7-branch
3. Merge feature/m7-campaign-backup → m7-branch
4. Run full test suite: `uv run pytest -q`
5. Clean up worktrees
6. Push m7-branch to origin
7. Create PR to vtt-scope

### Documentation Updates After M7
- Mark M7 complete in [README.md](http://README.md)
- Mark M7 complete in docs/delivery_plan.md
- Mark M7 complete in docs/README.md
- Update milestone status in docs/tasks/milestone7_tasks.md

---

## Next Steps (Original)

1. **User Review**: Please review this delivery plan
2. **Approvals**: Confirm approach and timeline
3. **Adjustments**: Make any needed changes
4. **Kickoff**: Begin Milestone 1 implementation

**Question**: Does this plan meet your expectations? Are there any adjustments needed before we proceed?
(End of file - total 864 lines)
``
