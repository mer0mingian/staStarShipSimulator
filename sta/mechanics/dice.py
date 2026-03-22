"""Dice rolling mechanics for Star Trek Adventures 2nd Edition 2d20 system.

Note: STA 2e does NOT use challenge dice for damage. Weapons have flat damage
ratings that are modified by the ship's Weapons system bonus.

Resolution Sequence (STA 2E Ch 7):
1. Calculate Target Number = Attribute + Discipline
2. Roll 2d20 + bonus dice from Momentum/Threat
3. Calculate base successes (roll <= TN = 1, roll=1 = 2, roll<=focus=2)
4. Calculate base complications based on Complication Range
5. Apply MODIFIERS (Talents/Abilities AFTER initial calculation):
   - Re-rolls (Moment of Inspiration): Replace specified dice with new rolls
   - Set die to 1 (Perfect Opportunity): Guaranteed 2 successes on chosen die
   - Critical Success conversion: Some talents auto-turn success into critical
   - Complication Range adjustment: Some talents reduce complications
6. Present final outcome
7. Calculate Momentum generated = max(0, successes - difficulty)
"""

import random
from dataclasses import dataclass, field
from typing import Optional, Literal

from sta.models.combat import TaskResult


@dataclass
class DiceRoll:
    """Individual die roll with metadata for tracking re-rolls."""

    value: int
    original_index: int
    is_rerolled: bool = False
    reroll_source: Optional[str] = None  # e.g., "Moment of Inspiration"


@dataclass
class TalentModifier:
    """A talent or ability that modifies the dice roll.

    Types of modifiers:
    - REROLL: Replace specific dice with new rolls (Moment of Inspiration)
    - SET_TO_ONE: Set chosen die to 1 for guaranteed critical (Perfect Opportunity)
    - CRITICAL_CONVERSION: Auto-convert success to critical (some talents)
    - REDUCE_COMPLICATIONS: Reduce complication range (some talents)
    """

    modifier_type: Literal[
        "REROLL", "SET_TO_ONE", "CRITICAL_CONVERSION", "REDUCE_COMPLICATIONS"
    ]
    dice_indices: list[int] = field(default_factory=list)  # Which dice to affect
    source_talent: str = ""  # Name of the talent granting this modifier
    complication_reduction: int = 0  # For REDUCE_COMPLICATIONS


@dataclass
class RollModifierResult:
    """Result of applying talent modifiers to a roll."""

    final_rolls: list[int]
    rerolled_indices: list[int]
    dice_set_to_one: list[int]
    criticals_added: int
    complication_range_reduced_by: int
    modifiers_applied: list[str]  # List of talent names that were applied


def roll_d20(count: int = 1) -> list[int]:
    """Roll one or more d20s."""
    return [random.randint(1, 20) for _ in range(count)]


def roll_die(roll_type: str = "d20") -> int:
    """Roll a single die of specified type.

    Args:
        roll_type: Type of die to roll ("d20", "d6", etc.)

    Returns:
        Roll result
    """
    if roll_type == "d20":
        return random.randint(1, 20)
    elif roll_type == "d6":
        return random.randint(1, 6)
    elif roll_type == "d8":
        return random.randint(1, 8)
    else:
        raise ValueError(f"Unknown die type: {roll_type}")


def reroll_die(roll: int) -> int:
    """Reroll a single die, returning the new result."""
    return random.randint(1, 20)


def set_die_to_one() -> int:
    """Set a die to 1 (Perfect Opportunity spend)."""
    return 1


def count_successes(
    rolls: list[int], target_number: int, focus_value: Optional[int] = None
) -> int:
    """
    Count successes from d20 rolls.

    Args:
        rolls: List of d20 roll results
        target_number: Attribute + Discipline (roll at or under = success)
        focus_value: Discipline value when focus applies (rolls at or under = 2 successes)

    Returns:
        Total number of successes

    Rules:
        - Roll <= target_number = 1 success
        - Roll of 1 = 2 successes (always)
        - Roll <= focus_value = 2 successes (when focus applies)
    """
    successes = 0
    for roll in rolls:
        if roll == 1:
            successes += 2
        elif roll <= target_number:
            if focus_value is not None and roll <= focus_value:
                successes += 2
            else:
                successes += 1
    return successes


