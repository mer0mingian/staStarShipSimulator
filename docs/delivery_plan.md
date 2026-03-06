# VTT Transition Delivery Plan

## Executive Summary

This document outlines the comprehensive plan for transitioning the Star Trek Adventures Starship Simulator from a dedicated combat encounter tool to a minimal Virtual Tabletop (VTT) experience. The plan covers all 6 milestones with detailed task breakdowns, parallel work assignments, testing strategies, and acceptance criteria.

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
```json
{
  "model": "opencode/minimax-m2.5-free",
  "provider": {
    "opencode": {}
  }
}
```

### Code Review Models
```json
{
  "model": "opencode/claude-sonnet-4-5",
  "provider": {
    "opencode": {}
  }
}
```

**Agent Configuration**:
- **python-dev agents**: Use `opencode/minimax-m2.5-free` (free tier)
- **code-reviewer agents**: Use `opencode/claude-sonnet-4-5` (high quality)
- **All agents**: Use `modern-python` skill for best practices

## Git Workflow

### Branch Structure
```
main (protected)
  ├── develop (integration branch)
  │   ├── feature/m1-database-schema
  │   ├── feature/m2-campaign-mgmt
  │   ├── feature/m3-scene-mgmt
  │   ├── feature/m4-char-ship-crud
  │   ├── feature/m5-combat-integration
  │   └── feature/m6-ui-ux-overhaul
```

### Workflow Rules
1. **Never commit directly to `main`**
2. **Feature branches** created from `develop`
3. **Git worktrees** for isolation (managed by agents)
4. **PR to `develop`** for integration testing
5. **PR to `main`** after milestone validation
6. **Code auditor review** before user review
7. **User approval** required for all merges

### Worktree Management
```bash
# Create worktree for feature
git worktree add ../feature-m1-database develop

# Work in isolated directory
cd ../feature-m1-database

# Create feature branch
git checkout -b feature/m1-database-schema

# Work, commit, push
# ...

# Cleanup when done
git worktree remove ../feature-m1-database
```

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

#### Task 1.3: Legacy Inventory & Documentation
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

### Status: IN PROGRESS

### Detailed Tasks
See `docs/milestone2_tasks.md` for specific implementation steps.

### Current State
Most campaign infrastructure already exists. Main gaps:
- Resource pool management (Momentum/Threat at campaign level)
- Universe Library API (new VTT integration)
- VTT character/ship integration with campaigns

### Tasks (Summary)

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

### Timeline: 5-7 days

## Milestone 3: Scene Management

### Overview
Complete scene lifecycle with narrative and combat support.

### Tasks

#### Task 3.1: Scene CRUD API
**Agent**: python-dev
**Skills**: modern-python, fastapi-pro
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement `/api/scenes/*` endpoints:
  - `POST /api/scenes` - Create scene
  - `GET /api/scenes/{id}` - Get scene details
  - `PUT /api/scenes/{id}` - Update scene
  - `POST /api/scenes/{id}/activate` - Activate scene
  - `POST /api/scenes/{id}/end` - End scene
  - `GET /api/scenes/{id}/participants` - List participants
- [ ] Add scene type support (narrative, combat, social)
- [ ] Implement scene status transitions (draft → active → completed)

**Files**: `sta/web/routes/scenes.py`

#### Task 3.2: Scene Transitions
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement connected scene logic
- [ ] Add Momentum reduction on transition (min 0)
- [ ] Create GM prompt for next scene selection
- [ ] Implement ad-hoc scene creation
- [ ] Add campaign overview return option

**Files**: `sta/web/routes/scenes.py`, `sta/mechanics/scene_transitions.py` (new)

#### Task 3.3: Participant Management
**Agent**: python-dev
**Skills**: modern-python
**Model**: `opencode/minimax-m2.5-free`

- [ ] Implement `/api/scenes/{id}/participants` endpoints
- [ ] Add character/ship assignment to scenes
- [ ] Implement visibility controls (GM vs players)
- [ ] Create initiative order management
- [ ] Add turn tracking system

**Files**: `sta/web/routes/scenes.py`, `sta/models/vtt/models.py`

### Testing Strategy
- **Unit Tests**: Scene validation and state transitions
- **Integration Tests**: Scene lifecycle workflows
- **Concurrency Tests**: Multiple participants joining
- **State Tests**: Scene status transitions

### Acceptance Criteria
- ✅ Scene CRUD fully functional
- ✅ Scene transitions with Momentum management
- ✅ Participant management with visibility controls
- ✅ Initiative and turn system working
- ✅ All tests passing

### Timeline: 5-7 days

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

### Sub-Milestones

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

```bash
# Before every commit
pytest

# Before PR
pytest --cov=sta --cov-report=term-missing

# Specific tests
pytest tests/test_*.py -v
```

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
- ✅ < 2s response time for API endpoints
- ✅ < 5s page load time
- ✅ 100% milestone completion

### Qualitative
- ✅ Intuitive user experience
- ✅ GM has sufficient control
- ✅ Players enjoy the interface
- ✅ Mobile-friendly on tablets
- ✅ Stable and reliable

## Next Steps

1. **User Review**: Please review this delivery plan
2. **Approvals**: Confirm approach and timeline
3. **Adjustments**: Make any needed changes
4. **Kickoff**: Begin Milestone 1 implementation

**Question**: Does this plan meet your expectations? Are there any adjustments needed before we proceed?