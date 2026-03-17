# Proposed Roadmap: Beyond Milestone 6

## Executive Summary
Current milestones (M1-M6) cover the core VTT infrastructure: Database, Campaign/Scene Management, Character/Ship CRUD, Core Combat Integration, and UI/UX.
Analysis of the STA 2e rules reveals several advanced systems that require dedicated implementation phases. This roadmap proposes M7-M10 to cover these gaps, explicitly tying features to entity properties defined in `/docs/tasks/future/`.

## Feature Gaps Analysis

### 1. Social Conflict System
- **Source**: `sta2ecore_ch08.md`
- **Description**: Rules for social encounters (Deception, Intimidation, Negotiation) using opposed tasks and Momentum spends.
- **Entities Involved**:
  - `Social Encounter` (Entity): Links Active/Reactive characters, defines tool (Deception, etc.).
  - `Character` (Entity): Uses Attributes/Departments for opposed rolls.
  - `Resource Pool` (Entity): Momentum/Threat spends.
- **Technical Needs**:
  - Opposed task resolution logic (Active vs Reactive rolls).
  - Social "damage" (Stress) tracking on Character entity.
  - UI for social actions (linked to Social Encounter entity).
- **Status**: Not covered in M5 (Combat Integration).

### 2. Extended Tasks & Challenges
- **Source**: `sta2ecore_ch11.md`, `objects.md`
- **Description**: Multi-step tasks with Progress tracks, Breakthrough effects, and Consequence tracks.
- **Entities Involved**:
  - `Extended Task` (Entity): Properties include `work_track`, `difficulty`, `magnitude`, `resistance`.
  - `Scene` (Entity): Links Extended Task to current gameplay context.
- **Technical Needs**:
  - Progress/Consequence track UI (visualizing `work_track`).
  - Logic for calculating Impact and Breakthroughs (based on `magnitude`/`resistance`).
  - Integration with Scene resources (Momentum/Threat).
- **Status**: Not covered in M1-M6.

### 3. NPC System & Creature Rules
- **Source**: `sta2ecore_ch11.md`
- **Description**: NPC Categories (Minor/Notable/Major), Personal Threat pools, and Creature Special Rules.
- **Entities Involved**:
  - `NPC` (Entity): Inherits Character, adds `category`, `personal_threat_pool`, `background`.
  - `NPC Category Logic` (Entity): Defines rules for Minor (no Stress), Notable (3 Threat), Major (6+ Threat).
  - `Trait` (Entity): Used for Creature Special Rules (Amphibious, Invulnerable).
- **Technical Needs**:
  - NPC creation calculator (attributes/depts) via API.
  - Category-specific logic (e.g., Minor NPCs instant defeat on injury).
  - Trait system for Creatures (linking Special Rules to Traits).
- **Status**: Partially covered in M4 (Character CRUD) but specific NPC logic is missing.

### 4. Values & Directives Mechanics
- **Source**: `sta2ecore_ch09.md`
- **Description**: Determination gain/spend logic based on Values and Directives.
- **Entities Involved**:
  - `Value` (Entity): Linked to Character, used for Determination gain.
  - `Determination` (Entity): Sub-entity of Character, tracks current/max.
- **Technical Needs**:
  - Logic for Determination gain (challenging/complying with values).
  - UI for Value management (linked to Character entity).
- **Status**: Covered in M4 (Character CRUD) but mechanics might need explicit implementation.

### 5. Equipment & Items System
- **Source**: `sta2ecore_ch06.md`
- **Description**: Opportunity costs, Escalation costs, Standard Issue gear.
- **Entities Involved**:
  - `Item` (Entity): Properties include `opportunity_cost`, `escalation_cost`.
  - `Character` (Entity): Links to Items via inventory.
- **Technical Needs**:
  - Item database with costs (Opportunity X, Escalation Y).
  - Logic for obtaining items (Momentum/Threat spend via Resource Pool).
- **Status**: Covered in M4 (Character/Ship CRUD) via "Items/Equipment" object.

## Proposed Milestones (M8+)

### Milestone 8: Test Cleanup & Investigation
- **Goal**: Investigate and fix remaining 28 skipped tests
- **Status**: Pending investigation
- **Duration**: 1-2 days

### Milestone 9: Advanced Conflict Systems
- **Goal**: Implement Social Conflict and Extended Tasks.
- **Features**:
  - Social Conflict UI (Opposed tasks, persuasion) linked to `Social Encounter` entity.
  - Extended Task UI (Progress tracks, Breakthroughs) linked to `Extended Task` entity.
  - Hazard Severity/Damage calculator (using `Injury` entity properties).
- **Duration**: 5-7 days.
- **Entities**: `Social Encounter`, `Extended Task`, `Injury`.

### Milestone 10: NPC & Creature Systems
- **Goal**: Implement full NPC generation and Creature rules.
- **Features**:
  - NPC Category logic (Minor/Notable/Major) via `NPC Category Logic` entity.
  - Creature Special Rules engine (using `Trait` entity).
  - NPC Creation API/UI (managing `NPC` entity properties).
- **Duration**: 5-7 days.
- **Entities**: `NPC`, `NPC Category Logic`, `Trait`.

### Milestone 11: GM Tools & Scene Logic
- **Goal**: Enhance GM control over scenes and resources.
- **Features**:
  - Scene Transition Logic (Connected scenes) via `Scene` entity.
  - Threat Pool Management UI (linked to `Resource Pool` entity).
  - Extended Task visualizer for GM (linked to `Extended Task` entity).
- **Duration**: 5-7 days.
- **Entities**: `Scene`, `Resource Pool`, `Extended Task`.

### Milestone 12: Beta & Polish
- **Goal**: Refine UI/UX and prepare for release.
- **Features**:
  - Performance optimization (database indexes on entity IDs).
  - Mobile responsiveness check (UI for entity management).
  - User documentation (covering entity relationships).
- **Duration**: 7-10 days.

## Implementation Notes
- All new milestones should follow the existing workflow (brainstorming -> writing-plans -> implementation).
- Use `opencode/minimax-m2.5-free` for implementation.
- Ensure compatibility with existing database schema (M1) and entity definitions in `/docs/tasks/future/`.
- Update `docs/learnings_and_decisions.md` after each milestone.
