# Talent System Design

This document describes the data model design for Talent objects and related rule-carrying entities in the STA Starship Simulator VTT.

## 1. Overview

The game needs to represent several categories of rule-bearing entities that modify or trigger game mechanics. These include Talents, Special Rules, Species Abilities, and Role Benefits. A unified approach allows:

- Storing rule metadata alongside character/ship data
- Future extensibility toward automated rule execution
- Clear separation between descriptive text and mechanical references
- GM override capability at every level

---

## 2. Validation of User Responses

Before designing the models, the following Q&A responses from `docs/m8.2-open-questions.md` were validated against the rulebook:

### Q1: Ship Stress/Shields/Breaches (Ch 5, 8)

**User Response**: Ships have a shields track (derived from Structure + Scale + Security), Resistance, and Breaches. Ships handle a number of breaches equal to their Scale in total, OR to a single system equal to half their Scale (whichever is smaller).

**Validation**: ✅ **VALIDATED**
- Ch05 (line 629): "A ship has shields equal to its Structure plus its Scale and Security."
- Ch05 (lines 565-610): Resistance = half Scale (round up) + Structure bonus (see Resistance table).
- Ch08 (lines 1160-1172): Breach rules — if shields at 0, ship suffers a breach. Ship is destroyed after suffering more breaches than its Scale in total, OR more breaches to one system than half its Scale.
- The "Shaken" Ship Trait (minor damage result) is confirmed in Ch08 (line 1114).

**Clarification**: "Ship Stress" does not exist in the 2e rules — ships use Shields (depletion track) and Breaches (system damage). The character's Fitness-based Stress track is PC-only.

### Q2: Initiative Keeping (Ch 7, 8)

**User Response**: Look this up in Ch08.3 under "Prepare for Combat".

**Validation**: ✅ **VALIDATED**
- Ch07 (lines 266-267): "After taking a turn in an action scene... a character may choose to Keep the Initiative. To Keep the Initiative... spend 2 Momentum... hand the action to another character on your own side."
- Ch07 (line 389): "Keep The Initiative: Pass the order of play to an ally, rather than an enemy, for 2 Threat." — NPC version.
- Ch08.1 (lines 28-29): Confirms 2 Momentum (Immediate) cost for personal conflict.
- Ch08.4 (line 506): "Keep The Initiative (2 Momentum, Immediate)" confirmed for starship combat — same cost applies across all conflict types.
- **Scope**: Applies to Personal, Social, and Starship conflict. Cost is always 2 Momentum (Immediate), or 2 Threat for NPCs.

### Q3: NPC Stress/Determination (Ch 8, 11)

**User Response**: Supporting Characters receive a Stress Track and Determination with their first Value. Major and Notable NPCs have a Stress Track, Minor ones do not. NPCs can have Personal Threat pools.

**Validation**: ✅ **VALIDATED**
- Ch08.1 (lines 50-59): "A supporting character who has one value has maximum Stress equal to half their Fitness (rounded up). A supporting character with two or more values has maximum Stress calculated as if they were a main player character." "NPCs do not have Stress." "Notable and Major NPCs may spend Threat to avoid negative consequences."
- Ch11.1 (lines 73-88): Personal Threat pools — Notable NPCs typically have 3, Major NPCs 6 or more. Notable NPCs may Avoid Injury once per scene by spending Threat equal to severity. Major NPCs may do so unlimited times.
- Ch11.1 (lines 137-151): NPC injury rules confirmed — Minor NPCs are instantly defeated; Notable once per scene; Major unlimited.

### Q4: Reinforcement Cost (Ch 9)

**User Response**: 1 Threat per Scale unit of the new ship.

**Validation**: ✅ **VALIDATED**
- Ch09.1 (lines 709-715): "A starship can be brought in (appearing on long-range sensors, dropping out of warp, or decloaking) by spending Threat equal to the ship's Scale."

### Q5: Task vs. Action (Ch 7, 8)

**User Response**: Tasks are all dice-rolls (including Challenge component tasks). Actions are related to Crew Station on the Bridge during Starship Combat only.

**Validation**: ✅ **VALIDATED**
- Ch07 (lines 261-265): Tasks defined as "any activity where there is doubt in the outcome, where failure or complications are interesting, or where the degree of success is important."
- Ch08.4 (lines 678-720): Bridge stations and position-based actions are explicitly Starship Combat mechanics.

