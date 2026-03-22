# Milestone 10 Tasks - UX & Rule-Adherent Implementation Guide

## Overview
This document provides detailed, rule-compliant specifications for Milestone 10 - the comprehensive UX overhaul focusing on player/GM resource transparency, dice roll visualization, dynamic encounter management, and guided character creation.

**Critical**: Agents implementing these tasks MUST understand the STA 2E rules embedded here. The python-dev agents do not have access to the rulebook files, so this document serves as their complete reference.

---

## Branch Information
- **Feature Branch:** `feature/m10-page-structure-ux`
- **Base Branch:** `main`
- **Model:** `opencode/minimax-m2.5-free`

---

## Status: 📋 Planned (Detailed Implementation Guide)

---

## STA 2E Rules Reference (Required Reading for Implementation)

### Core Dice Mechanics
```
Target Number = Attribute + Discipline
- Roll d20, result <= Target Number = 1 Success
- Roll of 1 = 2 Successes (Critical Success - always applies)
- Roll <= Discipline Value = 2 Successes (when Focus applies)
- Complications occur on rolls >= (21 - Complication Range)
  - Default: Range 1 = only 20 causes complication
  - Range 2 = 19-20 cause complications
  - Max Range: 5
```

### Player Resources (STA 2E Ch 7, 8)
| Resource | Max | Start | Reset |
|----------|-----|-------|-------|
| Stress | Equal to Fitness attribute | Fitness | Between scenes |
| Determination | 3 | 1 | Each mission |
| Momentum | 6 | 0 | Between sessions |

### Value Mechanics (STA 2E Ch 4, 7)
**Values** are core character beliefs that drive story and mechanics:
- **Used**: A Value can be invoked once per session (costs 1 Determination as per rules)
- **Challenged**: When a Value conflicts with immediate goals → gain 1 Determination
- **Complied**: When a Value aligned with goals but阻碍 progress → gain 1 Determination
- Players must define **at least 2 Values** during character creation

### Determination Spends (STA 2E Ch 7)
| Spend | Timing | Effect |
|-------|--------|--------|
| **Moment of Inspiration** | After rolling | Re-roll any number of d20s |
| **Perfect Opportunity** | Before rolling | Set 1 die to 1 (Critical Success) |

### Traits (STA 2E Ch 4, 7)
- **Traits** modify task Difficulty or Complication Range
- Applied via Scene/Encounter context (e.g., "Dark Environment" = +1 Difficulty)
- GM assigns Traits to scenes; these affect the Dice Roll Interface

### Action Resolution Sequence (STA 2E Ch 7)
```
1. Player selects Attribute + Department → calculates Target Number
2. GM may apply Traits → modifies Difficulty/Complication Range
3. Player rolls d20s (base 2 + bonus dice from Momentum/Threat)
4. Calculate base successes and complications
5. Apply modifiers (Talents grant re-rolls, Critical Success, complication range changes)
6. Present outcome → Player spends Momentum/Determination/Marks Value usage
```

### Character Creation Flow (STA 2E Ch 4)
The rulebook uses specific terminology:
1. **Foundation**: Define Attributes (7-12) and Species (Racial trait)
2. **Specialization**: Define Department Ratings (1-5) and select Talents
3. **Identity**: Create Values (minimum 2) and Directives
4. **Equipment**: Assign Items, Weapons, and Ship Systems (if applicable)

---

## Implementation Plan Status

| Order | Task Description | Status | Agent Type | Rule Reference |
| :---: | :--- | :---: | :--- | :--- |
| 1 | Deprecate standalone encounter creation | ⏳ Pending | `python-dev` | Encounters derive from Scenes |
| 2 | Extend Scene editor with encounter config | ⏳ Pending | `python-dev` | Traits for Difficulty/Complication |
| 3 | Wire encounter_config_json through activation | ⏳ Pending | `python-dev` | Scene → Encounter data flow |
| 4 | Update Scene editor UI (ships, participants, config) | ⏳ Pending | `python-dev` | UI for Trait assignment |
| 5 | Update campaign dashboard to show scene-derived encounters | ⏳ Pending | `python-dev` | Derived vs standalone |
| 6 | **Player Console UI - Dice Roll Interface** | ⏳ Pending | `python-dev` | Full dice visualization |
| 7 | **GM Console UI - Control & Feedback** | ⏳ Pending | `python-dev` | Threat spending, resource tracking |
| 8 | **Dynamic Round Tracker** | ⏳ Pending | `python-dev` | "Action Taken" status (no fixed turn order) |
| 9 | **Character Sheet - Narrative Tab** | ⏳ Pending | `python-dev` | Values, Logs, Persistence |
| 10 | **Guided Creation Flow** | ⏳ Pending | `python-dev` | Foundation→Identity→Equipment |
| 11 | Action Resolution Logic | ⏳ Pending | `python-dev` | Roll → Calculate → Apply Modifiers |
| 12 | Legacy field cleanup | ⏳ Pending | `python-dev` | Deprecation cleanup |
| 13 | Tests and verification | ⏳ Pending | `python-dev` | Full coverage required |

