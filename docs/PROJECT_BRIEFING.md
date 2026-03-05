# Project Briefing: VTT Scope Transition

## Overview
This document outlines the architectural changes required to transition the **Star Trek Adventures (STA) Starship Simulator** from a dedicated combat encounter tool to a **minimal Virtual Tabletop (VTT)** experience.

## Project Goal
Expand the scope to support:
- Character & Ship management (Main/Support PCs, NPCs)
- Multiple Scenes within a Campaign
- Improved Navigation & UI/UX
- Reusable Universe Library for Game Masters

## Key Learnings & Decisions

### 1. Data Model (Pydantic Schemas)
Location: `sta/models/vtt/`

- **`types.py`**: Core enumerations (Attribute, Department, System, CharState, etc.) and derived types (Attributes as 6-tuple).
- **`models.py`**: 
  - `Character` (Base), `Pc`, `Npc` - Support for Species, Traits, Talents, Attacks, Equipment.
  - `Ship` - Scale [1-7], Resistance, Systems (6), Departments (6), Power/Shields (simplified), Weapons.
  - `Scene` - Status (Active/Archived/Connected), Participants (Player/Non-Player), Initiative Order, Situation Traits.
- **`campaign.py`**:
  - `Campaign` - Shared Momentum/Threat, Scenes list, GM/Player identity.
  - `UniverseLibrary` - GM's private reusable content.

### 2. Rules Reference
- **Attributes**: Control, Daring, Fitness, Insight, Presence, Reason (7-12 range for humanoids).
- **Departments**: Command, Conn, Engineering, Medicine, Science, Security (0-5 range).
- **Stress**: Max = Fitness (for PCs).
- **Momentum**: Campaign-wide, max 6.
- **Threat**: GM pool.
- **Ship Combat**: Simplified shields (single value, not quadrant-based).

### 3. UI/UX Issues (Current)
- Navigation is not intuitive.
- Setup is difficult for new users.
- Needs mobile/tablet responsiveness (primary use case: shared screen/TV).

### 4. Personas
- **Player**: Can manage own PCs, view Campaign Library, enter Active Scenes.
- **GM**: Manage Universe Library, Campaigns, Scenes, Narrate, Control NPCs.
- **Observer**: View-only access (optional future feature).

### 5. Workflows
- **Player**: Login -> Select Campaign -> Overview (select PC/Ship) -> Enter Active Scene.
- **GM**: Login (Universe) -> Manage Campaigns -> Create/Activate Scenes -> Enter Scene Management.

### 6. Technical Debt
- Current `sta/models/` contains legacy schemas (`character.py`, `starship.py`, `combat.py`).
- `sta/mechanics/action_config.py` contains declarative action definitions (reusable).
- No existing Auth system (simple Name-Password proposed).

## Next Steps
1. Answer open questions in `docs/open_questions.md`.
2. Finalize Campaign & Scene specifications.
3. Design Database Schema (SQLAlchemy).
4. Implement UI navigation overhaul.

## References
- `docs/documentation/objects.md` - Object definitions.
- `docs/rules_reference.md` - Links to extracted STA 2e rules.
- `ADDING_ACTIONS.md` - Declarative action system guide.
