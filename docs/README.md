# Documentation Structure

This project uses **progressive disclosure** - showing essential information first, with detailed references available on demand.

## Progressive Disclosure Levels

| Level | Files | Description |
|-------|-------|-------------|
| **Start Here** | `delivery_plan.md` | VTT transition overview and milestone roadmap |
| **Current Work** | `tasks/milestone5_tasks.md` | Specific tasks for current milestone (M5 in progress) |
| **Reference** | See `references/` folder | Game rules, data models, technical details |

## Folder Structure

### Essential (Start Here)
- **delivery_plan.md** - High-level VTT transition plan with all 6 milestones

### Tasks (`tasks/`)
Active and completed milestone task lists:
- `milestone6_tasks.md` - UI/UX Overhaul (current)
- `milestone5_tasks.md` - Combat Integration + Scene Lifecycle (complete)
- `milestone4_tasks.md` - Character/Ship CRUD (complete)
- `milestone3_tasks.md` - Scene Management (complete)
- `milestone2_tasks.md` - Campaign Management (complete)

### Reference (`references/`)
Deep-dive technical documentation:
- **objects.md** - Data models and Pydantic schemas
- **game_machanics.md** - Combat mechanics, dice system, actions
- **technical.md** - Current tech stack and project structure
- **legacy_index.md** - Legacy code inventory

### Root Level Reference
- **rules_reference.md** - STA 2e rules index (links to raw rulebook chapters in `sta2e_rules/`)

### Archive (`archive/`)
Historical context and decisions:
- **PROJECT_BRIEFING.md** - Original VTT scope transition requirements
- **learnings_and_decisions.md** - Development decision log
- **agent_summary.md** - Agent configuration and model usage
- **open_questions.md** - Unresolved design questions

### External
- **sta2e_rules/** - Raw STA 2e Core Rulebook chapters (reference only, not for redistribution)

---

**Reading Order (Progressive Disclosure):**
1. Start with `delivery_plan.md` to understand the project
2. Check `tasks/milestone5_tasks.md` for current work
3. Dive into `references/` for specific technical details
4. Check `archive/` for historical context if needed
