# Documentation Structure

This project uses **progressive disclosure** - showing essential information first, with detailed references available on demand.

## Quick Navigation

| Looking for... | Go to... |
|----------------|---------|
| Project overview & roadmap | [`delivery_plan.md`](delivery_plan.md) |
| **Game rules & mechanics** | [`references/game_machanics.md`](references/game_machanics.md) |
| **Data models** | [`references/objects.md`](references/objects.md) |
| **Talent/Special Rules design** | [`references/talent_system_design.md`](references/talent_system_design.md) |
| Development decisions | [`archive/learnings_and_decisions.md`](archive/learnings_and_decisions.md) |
| Technical architecture | [`references/technical.md`](references/technical.md) |
| STA 2e rules reference | [`rules_reference.md`](rules_reference.md) |

---

## Folder Structure

### Start Here
- **[delivery_plan.md](delivery_plan.md)** — VTT transition overview with milestone roadmap (M1-M9)

### References (`references/`) — **Game Rules & Data Models**

| File | Description |
|------|-------------|
| **[game_machanics.md](references/game_machanics.md)** | Core game mechanics: dice system, Momentum/Threat, Ship Stress/Shields/Breaches, Actions |
| **[objects.md](references/objects.md)** | Data models: Characters, NPCs, Ships, Scenes, Traits, Talents |
| **[talent_system_design.md](references/talent_system_design.md)** | Design for Talent/Special Rules/Species Ability objects (Phase 1 & 2) |
| **[technical.md](references/technical.md)** | Tech stack, project structure, database schema |
| **[legacy_index.md](references/legacy_index.md)** | Legacy code inventory |

### Rules (`sta2e_rules/`) — **STA 2e Rulebook Reference**
- Extracted chapters from STA 2e Core Rulebook (reference only)
- See [`rules_reference.md`](rules_reference.md) for file index

### Tasks (`tasks/`)
Completed milestone task lists (M1-M8 all complete):
- [`tasks/milestone8_tasks.md`](tasks/milestone8_tasks.md)
- [`tasks/milestone7_tasks.md`](tasks/milestone7_tasks.md)
- [`tasks/milestone6_tasks.md`](tasks/milestone6_tasks.md)
- [`tasks/milestone5_tasks.md`](tasks/milestone5_tasks.md)
- [`tasks/milestone4_tasks.md`](tasks/milestone4_tasks.md)
- [`tasks/milestone3_tasks.md`](tasks/milestone3_tasks.md)
- [`tasks/milestone2_tasks.md`](tasks/milestone2_tasks.md)

### Future (`tasks/future/`)
- [`tasks/future/roadmap_proposal.md`](tasks/future/roadmap_proposal.md) — M9+ features

### Archive (`archive/`)
Historical context and resolved decisions:
- [`archive/learnings_and_decisions.md`](archive/learnings_and_decisions.md) — Development decision log
- [`archive/m8.2-open-questions.md`](archive/m8.2-open-questions.md) — Resolved M8.2 rules questions
- [`archive/open_questions.md`](archive/open_questions.md) — Older resolved questions
- [`archive/PROJECT_BRIEFING.md`](archive/PROJECT_BRIEFING.md) — Original VTT scope requirements
- [`archive/agent_summary.md`](archive/agent_summary.md) — Agent configuration

---

## Reading Order

### For Players
1. [`README.md`](../README.md) — Quick start and how to play

### For Developers
1. [`delivery_plan.md`](delivery_plan.md) — Understand the project scope
2. [`references/game_machanics.md`](references/game_machanics.md) — Understand game rules
3. [`references/objects.md`](references/objects.md) — Understand data models
4. [`references/technical.md`](references/technical.md) — Understand the codebase
5. [`AGENTS.md`](../AGENTS.md) — Agent workflow for development

### For Game Masters
1. [`delivery_plan.md`](delivery_plan.md) — VTT features overview
2. [`references/game_machanics.md`](references/game_machanics.md) — Detailed rules
3. [`references/objects.md`](references/objects.md) — NPC/Ship data structures