### Q6: NPC Trait Suppression (Ch 11)

**User Response**: Species traits modifying Stress/Determination should NOT be automatically suppressed. Notify GM of such abilities. Allow GM overwrite.

**Validation**: ✅ **VALIDATED**
- Ch11.1 (lines 281-282, 305-307, 384-386): For Minor, Notable, and Major NPCs: "if the special rule relates to Stress or Determination, it doesn't apply to NPCs."
- **Clarification**: The rules DO suppress these for NPCs. However, the user's preference is to keep them visible but flag them for GM attention, with override capability. This is a UX design decision beyond the rules — we will follow the user's preferred approach.

---

## 3. Talent Object Design

### 3.1 Core Model Fields

Each rule-bearing entity (Talent, Special Rule, Species Ability, Role Benefit) shares a common structure:

```
Talent:
  name: str              # Display name, e.g., "Intense", "Vulcan Nerve Pinch"
  description: str       # Human-readable rules text
  category: enum        # Talent | SpecialRule | SpeciesAbility | RoleBenefit
  conditions: list[str]  # When/under what circumstances this is active
  game_mechanic_reference: str  # Handler ID or predicate (Phase 1: string; Phase 2: predicate)
  applicable_to: enum   # Character | Ship | NPC
  source: str            # e.g., "Betazoid", "Security Department", "Section 31 Operative"
  mechanically_applies: bool  # True = auto-apply; False = GM discretion / flag for review
```

### 3.2 Categories

| Category | Description | Examples |
|---|---|---|
| **Talent** | Player-selectable character abilities | "Renowned", "Spirit of the Adventure" |
| **SpecialRule** | NPC/creature rules, often limiting | "PROFICIENCY: Security tasks, first d20 free" |
| **SpeciesAbility** | Inherited from species, auto-granted | "Telepathic", "Intense" (Andorian) |
| **RoleBenefit** | Granted by character role | Department-based bonuses |

### 3.3 Conditions

Conditions are stored as human-readable strings. Each condition is self-contained:

Examples:
- `"When succeeding at a task where you purchased d20s by adding to Threat"`
- `"When in personal combat"`
- `"When the NPC attempts a particular task"`
- `"Against Klingon species"`

**Phase 1** (immediate): Conditions are stored as plain strings. Code checks whether a condition applies by pattern-matching against game state (e.g., string contains "combat" → check if scene is combat).

**Phase 2** (future): Conditions evolve into a predicate language:

```python
# Example predicate grammar (Phase 2 target)
condition = {
    "type": "AND",
    "predicates": [
        {"type": "context", "value": "in_combat"},
        {"type": "attacking_with", "weapon_type": "phaser"},
        {"type": "target_species", "equals": "Klingon"},
    ]
}
```

This allows programmatic evaluation rather than string parsing.

### 3.4 Game Mechanic Reference

The `game_mechanic_reference` field is a string identifier linking to a code handler:

**Phase 1**: Use string IDs for known mechanics.
```
game_mechanic_reference: "bonus_d20_on_threat_spend"   # Andorian Intense
game_mechanic_reference: "stress_modifier:+1"           # Future modifier example
game_mechanic_reference: "reduce_difficulty:2"          # Familiarity special rule
game_mechanic_reference: "free_first_d20"               # PROFICIENCY special rule
```

**Phase 2**: Evolve to a structured predicate/command language that handlers can parse:

```python
# Example handler payload
{
    "handler": "conditional_bonus",
    "trigger": {"type": "AND", "predicates": [...]},
    "effect": {"type": "bonus_d20", "cost": "threat", "free_first": true}
}
```

### 3.5 Stress Track Modification

Some Species Abilities (e.g., Betazoid Resilience variants, or homebrew rules) may modify a character's maximum Stress. This must be represented in the Talent model:

```
Talent:
  ...
  stress_modifier: int | None   # e.g., +1 or -1 to max Stress
  notify_gm_on_apply: bool       # Always True for Stress-modifying abilities
```

**Character Creation Workflow**:
1. Character selects species → Species Ability auto-granted
2. System checks if `stress_modifier` is set on any granted Talent
3. If yes, display a notification to the GM: "This character has a Species Ability that modifies Stress."
4. GM can override the Stress modifier (increase, decrease, or zero it out)
5. Final Stress max is stored on the character record, decoupled from the Talent