---

## Detailed Task Specifications

### Task M10.6: Player Console UI & Dice Roll Interface
**Agent**: `python-dev`
**Estimated Time**: ~8 hours
**Rules Context**: STA 2E Ch 5 (Task Resolution), Ch 7 (Determination, Momentum, Traits)

#### Requirements:

**A. Dice Roll Interface (Primary Feature)**
Create a sidebar/modal that visually replicates LCARS styling with these sections:

1. **Input Section**:
   - Dropdown for **Attribute** selection: Control, Daring, Fitness, Insight, Presence, Reason
   - Dropdown for **Department** selection: Command, Conn, Engineering, Medicine, Science, Security
   - **Auto-calculate Target Number**: Display as `Target: [Attribute] + [Department] = [TOTAL]`
   - Optional **Focus** toggle (if character has applicable focus)
   - **Difficulty Display**: Show current Difficulty (base 1, modified by Traits)

2. **Output Section** (shows after roll):
   - **Dice Visualization**: Display individual d20 results, e.g., `[4, 19, 12]`
   - **Successes**: Show count with breakdown (normal + criticals from 1s + focus crits)
   - **Complications**: Show count with current Complication Range indicator
   - **Momentum Generated**: Calculate based on `successes - difficulty` (minimum 0)

3. **Actions Section**:
   - **Roll Button**: Triggers roll with visual animation
   - **Re-roll Option**: "Spend 1 Determination (Moment of Inspiration)" - re-roll selected dice
   - **Critical Option**: "Spend 1 Determination (Perfect Opportunity)" - set one die to 1
   - **Momentum Spend**: Standard Momentum options (re-roll single die: 1 Momentum, buy extra die: 2 Momentum, etc.)

4. **GM Threat Integration**:
   - Display **GM Threat Buttons**: GM can click to add Difficulty or extend Complication Range
   - Show cost in Threat (e.g., "+1 Difficulty costs 2 Threat")

5. **Trait Context**:
   - Display current **Active Traits** affecting this task
   - Show how Traits modify Difficulty and Complication Range

**B. Player Resource Display**
Create visible meters in the console:

1. **Stress Track**:
   - Visual progress bar (0 to max, where max = Fitness attribute)
   - Color coding: Green (safe), Yellow (half), Red (near max), Flashing (Fatigued)
   - Display current/max: `Stress: 3/8`
   - Click to "Suffer Stress" as alternative to consequences

2. **Determination Display**:
   - Show current Determination (starts at 1, max 3)
   - Distinct visuals for each point
   - Clear indication when Determination is spent

3. **Value Interaction Panel**:
   - List all character Values with status badges
   - Each Value shows: **Active** (available), **Used** (once/session), **Challenged** (gained Det), **Complied** (gained Det)
   - Click Value → Options: "Use" (spend Determination) OR "Mark Challenged/Complied" (gain Determination)
   - Input field to add description when Challenging/Complying

**C. Backend Requirements**
- API endpoint: `POST /api/characters/{id}/roll` accepting Attribute, Department, Focus, Difficulty, ComplicationRange
- API endpoint: `POST /api/characters/{id}/spend-determination` for re-rolls/crits
- API endpoint: `POST /api/characters/{id}/value-interaction` to update Value status and track session limits
- Session tracking for Value "Used" status (reset each session)

---

### Task M10.7: GM Console UI Overhaul
**Agent**: `python-dev`
**Estimated Time**: ~4 hours
**Rules Context**: STA 2E Ch 9 (Threat, GM Resources), Ch 11 (NPCs)

#### Requirements:

**A. Threat Control Panel**
Create a dedicated panel with quick-access buttons:

1. **Threat Display**:
   - Current Threat pool (campaign-wide)
   - Standard max: 24

