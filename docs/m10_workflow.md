# Milestone 10 Workflow Documentation
This document outlines the complete process for developing Milestone 10 features, based on project guidelines and the user's specific request.

## Goal
Unify encounter management under scenes: remove standalone encounter creation, extend scene editor with full encounter configuration, and wire encounter derivation through scene activation.

## Phase 1: Preparation & Documentation
1. **Branching:** Create and push remote branch: `feature/m10-page-structure` from `main`
2. **M10 Plan Created:** `docs/tasks/milestone10_tasks.md` drafted
3. **Workflow Documented:** This file documents the execution plan
4. **References Updated:** `docs/README.md` and `delivery_plan.md` to be updated

## Phase 2: Detailed Agent Execution Plan

### Agent Strategy
- **Backend/API Work (Tasks 1-3, 6):** Assigned to `python-dev` subagent
- **Frontend/UI Work (Tasks 4-5):** Assigned to `python-dev` subagent
- **Model:** `opencode/minimax-m2.5-free`

### Task Breakdown & Execution Order
| Order | Task Description | Status | Agent Type |
| :---: | :--- | :---: | :--- |
| 1 | Deprecate standalone encounter creation | ⏳ Pending | `python-dev` |
| 2 | Extend Scene editor with encounter config | ⏳ Pending | `python-dev` |
| 3 | Wire encounter_config_json through activation | ⏳ Pending | `python-dev` |
| 4 | Update Scene editor UI (ships, participants, map, config) | ⏳ Pending | `python-dev` |
| 5 | Update campaign dashboard scene/encounter display | ⏳ Pending | `python-dev` |
| 6 | Legacy field cleanup | ⏳ Pending | `python-dev` |
| 7 | Tests and verification | ⏳ Pending | `python-dev` |

### Mandatory Agent Protocols
- **Worktrees/VENV:** Use separate worktree for agent execution: `git worktree add -b feature/m10-page-structure ../m10-page-structure main`
- **Testing:** All subagents write spec-driven tests
- **Review Loop:** All tasks follow spec compliance then code quality review
- **Minimal Changes:** Keep changes surgical, match existing style

## Phase 3: Final Verification & Merge
1. **Test Run:** Full test suite: `uv run pytest tests/ -v`
2. **Code Review:** via `code-reviewer` agent
3. **Merge:** PR to `main`
4. **Documentation Update:** `delivery_plan.md`, `README.md`, `docs/README.md`

## Design Summary
- **Encounters are purely derived** from scenes at activation time
- **Scene is the planning layer**: ships, participants, tactical map, encounter config
- **Encounter is the runtime layer**: positions, turns, momentum, effects (copies from scene on activation)
- **Standalone encounter creation is removed**: `/campaigns/{id}/new-encounter` and `new_encounter.html`
- **Legacy encounter routes kept**: `/encounters/{id}` and related serve viewing derived encounters

See `docs/tasks/milestone10_tasks.md` for detailed task specifications.