def count_complications(rolls: list[int], complication_range: int = 1) -> int:
    """
    Count complications from d20 rolls.

    Args:
        rolls: List of d20 roll results
        complication_range: How many numbers from 20 cause complications
            - 1 (default): only 20
            - 2: 19-20
            - 3: 18-20, etc.

    Returns:
        Number of complications generated
    """
    threshold = 21 - complication_range
    return sum(1 for roll in rolls if roll >= threshold)


def task_roll(
    attribute: int,
    discipline: int,
    difficulty: int = 1,
    dice_count: int = 2,
    focus: bool = False,
    bonus_dice: int = 0,
) -> TaskResult:
    """
    Perform a complete task roll.

    Args:
        attribute: Character attribute value (e.g., Control = 9)
        discipline: Character discipline value (e.g., Science = 4)
        difficulty: Number of successes needed
        dice_count: Base number of dice (default 2)
        focus: Whether a relevant focus applies
        bonus_dice: Additional dice from Momentum/Threat

    Returns:
        TaskResult with all roll details
    """
    target_number = attribute + discipline
    focus_value = discipline if focus else None
    total_dice = dice_count + bonus_dice

    rolls = roll_d20(total_dice)
    successes = count_successes(rolls, target_number, focus_value)
    complications = count_complications(rolls)

    return TaskResult(
        rolls=rolls,
        target_number=target_number,
        successes=successes,
        complications=complications,
        difficulty=difficulty,
        focus_value=focus_value,
        momentum_generated=max(0, successes - difficulty)
        if successes >= difficulty
        else 0,
        succeeded=successes >= difficulty,
    )


def assisted_task_roll(
    attribute: int,
    discipline: int,
    system: int,
    department: int,
    difficulty: int = 1,
    dice_count: int = 2,
    focus: bool = False,
    bonus_dice: int = 0,
) -> TaskResult:
    """
    Perform a ship-assisted task roll.

    In starship combat, the character rolls using their Attribute + Discipline,
    and the ship's System + Department provides an additional assistance die.

    Args:
        attribute: Character attribute
        discipline: Character discipline
        system: Ship system value (for assistance die target number)
        department: Ship department value (for assistance die target number)
        difficulty: Task difficulty
        dice_count: Base dice (default 2)
        focus: Whether focus applies (to character dice only)
        bonus_dice: Extra dice from Momentum/Threat

    Returns:
        TaskResult with combined successes from character and ship assistance
    """
    # Character's target number
    char_target_number = attribute + discipline
    # Ship's target number for the assist die
    ship_target_number = system + department

    focus_value = discipline if focus else None

    # Roll character dice (base + bonus)
    char_dice_count = dice_count + bonus_dice
    char_rolls = roll_d20(char_dice_count)
    char_successes = count_successes(char_rolls, char_target_number, focus_value)
    char_complications = count_complications(char_rolls)

    # Roll ship assistance die (1d20 against ship's target number)
    # Ship assistance doesn't use focus
    ship_roll = roll_d20(1)
    ship_successes = count_successes(ship_roll, ship_target_number, None)
    ship_complications = count_complications(ship_roll)

    # Combine results
    total_rolls = char_rolls + ship_roll
    total_successes = char_successes + ship_successes
    total_complications = char_complications + ship_complications

    return TaskResult(
        rolls=total_rolls,
        target_number=char_target_number,  # Primary target number for display
        successes=total_successes,
        complications=total_complications,
        difficulty=difficulty,
        focus_value=focus_value,
        momentum_generated=max(0, total_successes - difficulty)
        if total_successes >= difficulty
        else 0,
        succeeded=total_successes >= difficulty,
        # Additional info for display
        ship_target_number=ship_target_number,
        ship_roll=ship_roll[0] if ship_roll else None,
        ship_successes=ship_successes,
    )


