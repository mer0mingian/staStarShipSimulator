"""
Generic action handlers that execute actions based on configuration.

These handlers eliminate the need to write custom code for each action,
dramatically speeding up feature implementation.
"""

from typing import Optional, Any
from sta.models.combat import Encounter, ActiveEffect, TaskResult
from sta.models.character import Character
from sta.models.starship import Starship
from sta.mechanics.dice import task_roll
from sta.mechanics.action_config import get_action_config, ActionConfig, EffectConfig


class ActionExecutionResult:
    """Result of executing an action."""

    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message
        self.task_result: Optional[TaskResult] = None
        self.effect_created: Optional[ActiveEffect] = None
        self.momentum_generated: int = 0
        self.data: dict[str, Any] = {}

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        result = {
            "success": self.success,
            "message": self.message,
            "momentum_generated": self.momentum_generated,
        }

        if self.task_result:
            result["task_result"] = {
                "rolls": self.task_result.rolls,
                "target_number": self.task_result.target_number,
                "successes": self.task_result.successes,
                "complications": self.task_result.complications,
                "difficulty": self.task_result.difficulty,
                "succeeded": self.task_result.succeeded,
                "momentum_generated": self.task_result.momentum_generated,
            }

        if self.effect_created:
            result["effect_created"] = self.effect_created.to_dict()
            result["effect_applied"] = self.effect_created.source_action
            if self.effect_created.resistance_bonus > 0:
                result["resistance_bonus"] = self.effect_created.resistance_bonus

        result.update(self.data)
        return result


def execute_buff_action(
    action_name: str,
    encounter: Encounter,
    config: Optional[ActionConfig] = None
) -> ActionExecutionResult:
    """
    Execute a simple buff action that creates an active effect.

    Args:
        action_name: Name of the action
        encounter: The combat encounter
        config: Action configuration (will be looked up if not provided)

    Returns:
        ActionExecutionResult with the created effect
    """
    if config is None:
        config = get_action_config(action_name)

    if not config or config.get("type") != "buff":
        return ActionExecutionResult(False, f"Invalid buff action: {action_name}")

    effect_config = config.get("effect")
    if not effect_config:
        return ActionExecutionResult(False, f"No effect configured for {action_name}")

    # Create the active effect
    effect = ActiveEffect(
        source_action=action_name,
        applies_to=effect_config.get("applies_to", "all"),
        duration=effect_config.get("duration", "next_action"),
        damage_bonus=effect_config.get("damage_bonus", 0),
        resistance_bonus=effect_config.get("resistance_bonus", 0),
        difficulty_modifier=effect_config.get("difficulty_modifier", 0),
        can_reroll=effect_config.get("can_reroll", False),
        can_choose_system=effect_config.get("can_choose_system", False),
        piercing=effect_config.get("piercing", False),
    )

    encounter.add_effect(effect)

    result = ActionExecutionResult(True, f"{action_name} activated!")
    result.effect_created = effect

    # Generate a descriptive message
    messages = []
    if effect.damage_bonus > 0:
        messages.append(f"Next attack: +{effect.damage_bonus} damage")
    if effect.resistance_bonus > 0:
        messages.append(f"Resistance +{effect.resistance_bonus} until {effect.duration.replace('_', ' ')}")
    if effect.can_reroll:
        messages.append(f"Next {effect.applies_to}: can re-roll 1d20")
    if effect.can_choose_system:
        messages.append(f"Next attack: choose system hit")
    if effect.piercing:
        messages.append(f"Next attack: Piercing (ignores resistance)")

    if messages:
        result.message = f"{action_name} activated! " + ", ".join(messages) + "."

    return result