2. **Spend Buttons** (with Threat cost):
   - **Apply Trait**: 1-3 Threat (modifies Difficulty/Complication Range)
   - **Reinforce Scene**: 1-2 Threat (add Minor/Notable NPCs)
   - **Introduce Hazard**: 2 Threat (environmental hazard affecting players)
   - **Reversal**: 2 Threat (turn success into partial success/complication)
   - **NPC Complications**: 2 Threat (buy off player-triggered complications)
   - **Extended Task Progress**: 1 Threat (advance clock)

3. **Gain Buttons** (reduce Threat):
   - **Claim Momentum**: Convert 2 Momentum to 1 Threat

**B. Player Resource Feedback**
Real-time display showing:

1. **Active Players Panel**:
   - List all player characters in scene
   - Show each player's current Stress, Determination status
   - **Value Status Icons**:
     - ✅ = Available
     - 🔶 = Used (this session)
     - 💎 = Challenged (gained Determination)
     - 💠 = Complied (gained Determination)

2. **Event Log**:
   - Auto-feed showing player actions
   - Highlight Determination spends with gold border
   - Track Value interactions (show who challenged/complied which Value)

**C. Scene Trait Editor**
- Add/remove Traits that modify Difficulty/Complication Range
- Quick-select common traits with preset effects

---

### Task M10.8: Dynamic Round Tracker
**Agent**: `python-dev`
**Estimated Time**: ~3 hours
**Rules Context**: STA 2E Ch 7 (Rounds, Initiative) - No fixed turn order in 2E

#### Requirements:

**A. Round Structure** (STA 2E uses fluid initiative, not fixed order):
1. Track Round number (increments when GM starts new round)
2. Each participant has **"Action Taken"** status (boolean)
3. Status resets at start of new Round
4. GM controls when to mark "Action Taken" after resolution

**B. UI Components**:
1. **Round Counter**: Display "Round 3" prominently
2. **Participant List**:
   - Grouped by side (Players vs. NPCs/Opposition)
   - Each shows: Name, Status badge ("Ready" / "Action Taken")
   - Color coding: Green = Ready, Gray = Action Taken
3. **Start Round Button**: Resets all "Action Taken" to Ready
4. **Toggle Action Button**: GM clicks to mark participant's action complete

**C. Edge Cases**:
- If all PCs have "Action Taken" but NPCs haven't → highlight for GM
- "Keep the Initiative" variant: Can flag a participant as "Going Next" for visual ordering (optional display, not mechanical requirement)

---

### Task M10.9: Character Sheet Narrative Tab
**Agent**: `python-dev`
**Estimated Time**: ~5 hours
**Rules Context**: STA 2E Ch 4 (Values, Personal Logs)

#### Requirements:

**A. Values Section** (Primary Feature):
1. **Display All Values**:
   - Name of Value + description
   - Status badge: Available / Used / Challenged / Complied
   - Last interaction timestamp

2. **Interaction Controls**:
   - "Mark Used" button (max once per session)
   - "Mark Challenged" button (gain 1 Determination, enter description)
   - "Mark Complied" button (gain 1 Determination, enter description)
   - Modal for description: "Why is this Value being challenged/complied?"

**B. Personal Logs** (New Feature):
1. **Text Area**: Rich text input for character roleplay/flashback
2. **Visibility**: **ALL OTHER PLAYERS can read** (not just GM)
3. **Purpose**: Share character perspective, backstory snippets, mission notes

**C. Mission/Value Logs** (Auto-generated):
1. **Trigger Events**:
   - Scene Activation: Auto-create log entry with scene name
   - Scene Completion: Mark completion timestamp
   - Value Interaction: Create entry when Value is used/challenged/complied
2. **Structure**:
   - Timestamp
   - Event type (Scene Enter, Scene Exit, Value Challenged, etc.)
   - Character name involved
   - Optional player-added description (up to 280 characters)

**D. Backend Requirements**:
- `CharacterValue` model extended with: status enum, last_session_used, interaction_count
- `LogEntry` model: id, character_id, type, content, timestamp, created_by
- Personal log visibility query: All players in campaign EXCEPT owner can read

---

### Task M10.10: Guided Creation Flow
**Agent**: `python-dev`
**Estimated Time**: ~6 hours
**Rules Context**: STA 2E Ch 4 (Character Creation)

#### Requirements:

**A. Character Wizard - 4 Steps**:

**Step 1: Foundation**
- **Species Selection**: Dropdown with common species (Human, Vulcan, Andorian, etc.) - each adds a trait
- **Attribute Assignment**:
  - 6 attributes: Control, Daring, Fitness, Insight, Presence, Reason
  - Starting distribution: 7-12 range, total sum typically 42-52
  - Suggested: Use point buy (27 points across 6 attrs, 7-12 range)