def apply_talent_modifiers(
    rolls: list[int],
    modifiers: list[TalentModifier],
) -> RollModifierResult:
    """
    Apply talent/ability modifiers to dice rolls.

    This function handles re-rolls (replacement, not addition), setting dice
    to 1 for guaranteed criticals, and other modifier effects.

    Args:
        rolls: Original dice rolls
        modifiers: List of talent modifiers to apply

    Returns:
        RollModifierResult with modified rolls and metadata

    Rules:
        - Re-rolls: Replace specified dice with new rolls (Moment of Inspiration)
        - Set to 1: Set chosen die to 1 for guaranteed 2 successes (Perfect Opportunity)
        - Critical conversion: Some talents auto-turn success into critical
        - Complication reduction: Some talents reduce complication range
    """
    final_rolls = list(rolls)  # Copy original rolls
    rerolled_indices: list[int] = []
    dice_set_to_one: list[int] = []
    criticals_added: int = 0
    complication_range_reduced_by: int = 0
    modifiers_applied: list[str] = []

    for modifier in modifiers:
        if modifier.modifier_type == "REROLL":
            for idx in modifier.dice_indices:
                if 0 <= idx < len(final_rolls):
                    final_rolls[idx] = roll_d20(1)[0]
                    rerolled_indices.append(idx)
            if modifier.dice_indices:
                modifiers_applied.append(modifier.source_talent)

        elif modifier.modifier_type == "SET_TO_ONE":
            for idx in modifier.dice_indices:
                if 0 <= idx < len(final_rolls):
                    final_rolls[idx] = 1
                    dice_set_to_one.append(idx)
                    criticals_added += 1
            if modifier.dice_indices:
                modifiers_applied.append(modifier.source_talent)

        elif modifier.modifier_type == "CRITICAL_CONVERSION":
            criticals_added += 1
            modifiers_applied.append(modifier.source_talent)

        elif modifier.modifier_type == "REDUCE_COMPLICATIONS":
            complication_range_reduced_by += modifier.complication_reduction
            modifiers_applied.append(modifier.source_talent)

    return RollModifierResult(
        final_rolls=final_rolls,
        rerolled_indices=rerolled_indices,
        dice_set_to_one=dice_set_to_one,
        criticals_added=criticals_added,
        complication_range_reduced_by=complication_range_reduced_by,
        modifiers_applied=modifiers_applied,
    )


def resolve_action(
    attribute: int,
    discipline: int,
    difficulty: int = 1,
    complication_range: int = 1,
    focus_applies: bool = False,
    talent_modifiers: Optional[list[TalentModifier]] = None,
    bonus_dice: int = 0,
) -> TaskResult:
    """
    STA 2E compliant action resolution with full modifier support.

    This implements the exact resolution sequence from STA 2E Chapter 7:
    1. Calculate Target Number = Attribute + Discipline
    2. Roll 2d20 + bonus dice from Momentum/Threat
    3. Calculate base successes (roll <= TN = 1, roll=1 = 2, roll<=focus=2)
    4. Calculate base complications based on Complication Range
    5. Apply MODIFIERS (Talents/Abilities AFTER initial calculation):
       - Re-rolls (Moment of Inspiration): Replace specified dice with new rolls
       - Set die to 1 (Perfect Opportunity): Guaranteed 2 successes on chosen die
       - Critical Success conversion: Some talents auto-turn success into critical
       - Complication Range adjustment: Some talents reduce complications
    6. Present final outcome
    7. Calculate Momentum generated = max(0, successes - difficulty)

    Args:
        attribute: Character attribute value
        discipline: Character discipline value
        difficulty: Number of successes needed (default 1)
        complication_range: How many numbers from 20 cause complications (default 1)
        focus_applies: Whether focus applies to this task
        talent_modifiers: List of talent modifiers to apply (optional)
        bonus_dice: Additional dice from Momentum/Threat (optional)

    Returns:
        TaskResult with all roll details and final outcome
    """
    target_number = attribute + discipline
    focus_value = discipline if focus_applies else None

    total_dice = 2 + bonus_dice
    rolls = roll_d20(total_dice)

    base_successes = count_successes(rolls, target_number, focus_value)
    base_complications = count_complications(rolls, complication_range)

    modifiers = talent_modifiers or []
    modifier_result = apply_talent_modifiers(rolls, modifiers)

    effective_complication_range = max(
        1, complication_range - modifier_result.complication_range_reduced_by
    )

    final_successes = count_successes(
        modifier_result.final_rolls, target_number, focus_value
    )
    final_successes += modifier_result.criticals_added

    final_complications = count_complications(
        modifier_result.final_rolls, effective_complication_range
    )

    succeeded = final_successes >= difficulty
    momentum = max(0, final_successes - difficulty) if succeeded else 0

    return TaskResult(
        rolls=modifier_result.final_rolls,
        target_number=target_number,
        successes=final_successes,
        complications=final_complications,
        difficulty=difficulty,
        focus_value=focus_value,
        momentum_generated=momentum,
        succeeded=succeeded,
    )