def execute_task_roll_action(
    action_name: str,
    encounter: Encounter,
    character: Character,
    ship: Starship,
    attribute_value: int,
    discipline_value: int,
    focus: bool = False,
    bonus_dice: int = 0,
    config: Optional[ActionConfig] = None
) -> ActionExecutionResult:
    """
    Execute an action that requires a task roll.

    Args:
        action_name: Name of the action
        encounter: The combat encounter
        character: The character performing the action
        ship: The ship
        attribute_value: Attribute value for the roll
        discipline_value: Discipline value for the roll
        focus: Whether focus applies
        bonus_dice: Number of bonus dice
        config: Action configuration (will be looked up if not provided)

    Returns:
        ActionExecutionResult with task roll results
    """
    if config is None:
        config = get_action_config(action_name)

    if not config or config.get("type") != "task_roll":
        return ActionExecutionResult(False, f"Invalid task roll action: {action_name}")

    roll_config = config.get("roll")
    if not roll_config:
        return ActionExecutionResult(False, f"No roll configuration for {action_name}")

    # Check resource requirements
    if config.get("requires_reserve_power", False) and not ship.has_reserve_power:
        return ActionExecutionResult(False, f"{action_name} requires Reserve Power!")

    # Perform the task roll
    difficulty = roll_config.get("difficulty", 1)
    focus_eligible = roll_config.get("focus_eligible", True) and focus

    task_result = task_roll(
        attribute=attribute_value,
        discipline=discipline_value,
        difficulty=difficulty,
        focus=focus_eligible,
        bonus_dice=bonus_dice
    )

    result = ActionExecutionResult(
        task_result.succeeded,
        f"{action_name} {'succeeded' if task_result.succeeded else 'failed'}!"
    )
    result.task_result = task_result

    # Process success effects
    if task_result.succeeded:
        on_success = config.get("on_success", {})

        # Generate momentum
        if on_success.get("generate_momentum", False) and task_result.momentum_generated > 0:
            added = encounter.add_momentum(task_result.momentum_generated)
            result.momentum_generated = added
            result.message += f" +{added} Momentum."

        # Create effect
        effect_config = on_success.get("create_effect")
        if effect_config:
            effect = ActiveEffect(
                source_action=action_name,
                applies_to=effect_config.get("applies_to", "all"),
                duration=effect_config.get("duration", "next_action"),
                damage_bonus=effect_config.get("damage_bonus", 0),
                resistance_bonus=effect_config.get("resistance_bonus", 0),
                difficulty_modifier=effect_config.get("difficulty_modifier", 0),
                can_reroll=effect_config.get("can_reroll", False),
                can_choose_system=effect_config.get("can_choose_system", False),
                piercing=effect_config.get("piercing", False),
            )
            encounter.add_effect(effect)
            result.effect_created = effect

        # Patch breach
        if on_success.get("patch_breach", False):
            result.data["patch_breach"] = True
            # Actual breach patching logic would go here

        # Restore power
        if on_success.get("restore_power", False):
            ship.has_reserve_power = True
            result.message += " Reserve Power restored!"

    else:
        result.message += f" {task_result.complications} complication(s)." if task_result.complications > 0 else ""

    return result


def apply_task_roll_success(
    action_name: str,
    encounter: Encounter,
    ship: Starship,
    momentum_generated: int = 0,
    config: Optional[ActionConfig] = None
) -> ActionExecutionResult:
    """
    Apply the success effects of a task roll action (when roll was already done).

    Args:
        action_name: Name of the action
        encounter: The combat encounter
        ship: The ship
        momentum_generated: Momentum from the successful roll
        config: Action configuration (will be looked up if not provided)

    Returns:
        ActionExecutionResult with applied effects
    """
    if config is None:
        config = get_action_config(action_name)

    if not config or config.get("type") != "task_roll":
        return ActionExecutionResult(False, f"Invalid task roll action: {action_name}")

    on_success = config.get("on_success", {})

    result = ActionExecutionResult(True, f"{action_name} succeeded!")

    # Generate momentum
    if on_success.get("generate_momentum", False) and momentum_generated > 0:
        added = encounter.add_momentum(momentum_generated)
        result.momentum_generated = added
        result.message += f" +{added} Momentum."

    # Create effect
    effect_config = on_success.get("create_effect")
    if effect_config:
        effect = ActiveEffect(
            source_action=action_name,
            applies_to=effect_config.get("applies_to", "all"),
            duration=effect_config.get("duration", "next_action"),
            damage_bonus=effect_config.get("damage_bonus", 0),
            resistance_bonus=effect_config.get("resistance_bonus", 0),
            difficulty_modifier=effect_config.get("difficulty_modifier", 0),
            can_reroll=effect_config.get("can_reroll", False),
            can_choose_system=effect_config.get("can_choose_system", False),
            piercing=effect_config.get("piercing", False),
        )
        encounter.add_effect(effect)
        result.effect_created = effect

        # Add descriptive message
        messages = []
        if effect.resistance_bonus > 0:
            messages.append(f"+{effect.resistance_bonus} Resistance")
        if effect.damage_bonus > 0:
            messages.append(f"+{effect.damage_bonus} damage")
        if effect.piercing:
            messages.append("Piercing")
        if messages:
            result.message += " " + ", ".join(messages) + "."

    # Restore power
    if on_success.get("restore_power", False):
        ship.has_reserve_power = True
        result.message += " Reserve Power restored!"

    return result