---

## 4. Special Rules for NPCs

### 4.1 Model

```
SpecialRule:
  name: str
  description: str
  category: "SpecialRule"
  conditions: list[str]      # e.g., ["When performing a particular task"]
  particular_task: str        # The limiting task description from Ch11 (e.g., "Security tasks")
  game_mechanic_reference: str  # e.g., "free_first_d20", "reduce_difficulty:2"
  applicable_to: "NPC"
```

### 4.2 Ch11 Special Rules

The following special rules from Ch11 require implementation:

| Rule | Effect | Mechanic Reference |
|---|---|---|
| ADDITIONAL THREAT SPENT | Spend 1 Threat for specific/unique benefit on particular department task | `threat_spend_bonus` |
| CONCEPT | Defines NPC role — descriptive only | None |
| FAMILIARITY | Reduce Difficulty by 2 (min 0) on particular task | `reduce_difficulty:2` |
| GUIDANCE | When assisting another NPC in a particular way, re-roll d20 | `assist_reroll` |
| PROFICIENCY | First bonus d20 free on particular task | `free_first_d20` |
| SUBSTITUTION | Use different department or focus on particular task | `department_swap` |
| THREATENING | When buying d20s with Threat on particular task, re-roll 1 d20 | `threat_buy_reroll` |

### 4.3 Condition Format for Special Rules

Per Ch11 (lines 359-362): "when the special rule calls for a 'particular task'... it is asking for a limiting factor to the rule."

**String format (Phase 1)**:
```
"particular_task: Security"
"particular_task: Engineering, when repairing systems"
"particular_task: Presence + Command"
```

**Structured format (Phase 2)**:
```
{
    "type": "task_match",
    "department": "Security",
    "context": ["combat"]
}
```

---

## 5. NPC-Specific Rules

### 5.1 NPC Categories and Rule Differences

| NPC Type | Stress Track | Personal Threat | Avoid Injury | Special Rules |
|---|---|---|---|---|
| **Minor NPC** | None | 0 | Cannot avoid — instant defeat | Yes (from species) |
| **Notable NPC** | None (uses Threat) | 3 | Once per scene, cost = severity | Yes |
| **Major NPC** | None (uses Threat) | 6 + 1 per Value | Unlimited per scene, cost = severity | Yes |
| **Supporting Character** (0 Values) | None | 0 | Cannot avoid | No |
| **Supporting Character** (1 Value) | Fitness ÷ 2 (round up) | 0 | Like PC (Stress) | No |
| **Supporting Character** (2+ Values) | Like Main PC (Fitness) | 0 | Like PC (Stress) | No |

### 5.2 Personal Threat Pools

Notable and Major NPCs have Personal Threat pools:
- **Notable**: Typically 3 Personal Threat (Ch11.1 line 87)
- **Major**: 6 Personal Threat + 1 per Value (Ch11.1 line 352)
- Personal Threat is separate from the GM's campaign Threat pool
- Personal Threat can only be spent on effects affecting that specific NPC
- NPCs may spend from Personal Threat OR GM Threat in any combination
- Personal Threat refreshes at the start of each scene (Ch11.1 line 85)

### 5.3 Crew Quality vs. Assigned NPC

For NPC ships (Ch11.3, lines 191-196):
- NPC ships do NOT track individual bridge crew
- Instead, they use a **Crew Quality** rating for all rolls:

| Crew Quality | Attribute Rating | Department Rating |
|---|---|---|
| Basic | 8 | 1 |
| Proficient | 9 | 2 |
| Talented | 10 | 3 |
| Exceptional | 11 | 4 |

**Decision**: If a player assigns an NPC to a bridge station, use the NPC's own attributes/departments. If no NPC is assigned, use the ship's Crew Quality rating. This must be implemented at the task resolution level.

**Limitation**: In any round, each NPC ship may only attempt one task assisted by each system. The second and third tasks using the same system cost 1 Threat each (Ch11.3, line 274-275).

---

## 6. Implementation Plan

### Phase 1: String-Based Conditions (Immediate)

