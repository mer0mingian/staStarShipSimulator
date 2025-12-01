"""Dice rolling mechanics for Star Trek Adventures 2nd Edition 2d20 system.

Note: STA 2e does NOT use challenge dice for damage. Weapons have flat damage
ratings that are modified by the ship's Weapons system bonus.
"""

import random
from typing import Optional

from sta.models.combat import TaskResult


def roll_d20(count: int = 1) -> list[int]:
    """Roll one or more d20s."""
    return [random.randint(1, 20) for _ in range(count)]


def count_successes(
    rolls: list[int],
    target_number: int,
    focus_value: Optional[int] = None
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
            # Natural 1 always counts as 2 successes
            successes += 2
        elif roll <= target_number:
            # Success - check for focus critical
            if focus_value is not None and roll <= focus_value:
                successes += 2  # Critical via focus
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
    bonus_dice: int = 0
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
        momentum_generated=max(0, successes - difficulty) if successes >= difficulty else 0,
        succeeded=successes >= difficulty
    )


def assisted_task_roll(
    attribute: int,
    discipline: int,
    system: int,
    department: int,
    difficulty: int = 1,
    dice_count: int = 2,
    focus: bool = False,
    bonus_dice: int = 0
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
        momentum_generated=max(0, total_successes - difficulty) if total_successes >= difficulty else 0,
        succeeded=total_successes >= difficulty,
        # Additional info for display
        ship_target_number=ship_target_number,
        ship_roll=ship_roll[0] if ship_roll else None,
        ship_successes=ship_successes
    )
