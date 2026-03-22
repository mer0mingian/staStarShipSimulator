# VTT Transition Delivery Plan
## Executive Summary
This document outlines the comprehensive plan for transitioning the Star Trek Adventures Starship Simulator from a dedicated combat encounter tool to a minimal Virtual Tabletop (VTT) experience. The plan covers all milestones with detailed task breakdowns, parallel work assignments, testing strategies, and acceptance criteria.
**Status**: M1-M9 **COMPLETE**. M10 **IN PROGRESS** - UX/Architecture Rework.

## Milestone 8.2: Rules Understanding & Documentation Sync
### Status: ✅ Complete — Documentation synchronized with core rules (Ch 7, 9 analysis complete).

## Milestone 9: Web UI & Theme Support
### Status: ✅ Complete — Merged to `main` (PR #21)

## Milestone 10: Page Structure Rework & UX Enhancements (Planned)
### Overview
Unify encounter management under scenes and implement critical UX/UI enhancements for player resources, guided creation, rule-compliant action resolution, and dynamic pacing.

### Design Decisions (Finalized)
- **Encounters/Traits:** Scenes host encounters. **Traits** are the primary mechanism for altering task Difficulty/Complication Range (per Ch 7/9).
- **Turn Order:** Dynamic **"Action Taken"** status per participant in an Encounter Round.
- **Player Resources:** UI features **Stress**, **Determination (Max 3)**, and **Momentum** tracking. **Values** are marked **Used (Session Limit)** or used to gain Determination (**Challenged/Complied**).
- **Action Resolution:** Detailed **Dice Roll Interface** visualizes all dice, showing modifiers from Talents/Abilities *after* the initial roll.
- **Creation:** Character/Ship creation uses a **multi-step guided wizard** with rulebook terminology (**Foundation, Specialization, Identity, Equipment**).
- **Narrative:** Character sheets feature a **Narrative Tab** with **Personal Logs (visible to all players)** and **auto-generated Mission/Value Logs**.

### Status: 📋 PLANNED (Awaiting Implementation)
### Tasks
| Task | Description |
|---|---|
| M10.1 - M10.5 | Scene/Encounter decoupling and core configuration wiring. |
| M10.6 | Player Console UI & Detailed Dice Roll Interface (Attr/Dept selection, dice visualization, GM difficulty control). |
| M10.7 | GM Console UI & Resource Feedback (Threat Spends, tracking player Determination/Value changes). |
| M10.8 | Dynamic Round Tracker (Shows "Action Taken" status per participant). |
| M10.9 | Character Sheet Overhaul (Narrative Tab for Values/Logs/Player-visible logs). |
| M10.10 | Guided Character/Ship Creation Flow (Multi-step wizard). |
| M10.11 | Action Resolution Logic implementation summary. |
| M10.12 | Legacy field cleanup. |
| M10.13 | Tests and verification (Extended). |

### Future Milestones (Deferred)
- **Spectator View:** Moved to **M13** to prioritize core gameplay stability in M10/M11/M12.

**Branch:** `feature/m10-page-structure-ux` from `main`
**Tasks doc:** `docs/tasks/milestone10_tasks.md`

## Acceptance Criteria
- ✅ All M10 tasks (including UX enhancements) are implemented.
- ✅ Player resource interaction and Dice Roll interface are fully functional.
- ✅ **Traits** are used correctly to model temporary scene conditions affecting task difficulty/complications.
- ✅ Tests for new functionality pass.

## Next Steps
1.  Begin implementation of the detailed M10 plan.
2.  Document all structural/design decisions in `docs/learnings_and_decisions.md`.
3.  Continue to verify rule compliance as code is modified.