- **Background Info** (optional): Environment, Upbringing, Career Path

**Step 2: Specialization**
- **Department Ratings**:
  - 6 departments: Command, Conn, Engineering, Medicine, Science, Security
  - Range: 1-5, each main character must have at least 1
  - Distribute 15 points across departments
- **Focus Selection**: Choose 3-4 focuses relevant to departments
- **Talents**: Select from available talent pool (filtered by prerequisites)

**Step 3: Identity** (Critical - Value Mechanics)
- **Values Creation**:
  - Minimum 2 Values required
  - Pre-defined list + custom option
  - Each Value must have name + brief description (e.g., "Logic Above All - I trust in rational analysis over emotions")
  - Tag each Value as potentially "Helpful" or "Problematic" for Determination tracking
- **Directives** (optional): Character-specific mission statements

**Step 4: Equipment**
- **Personal Items**: Add equipment from inventory list
- **Weapons** (if Security focus): Sidearm type
- **Rank Assignment**: Starting Starfleet rank

**B. Ship Wizard** (If character is ship's commanding officer):
- **Scale Selection**: Ship size class
- **System Ratings**: 6 ship systems (Communications, Computers, Engines, Sensors, Structure, Weapons) - range 0-5
- **Department Ratings**: Ship departments - range 0-5
- **Crew Quality**: Typically equals sum of key crew departments
- **Traits**: Add ship-specific traits (Federation Starship, Ship Class, etc.)

**C. Validation Rules**:
- Cannot proceed to next step without completing required fields
- At least 2 Values must be defined (enforced)
- Stress max = Fitness attribute (auto-calculated)
- Determination starts at 1 (per rules)

---

### Task M10.11: Action Resolution Logic
**Agent**: `python-dev`
**Estimated Time**: ~2 hours (Logic Design)
**Rules Context**: STA 2E Ch 5, 7 (Task Resolution)

#### Requirements:

**Implement this exact sequence in backend**:

```python
def resolve_action(attribute, discipline, difficulty, complication_range, 
                  focus_applies, talent_modifiers, bonus_dice=0):
    """
    STA 2E compliant action resolution.
    
    Sequence:
    1. Calculate Target Number (Attribute + Discipline)
    2. Roll dice (2 base + bonus dice)
    3. Calculate base successes from dice
    4. Calculate complications from dice
    5. Apply talent/ability modifiers (re-rolls, crits, complication range changes)
    6. Determine final outcome
    7. Calculate Momentum generated
    """
    
    # Step 1: Calculate Target Number
    target_number = attribute + discipline
    focus_value = discipline if focus_applies else None
    
    # Step 2: Roll dice
    total_dice = 2 + bonus_dice
    rolls = roll_d20(total_dice)
    
    # Step 3: Base successes (before modifiers)
    base_successes = count_successes(rolls, target_number, focus_value)
    base_complications = count_complications(rolls, complication_range)
    
    # Step 4: Track re-rolls from talents (these replace original dice)
    final_rolls = apply_talent_rerolls(rolls, talent_modifiers)
    
    # Step 5: Calculate with modified rolls
    final_successes = count_successes(final_rolls, target_number, focus_value)
    final_complications = count_complications(final_rolls, complication_range)
    
    # Step 6: Apply special talent effects (Critical Success conversion, etc.)
    final_successes = apply_talent_crits(final_successes, talent_modifiers)
    
    # Step 7: Determine outcome
    succeeded = final_successes >= difficulty
    momentum = max(0, final_successes - difficulty) if succeeded else 0
    
    return TaskResult(
        rolls=final_rolls,
        target_number=target_number,
        difficulty=difficulty,
        complication_range=complication_range,
        successes=final_successes,
        complications=final_complications,
        momentum_generated=momentum,
        succeeded=succeeded
    )
```

**Important Distinctions**:
- **Re-rolls** (Moment of Inspiration, talents): Replace the original dice with new rolls
- **Critical Success conversion** (Perfect Opportunity, talents): Set a die to 1 - this is a guaranteed 2 successes
- **Complication Range modification**: Happens BEFORE roll calculation, affects threshold for what counts as complication

---

### Task M10.12: Legacy Field Cleanup
**Agent**: `python-dev`
**Requirements**:
- Remove standalone encounter creation endpoints (only scenes create encounters now)
- Deprecate old encounter-related fields in schema
- 301 redirect old URLs to new scene-based URLs

---

### Task M10.13: Tests and Verification
**Agent**: `python-dev`
**Requirements**:
- Write comprehensive tests for:
  - Dice roll mechanics (success counting, criticals, complications)
  - Value interaction (Used/Challenged/Complied status changes)
  - Determination spends (re-roll, critical)
  - Guided creation wizard flow (all 4 steps)
  - Round tracker state transitions
  - Personal log visibility (all players EXCEPT owner)
- Run full test suite before submission
- Target: 100% coverage for new features

---

## Future Task Deferral

**Spectator View**: Moved to Milestone 13 to prioritize core gameplay loop stability.

Reference: `docs/tasks/future/roadmap_proposal.md`

---

## Subagent Prompts for Parallel Execution

### Agent 1: Backend Structure (Scene/Encounter Wiring)
```
task(
    description="Scene-Encounter Wiring & Legacy Cleanup",
    prompt="Execute Tasks M10.1, M10.2, M10.3, M10.4, M10.12.\n\nFOCUS:\n1. Deprecate standalone encounter creation - scenes derive encounters\n2. Wire encounter_config_json from scene activation into EncounterRecord\n3. Implement Scene API supports Trait storage (for Difficulty/Complication modification)\n4. Add Value session tracking to Character model (Used status per session)\n5. Clean up legacy encounter fields after migration\n\nRULES REFERENCE:\n- Traits: Scene.Traits array modifies task Difficulty/Complication Range\n- Values: Each character needs 'used_this_session' flag per Value\n- Encounters now derive from Scenarios, not standalone creation\n\nCreate tests for Scene→Encounter derivation and Value session tracking.",
    subagent_type="python-dev",
    model="opencode/minimax-m2.5-free"
)
```

### Agent 2: Player Console & Dice Interface
```
task(
    description="Player Dice Roll Interface",
    prompt="Execute Task M10.6 - Player Console & Dice Roll Interface.\n\nREQUIRED IMPLEMENTATION:\n\nA. DICE ROLL INTERFACE:\n- Input: Attribute (Control/Daring/Fitness/Insight/Presence/Reason) + Department (Command/Conn/Engineering/Medicine/Science/Security)\n- Calculate Target Number = Attribute + Discipline\n- Display rolled dice individually: [4, 19, 12]\n- Show successes: normal (roll <= TN) + criticals (roll=1 always 2 successes) + focus crits (roll <= focus value = 2 successes)\n- Show complications: based on Complication Range (default 1 = only 20)\n- GM Threat buttons to increase Difficulty (costs Threat)\n\nB. PLAYER RESOURCES:\n- Stress meter: 0 to max (max = Fitness)\n- Determination: start 1, max 3\n- Value panel: Each Value shows status (Available/Used/Challenged/Complied)\n- Value interaction: 'Use' (once/session), 'Challenged' (gain Det), 'Complied' (gain Det)\n\nC. BACKEND:\n- POST /api/characters/{id}/roll\n- POST /api/characters/{id}/value-interaction (update Value status)\n\nRULES: \n- Target = Attribute + Discipline\n- Roll <= TN = 1 success, Roll = 1 = 2 successes, Roll <= Focus value = 2 successes\n- Complication Range 1 = 20 causes complication, Range 2 = 19-20, etc.\n- Determination: Start 1, Max 3, spend for re-roll or set die to 1\n- Value Used: Once per session, allows Determination spend\n\nInclude tests for dice counting, Value status transitions.",
    subagent_type="python-dev",
    model="opencode/minimax-m2.5-free"
)
```

### Agent 3: GM Console & Round Tracker
```
task(
    description="GM Console & Dynamic Round Tracker",
    prompt="Execute Tasks M10.7 and M10.8.\n\nTASK M10.7 - GM CONSOLE:\n1. Threat Panel:\n   - Display current Threat (campaign pool, max 24)\n   - Spend buttons: Trait (1-3), Reinforcement (1-2), Hazard (2), Reversal (2), NPC Complications (2)\n   - 'Claim Momentum' button: Convert 2 Momentum to 1 Threat\n\n2. Player Resource Feedback:\n   - List all PCs showing Stress/Determination/Value status\n   - Value status icons: Available, Used, Challenged (gained Det), Complied (gained Det)\n   - Auto-log Determination spends and Value interactions\n\nTASK M10.8 - DYNAMIC ROUND TRACKER:\n1. Round counter (displays current Round#)\n2. Participant list with 'Ready'/'Action Taken' toggle\n3. 'Start New Round' button resets all Action Taken to Ready\n4. GM clicks participant to toggle action status after resolution\n\nRULES:\n- No fixed turn order in STA 2E - fluid initiative\n- 'Action Taken' status tracks who has acted this round\n- Reset at start of new Round\n\nBackend: API to toggle participant action status, track round number, auto-reset on new round.\n\nInclude tests for Threat spending, round status transitions.",
    subagent_type="python-dev",
    model="opencode/minimax-m2.5-free"
)
```

### Agent 4: Narrative Tab & Creation Wizard
```
task(
    description="Narrative Tab & Guided Creation",
    prompt="Execute Tasks M10.9 and M10.10.\n\nTASK M10.9 - CHARACTER SHEET NARRATIVE TAB:\nValues Section:\n- Display all character Values with status badges\n- Each Value: 'Mark Used' (once/session), 'Mark Challenged' (gain Determination), 'Mark Complied' (gain Determination)\n- Modal to add description: 'Why is this Value being challenged/complied?'\n\nPersonal Logs:\n- Text area for character roleplay notes\n- VISIBILITY: ALL OTHER PLAYERS can see (not just owner/GM)\n\nMission/Value Logs:\n- Auto-generate entries on: Scene Activation, Scene Completion, Value interaction\n- Structure: timestamp, event_type, character, description\n\nTASK M10.10 - GUIDED CREATION FLOW:\n\nCharacter Wizard (4 steps using STA 2E terminology):\n1. FOUNDATION: Attributes (7-12, total ~42-52), Species (adds trait)\n2. SPECIALIZATION: Department ratings (1-5, total 15 pts), Talents, Focuses\n3. IDENTITY: Values (MINIMUM 2 required per rules), Directives\n4. EQUIPMENT: Items, Weapons, Rank\n\nShip Wizard (if applicable):\n- Scale selection, System ratings (0-5), Department ratings (0-5)\n\nValidation: Cannot proceed without required fields, enforce 2+ Values.\n\nBackend:\n- LogEntry model: id, character_id, type (PERSONAL/MISSION/VALUE), content, timestamp\n- Character creation API: 4-step form submission\n\nRULES:\n- Each Value can be Used once per session to spend Determination\n- Challenging/Complying a Value grants 1 Determination\n- Stress max = Fitness attribute\n- Determination starts at 1, max 3\n\nInclude tests for Value status, log visibility (player can see others' personal logs), creation flow validation.",
    subagent_type="python-dev",
    model="opencode/minimax-m2.5-free"
)
```

### Agent 5: Action Resolution Logic & Full Test Suite
```
task(
    description="Action Resolution Logic Implementation",
    prompt="Execute Task M10.11 - implement exact resolution sequence.\n\nREQUIRED SEQUENCE (STA 2E COMPLIANT):\n\n1. Calculate Target Number = Attribute + Discipline\n2. Roll 2d20 + bonus dice from Momentum/Threat\n3. Calculate base successes (roll <= TN = 1, roll=1 = 2, roll<=focus=2)\n4. Calculate base complications based on Complication Range\n5. Apply MODIFIERS (Talents/Abilities AFTER initial calculation):\n   - Re-rolls (Moment of Inspiration): Replace specified dice with new rolls\n   - Set die to 1 (Perfect Opportunity): Guaranteed 2 successes on chosen die\n   - Critical Success conversion: Some talents auto-turn success into critical\n   - Complication Range adjustment: Some talents reduce complications\n6. Present final outcome\n7. Calculate Momentum generated = max(0, successes - difficulty)\n\nImplement in `sta/mechanics/dice.py`:\n- Extend existing task_roll() function\n- Add apply_talent_modifiers() function\n- Handle re-roll logic correctly (replacement, not addition)\n\nAlso complete:\n- All unit tests for M10.1-M10.11\n- Integration tests for resource flows\n- Tests for Guided Creation wizard\n- Dice resolution with various edge cases (all 1s, all 20s, focus crits, re-rolls, etc.)\n\nRun full pytest suite - target 100% coverage on new features.\n\nVerify no regressions before submission.",
    subagent_type="python-dev",
    model="opencode/minimax-m2.5-free"
)
```

---

## Verification Commands

Before submitting completion feedback, run:

```bash
# Install dependencies
uv venv && uv pip install -r requirements.txt -r requirements-dev.txt

# Run full test suite
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=sta tests/
```

All tests must pass before marking tasks complete.