def check_action_requirements(
    action_name: str,
    encounter: Encounter,
    ship: Starship,
    config: Optional[ActionConfig] = None
) -> tuple[bool, str]:
    """
    Check if all requirements for an action are met.

    Returns:
        (can_execute, error_message)
    """
    if config is None:
        config = get_action_config(action_name)

    if not config:
        return False, f"Unknown action: {action_name}"

    # Check reserve power requirement
    if config.get("requires_reserve_power", False) and not ship.has_reserve_power:
        return False, f"{action_name} requires Reserve Power!"

    # Check flag requirement
    required_flag = config.get("requires_flag")
    if required_flag:
        # This would check ship state for specific flags
        return False, f"{action_name} requires {required_flag}!"

    # Check momentum cost
    momentum_cost = config.get("momentum_cost", 0)
    if momentum_cost > 0 and encounter.momentum < momentum_cost:
        return False, f"{action_name} requires {momentum_cost} Momentum!"

    return True, ""


def apply_effects_to_attack(
    encounter: Encounter,
    base_damage: int,
    target_resistance: int
) -> tuple[int, list[ActiveEffect], dict[str, Any]]:
    """
    Apply active effects to an attack and return modified values.

    Returns:
        (modified_damage, cleared_effects, effect_details)
    """
    effects = encounter.get_effects("attack")
    effect_details = {
        "total_damage_bonus": 0,
        "can_reroll": False,
        "can_choose_system": False,
        "piercing": False,
        "effects_applied": [],
    }

    total_bonus = 0
    for effect in effects:
        if effect.damage_bonus > 0:
            total_bonus += effect.damage_bonus
            effect_details["effects_applied"].append(f"+{effect.damage_bonus} from {effect.source_action}")
        if effect.can_reroll:
            effect_details["can_reroll"] = True
        if effect.can_choose_system:
            effect_details["can_choose_system"] = True
        if effect.piercing:
            effect_details["piercing"] = True

    effect_details["total_damage_bonus"] = total_bonus
    modified_damage = base_damage + total_bonus

    # Clear "next_action" effects
    cleared = encounter.clear_effects(applies_to="attack", duration="next_action")

    return modified_damage, cleared, effect_details


def apply_effects_to_defense(
    encounter: Encounter,
    base_resistance: int
) -> tuple[int, list[ActiveEffect], dict[str, Any]]:
    """
    Apply active effects to defense and return modified resistance.

    Returns:
        (modified_resistance, cleared_effects, effect_details)
    """
    effects = encounter.get_effects("defense")
    effect_details = {
        "total_resistance_bonus": 0,
        "effects_applied": [],
    }

    total_bonus = 0
    for effect in effects:
        if effect.resistance_bonus > 0:
            total_bonus += effect.resistance_bonus
            effect_details["effects_applied"].append(f"+{effect.resistance_bonus} from {effect.source_action}")

    effect_details["total_resistance_bonus"] = total_bonus
    modified_resistance = base_resistance + total_bonus

    # Don't clear effects here - they typically last until end of turn
    # and might apply to multiple attacks

    return modified_resistance, [], effect_details
