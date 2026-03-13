# Learnings and Decisions

This document captures key learnings from user feedback and decisions made during the VTT transition project.

## Table of Contents

- [Model Selection and Configuration](#model-selection-and-configuration)
- [Project Scope and Milestones](#project-scope-and-milestones)
- [Database Migration Strategy](#database-migration-strategy)
- [Authentication System](#authentication-system)
- [Parallel Development Strategy](#parallel-development-strategy)
- [Git Workflow](#git-workflow)
- [Testing Strategy](#testing-strategy)
- [Code Review Process](#code-review-process)
- [Legacy Code Management](#legacy-code-management)

## Model Selection and Configuration

### Learnings

1. **OpenCode Zen Models**: The user specified using "OpenCode Zen MiniMax 2.5 Free" and "Big Pickle" for development work, and "Mistral/Codestral" or "Mistral/Devstral 2" for code reviews.

2. **Available Models**: Research revealed these are available through OpenCode Zen:
   - `minimax-m2.5-free` - Free tier, suitable for development
   - `big-pickle` - Free tier, suitable for development  
   - Mistral models are not directly available in OpenCode Zen

3. **Configuration Method**: Models are configured in `opencode.json` using the format `opencode/<model-id>`

### Decisions

1. **Development Models**: Use `opencode/minimax-m2.5-free` for development agents (free tier)
2. **Code Review Models**: Use `opencode/claude-sonnet-4-5` for code reviews (paid but high quality)
3. **Configuration**: Update `opencode.json` to specify model preferences per agent type

## Project Scope and Milestones

### Learnings

1. **Full Transition**: User wants complete VTT transition (all milestones 1-6)
2. **Parallel Work**: Agents should work on partial deliverables simultaneously
3. **Quality Requirements**: Each deliverable must include:
   - Comprehensive test coverage
   - Regression tests
   - Integration tests with existing features
   - Code auditor review
   - User review via PR

### Decisions

1. **Milestone Prioritization**:
   - **Milestone 1**: Database Schema Migration (Foundation)
   - **Milestone 2**: Campaign Management (Core Feature)
   - **Milestone 3**: Scene Management (Core Feature)
   - **Milestone 4**: Character/Ship CRUD (Data Management)
   - **Milestone 5**: Combat Integration (Game Mechanics)
   - **Milestone 6**: UI/UX Overhaul (User Experience)

2. **Parallel Work Strategy**: 3 agents working simultaneously on isolated components

## Database Migration Strategy

### Learnings

1. **Clean Break**: No existing data needs migration - can flush database
2. **Legacy Code**: Existing combat system has schemas, models, and routes
3. **New VTT Models**: Already defined in `sta/models/vtt/`

### Decisions

1. **Migration Approach**: Create new VTT schema tables alongside legacy ones
2. **Legacy Inventory**: Create `docs/legacy_index.md` documenting all legacy components
3. **Deletion Plan**: Remove legacy code only after new VTT system is fully tested
4. **Database Flush**: Safe to delete `sta_simulator.db` and recreate

## Authentication System

### Learnings

1. **GM Password**: Already implemented in `CampaignRecord` with hashed password
2. **Player Access**: Session-based with tokens
3. **No Complex Auth**: Simple name+password sufficient for MVP

### Decisions

1. **Implementation**: Use existing GM password system
2. **Player Authentication**: Session tokens for claimed characters
3. **No OAuth**: Keep simple for initial release

## Parallel Development Strategy

### Learnings

1. **Agent Count**: 3 agents recommended for optimal parallelism.
2. **Worktree Usage**: Git worktrees are essential for isolation when agents work on same branch.
3. **Model Budget**: Use free models (MiniMax, Big Pickle) for development.
4. **Conflict Resolution**: When merging feature branches with parallel changes, expect conflicts in shared files (e.g., `scenes.py`). Resolve by carefully combining both sides' logic.
5. **Test Environment**: Agents must ensure virtualenv exists; if missing, `uv venv` + `uv pip install -r requirements*.txt` fixes.

### Decisions

1. **Agent Assignment**:
   - Agent 1: Database & Models (python-dev skill)
   - Agent 2: API & Backend (python-dev skill)  
   - Agent 3: Tests & Integration (code-reviewer skill)

2. **Worktree Management**: Use git worktrees for each feature branch; agents commit to their own worktree branch then merge to main feature branch.

3. **Model Configuration**:
   - Dev agents: `opencode/minimax-m2.5-free`
   - Code review: `opencode/claude-sonnet-4-5`

4. **Workflow**:
   - Create worktree from base: `git worktree add -b <task-branch> <path> <base-branch>`
   - Agent works, tests, commits, pushes
   - Main branch merges each task branch
   - Resolve conflicts by taking both sides' distinct functions/endpoints

## Git Workflow

### Learnings

1. **User Preference**: Worktree-based isolation
2. **Existing Setup**: Git repository with main branch
3. **Review Process**: PR-based with user approval

### Decisions

1. **Branch Structure**:
   ```
   main (protected)
   ├── develop (integration)
   │   ├── feature/m1-database-schema
   │   ├── feature/m2-campaign-mgmt
   │   └── feature/m3-scene-mgmt
   ```

2. **Workflow Rules**:
   - Never commit directly to `main`
   - Feature branches from `develop`
   - PR to `develop` for integration
   - PR to `main` after milestone validation
   - Use worktrees for isolation

## Testing Strategy

### Learnings

1. **Mixed Approach**: TDD for core, integration for workflows
2. **Existing Tests**: Comprehensive test suite already exists
3. **Coverage Requirements**: High coverage for new features

### Decisions

1. **Testing Levels**:
   - **Unit Tests**: TDD for data models and business logic
   - **Integration Tests**: API endpoints and workflows
   - **Regression Tests**: Ensure new code doesn't break existing features
   - **E2E Tests**: Critical user journeys

2. **Test Execution**: Run `pytest` before every commit

## Code Review Process

### Learnings

1. **Review Models**: Use Mistral/Codestral for code reviews
2. **Quality Standards**: High bar for code quality
3. **Iteration Expected**: Multiple review cycles likely

### Decisions

1. **Review Workflow**:
   - Agent implements feature
   - Code auditor reviews with `opencode/claude-sonnet-4-5`
   - Agent fixes issues
   - User reviews final PR

2. **Review Criteria**:
   - Code follows existing patterns
   - Tests pass
   - Documentation updated
   - No breaking changes

## Legacy Code Management

### Learnings

1. **Inventory Needed**: Document all legacy components
2. **Gradual Removal**: Only delete after new system works
3. **Compatibility**: Some legacy may need to coexist temporarily

### Decisions

1. **Legacy Inventory**: Create `docs/legacy_index.md` with:
   - All legacy database tables
   - Legacy model classes
   - Legacy route endpoints
   - Legacy configuration files

2. **Removal Plan**: Delete legacy code in final cleanup milestone

## Milestone 4: Character/Ship CRUD

### Learnings
- Completed character and ship CRUD APIs.
- Integrated character/ship management with the Universe Library.
- Implemented import/export functionality for VTT records.
- Identified some LSP errors in `campaigns.py` and `scenes.py` that need monitoring during future milestones.

### Decisions
- Successfully completed Milestone 4.
- Milestone 4 is now marked as complete in the delivery plan.

## Milestone 5: Combat Integration

### Learnings
- Milestone 5 requires bridging the gap between new VTT models (`VTTCharacterRecord`, `VTTShipRecord`) and the legacy combat system.
- `EncounterRecord` currently manages combat state but needs updates to fully support VTT records and multiple players.

### Decisions
- Created a detailed task list in `docs/tasks/milestone5_tasks.md`.
- Implementation will focus on a unified `VTTCombatManager` in `sta/mechanics/vtt_combat.py`.
- Action system will be adapted to handle VTT records natively.
- UI integration will focus on updating existing `combat.html` and `combat_gm.html` templates to use new VTT APIs.

## Continuous Update Instructions

This document should be continuously updated throughout the project:

1. **After Each Decision**: Add new section or update existing
2. **After User Feedback**: Document learnings and decisions
3. **After Milestone Completion**: Review and update strategy
4. **Before Starting New Work**: Consult this document

**Format for Updates**:
```markdown
## [Topic]

### Learnings
- Bullet point of what was learned
- Another learning point

### Decisions  
- Decision made based on learnings
- Implementation approach chosen
```

**Update Frequency**: After every significant user interaction or milestone completion.