@dataclass
class ExtendedTaskResult(TaskResult):
    """Extended TaskResult with additional metadata for transparency."""

    base_rolls: list[int] = field(default_factory=list)
    base_successes: int = 0
    base_complications: int = 0
    rerolled_indices: list[int] = field(default_factory=list)
    dice_set_to_one: list[int] = field(default_factory=list)
    modifiers_applied: list[str] = field(default_factory=list)
    complication_range: int = 1
    effective_complication_range: int = 1


def resolve_action_extended(
    attribute: int,
    discipline: int,
    difficulty: int = 1,
    complication_range: int = 1,
    focus_applies: bool = False,
    talent_modifiers: Optional[list[TalentModifier]] = None,
    bonus_dice: int = 0,
) -> ExtendedTaskResult:
    """
    STA 2E compliant action resolution with full transparency.

    Same as resolve_action but returns ExtendedTaskResult with detailed
    breakdown of all steps for UI display.

    Args:
        attribute: Character attribute value
        discipline: Character discipline value
        difficulty: Number of successes needed (default 1)
        complication_range: How many numbers from 20 cause complications (default 1)
        focus_applies: Whether focus applies to this task
        talent_modifiers: List of talent modifiers to apply (optional)
        bonus_dice: Additional dice from Momentum/Threat (optional)

    Returns:
        ExtendedTaskResult with complete roll breakdown
    """
    target_number = attribute + discipline
    focus_value = discipline if focus_applies else None

    total_dice = 2 + bonus_dice
    rolls = roll_d20(total_dice)

    base_successes = count_successes(rolls, target_number, focus_value)
    base_complications = count_complications(rolls, complication_range)

    modifiers = talent_modifiers or []
    modifier_result = apply_talent_modifiers(rolls, modifiers)

    effective_complication_range = max(
        1, complication_range - modifier_result.complication_range_reduced_by
    )

    final_successes = count_successes(
        modifier_result.final_rolls, target_number, focus_value
    )
    final_successes += modifier_result.criticals_added

    final_complications = count_complications(
        modifier_result.final_rolls, effective_complication_range
    )

    succeeded = final_successes >= difficulty
    momentum = max(0, final_successes - difficulty) if succeeded else 0

    return ExtendedTaskResult(
        rolls=modifier_result.final_rolls,
        target_number=target_number,
        successes=final_successes,
        complications=final_complications,
        difficulty=difficulty,
        focus_value=focus_value,
        momentum_generated=momentum,
        succeeded=succeeded,
        base_rolls=rolls,
        base_successes=base_successes,
        base_complications=base_complications,
        rerolled_indices=modifier_result.rerolled_indices,
        dice_set_to_one=modifier_result.dice_set_to_one,
        modifiers_applied=modifier_result.modifiers_applied,
        complication_range=complication_range,
        effective_complication_range=effective_complication_range,
    )