**Database Schema Additions**:
```sql
-- Add to CharRecord or create Talent/SpecialRule table
ALTER TABLE characters ADD COLUMN talents JSON;
ALTER TABLE characters ADD COLUMN special_rules JSON;
ALTER TABLE characters ADD COLUMN species_ability_override JSON;  -- For GM overrides
```

**Data Model** (Python, Phase 1):
```python
@dataclass
class Talent:
    name: str
    description: str
    category: Literal["Talent", "SpecialRule", "SpeciesAbility", "RoleBenefit"]
    conditions: list[str]                    # Phase 1: string list
    game_mechanic_reference: str | None      # Handler ID string
    applicable_to: Literal["Character", "Ship", "NPC"]
    source: str | None
    stress_modifier: int | None             # For Stress-modifying abilities
    mechanically_applies: bool = True        # False = GM discretion

@dataclass
class SpecialRule:
    name: str
    description: str
    particular_task: str                    # Limiting task description
    game_mechanic_reference: str            # Handler ID
    applicable_to: Literal["NPC"] = "NPC"
```

**Handler Registry Pattern**:
```python
# sta/mechanics/talent_handlers.py
TALENT_HANDLERS: dict[str, Callable] = {
    "free_first_d20": handle_free_first_d20,
    "reduce_difficulty:2": handle_reduce_difficulty_2,
    "bonus_momentum_on_threat": handle_bonus_momentum,
    "stress_modifier": handle_stress_modifier,
    # ...
}

def evaluate_talent(
    talent: Talent,
    context: GameContext,
) -> list[GameEffect]:
    """Phase 1: Simple string-based condition evaluation."""
    if not talent.conditions:
        return [TALENT_HANDLERS[talent.game_mechanic_reference](context)]

    for condition in talent.conditions:
        if matches_condition(condition, context):
            return [TALENT_HANDLERS[talent.game_mechanic_reference](context)]
    return []
```

**Character Creation Hook**:
```python
def apply_character_talents(character: CharacterRecord, gm_overrides: dict) -> None:
    # 1. Auto-apply Species Ability
    species_ability = get_species_ability(character.species)
    if species_ability:
        character.talents.append(species_ability)
        if species_ability.stress_modifier is not None:
            notify_gm(f"Stress modifier detected: {species_ability.name}")
            # Apply GM override if present, otherwise default
            modifier = gm_overrides.get(species_ability.name, species_ability.stress_modifier)
            character.max_stress_modifier = modifier

    # 2. Apply Role Benefits
    role_benefit = get_role_benefit(character.role)
    if role_benefit:
        character.talents.append(role_benefit)

    # 3. Apply player-selected Talents (handled separately)
```

### Phase 2: Predicate Language (Future)

Migrate conditions from strings to structured predicates:

```python
@dataclass
class PredicateCondition:
    type: Literal["context", "task_match", "attacker", "target", "scene_type", "AND", "OR", "NOT"]
    value: Any  # Depends on type
    nested: list["PredicateCondition"] | None  # For AND/OR/NOT

@dataclass
class Talent:
    ...
    conditions: list[str | PredicateCondition]  # Union during migration
    game_mechanic_reference: dict  # Structured handler payload
```

---

## 7. Key Decisions

1. **Unified Talent model** for all rule-bearing entities (Talent, SpecialRule, SpeciesAbility, RoleBenefit) — differentiated by `category` field only. Reduces code duplication and allows a single handler system.

2. **Stress modifiers stored on Talent, final value on Character** — this allows GM overrides without modifying the source-of-truth Talent data.

3. **GM notification system** for Stress-modifying abilities — ensures GMs are aware even if the rules technically suppress such abilities for NPCs.

4. **NPC Personal Threat vs. campaign Threat** — implement as separate pools in the database. Personal Threat is NPC-specific; campaign Threat is GM-wide.

5. **Crew Quality fallback** — NPC ships use Crew Quality unless a specific NPC is assigned to a station. This decision makes the system both simple (default NPC ships) and flexible (player-controlled NPCs override the default).

6. **No automatic suppression** of NPC Stress/Determination abilities — instead, flag them for GM review and allow explicit suppression. This matches the user's preference over the literal rulebook wording.

7. **Phase 1 conditions are strings** — keep the system simple for now. The predicate language is designed for future Phase 2 but the data model must accommodate both during the transition.