def player_task_roll(
    attribute: int,
    discipline: int,
    difficulty: int = 1,
    complication_range: int = 1,
    focus: bool = False,
    bonus_dice: int = 0,
    dice_count: int = 2,
) -> dict:
    """
    Perform a player dice roll with full visualization details.

    This is the core roll function for the Player Console Dice Interface.

    Args:
        attribute: Character attribute value (e.g., Control = 9)
        discipline: Character discipline value (e.g., Science = 4)
        difficulty: Number of successes required (base 1)
        complication_range: How many numbers from 20 cause complications
            - 1 (default): only 20
            - 2: 19-20
            - etc.
        focus: Whether a relevant focus applies
        bonus_dice: Additional dice from Momentum/Threat
        dice_count: Base number of dice (default 2)

    Returns:
        Dictionary with full roll details for UI display
    """
    target_number = attribute + discipline
    focus_value = discipline if focus else None
    total_dice = dice_count + bonus_dice

    complication_threshold = 21 - complication_range

    rolls = roll_d20(total_dice)

    roll_details = []
    total_successes = 0
    normal_successes = 0
    critical_successes = 0
    focus_critical_successes = 0
    complications = 0

    for roll in rolls:
        roll_info = {"value": roll}

        if roll == 1:
            critical_successes += 1
            total_successes += 2
            roll_info["type"] = "success"
            roll_info["reason"] = "natural_critical"
            roll_info["successes"] = 2
        elif roll <= target_number:
            if focus_value is not None and roll <= focus_value:
                focus_critical_successes += 1
                total_successes += 2
                roll_info["type"] = "success"
                roll_info["reason"] = "focus_critical"
                roll_info["successes"] = 2
            else:
                normal_successes += 1
                total_successes += 1
                roll_info["type"] = "success"
                roll_info["reason"] = "normal"
                roll_info["successes"] = 1
        elif roll >= complication_threshold:
            complications += 1
            roll_info["type"] = "complication"
            roll_info["reason"] = "at_complication_threshold"
        else:
            roll_info["type"] = "failure"
            roll_info["reason"] = "above_target"

        roll_details.append(roll_info)

    succeeded = total_successes >= difficulty
    momentum_generated = max(0, total_successes - difficulty) if succeeded else 0

    return {
        "rolls": rolls,
        "target_number": target_number,
        "attribute_used": None,
        "discipline_used": None,
        "difficulty": difficulty,
        "complication_range": complication_range,
        "complication_threshold": complication_threshold,
        "focus_applied": focus,
        "focus_value": focus_value,
        "bonus_dice": bonus_dice,
        "dice_count": dice_count,
        "total_dice": total_dice,
        "successes": {
            "total": total_successes,
            "normal": normal_successes,
            "criticals": critical_successes,
            "focus_criticals": focus_critical_successes,
        },
        "complications": complications,
        "succeeded": succeeded,
        "momentum_generated": momentum_generated,
        "roll_details": roll_details,
    }


def reroll_selected(
    original_rolls: list[int],
    indices_to_reroll: list[int],
    target_number: int,
    focus_value: Optional[int] = None,
) -> tuple[list[int], list[dict]]:
    """
    Reroll specific dice from a previous roll.

    Args:
        original_rolls: The original dice rolls
        indices_to_reroll: Which dice indices to reroll (0-indexed)
        target_number: Target number for success calculation
        focus_value: Discipline value for focus criticals

    Returns:
        Tuple of (new_rolls, reroll_details)
    """
    new_rolls = list(original_rolls)
    reroll_details = []

    for idx in sorted(indices_to_reroll):
        new_roll = reroll_die(new_rolls[idx])
        new_rolls[idx] = new_roll

        detail = {
            "index": idx,
            "old_value": original_rolls[idx],
            "new_value": new_roll,
        }

        if new_roll == 1:
            detail["successes_added"] = 2
            detail["type"] = "critical"
        elif new_roll <= target_number:
            detail["successes_added"] = (
                2 if (focus_value and new_roll <= focus_value) else 1
            )
            detail["type"] = "success"
        else:
            detail["successes_added"] = 0
            detail["type"] = "failure"

        reroll_details.append(detail)

    return new_rolls, reroll_details


def apply_perfect_opportunity(
    rolls: list[int],
    index_to_set: int,
    target_number: int,
) -> tuple[list[int], dict]:
    """
    Set a specific die to 1 (Perfect Opportunity spend).

    Args:
        rolls: Current dice rolls
        index_to_set: Which die to set to 1
        target_number: Target number (for calculating new success count)

    Returns:
        Tuple of (new_rolls, effect_detail)
    """
    new_rolls = list(rolls)
    old_value = new_rolls[index_to_set]
    new_rolls[index_to_set] = 1

    detail = {
        "index": index_to_set,
        "old_value": old_value,
        "new_value": 1,
        "effect": "perfect_opportunity",
        "successes_added": 2,
        "reason": "set_to_one",
    }

    return new_rolls, detail
