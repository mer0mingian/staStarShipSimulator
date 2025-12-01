"""
Declarative action configuration system.

This module defines actions as data configurations rather than code,
making it much faster to add new actions without writing custom handlers.
"""

from typing import Literal, TypedDict, Optional


class EffectConfig(TypedDict, total=False):
    """Configuration for an active effect."""
    applies_to: str  # "attack", "defense", "sensor", "movement", "all"
    duration: Literal["next_action", "end_of_turn", "end_of_round"]
    damage_bonus: int
    resistance_bonus: int
    difficulty_modifier: int
    can_reroll: bool
    can_choose_system: bool
    piercing: bool


class TaskRollConfig(TypedDict, total=False):
    """Configuration for a task roll."""
    attribute: str  # e.g., "control", "presence", "reason"
    discipline: str  # e.g., "security", "command", "science"
    difficulty: int
    focus_eligible: bool


class ActionSuccessConfig(TypedDict, total=False):
    """What happens on successful task roll."""
    generate_momentum: bool
    patch_breach: bool
    restore_power: bool
    create_effect: Optional[EffectConfig]


class ActionConfig(TypedDict, total=False):
    """Configuration for a complete action."""
    type: Literal["buff", "task_roll", "resource_action", "special"]

    # For buff actions
    effect: Optional[EffectConfig]

    # For task roll actions
    roll: Optional[TaskRollConfig]
    on_success: Optional[ActionSuccessConfig]
    on_failure: Optional[dict]

    # Resource requirements
    requires_reserve_power: bool
    requires_flag: Optional[str]  # e.g., "shields_raised"

    # Cost
    momentum_cost: int
    threat_cost: int


# ===== ACTION CONFIGURATIONS =====
# Define all actions as declarative configurations

ACTION_CONFIGS: dict[str, ActionConfig] = {
    # ===== TACTICAL ACTIONS =====

    "Calibrate Weapons": {
        "type": "buff",
        "effect": {
            "applies_to": "attack",
            "duration": "next_action",
            "damage_bonus": 1,
        }
    },

    "Targeting Solution": {
        "type": "buff",
        "effect": {
            "applies_to": "attack",
            "duration": "next_action",
            "can_reroll": True,
            "can_choose_system": True,
        }
    },

    "Modulate Shields": {
        "type": "task_roll",
        "roll": {
            "attribute": "control",
            "discipline": "security",
            "difficulty": 1,
            "focus_eligible": True,
        },
        "on_success": {
            "create_effect": {
                "applies_to": "defense",
                "duration": "end_of_turn",
                "resistance_bonus": 2,
            }
        }
    },

    # ===== SCIENCE ACTIONS =====

    "Calibrate Sensors": {
        "type": "buff",
        "effect": {
            "applies_to": "sensor",
            "duration": "next_action",
            "can_reroll": True,
        }
    },

    "Scan For Weakness": {
        "type": "task_roll",
        "roll": {
            "attribute": "control",
            "discipline": "science",
            "difficulty": 2,
            "focus_eligible": True,
        },
        "on_success": {
            "create_effect": {
                "applies_to": "attack",
                "duration": "next_action",
                "damage_bonus": 2,
                "piercing": True,
            }
        }
    },

    "Sensor Sweep": {
        "type": "task_roll",
        "roll": {
            "attribute": "reason",
            "discipline": "science",
            "difficulty": 1,
            "focus_eligible": True,
        },
        "on_success": {
            "generate_momentum": True,
        }
    },

    # ===== CONN/HELM ACTIONS =====

    "Attack Pattern": {
        "type": "buff",
        "effect": {
            "applies_to": "all",  # Affects ship's attacks and enemies attacking the ship
            "duration": "end_of_round",
            "difficulty_modifier": -1,  # Allies get -1 difficulty on attacks (easier)
        }
    },

    "Evasive Action": {
        "type": "buff",
        "effect": {
            "applies_to": "defense",
            "duration": "end_of_round",
            # This is complex - enemy attacks become opposed, ship's attacks get +1 difficulty
            # We'll handle this specially in the fire endpoint
        }
    },

    "Maneuver": {
        "type": "task_roll",
        "roll": {
            "attribute": "control",
            "discipline": "conn",
            "difficulty": 2,  # Variable based on terrain
            "focus_eligible": True,
        },
        "on_success": {
            "generate_momentum": True,
        }
    },

    # ===== ENGINEERING ACTIONS =====

    "Damage Control": {
        "type": "task_roll",
        "roll": {
            "attribute": "presence",
            "discipline": "engineering",
            "difficulty": 2,  # + breach potency
            "focus_eligible": True,
        },
        "on_success": {
            "patch_breach": True,
        }
    },

    "Regain Power": {
        "type": "task_roll",
        "roll": {
            "attribute": "control",
            "discipline": "engineering",
            "difficulty": 1,
            "focus_eligible": True,
        },
        "on_success": {
            "restore_power": True,
        }
    },

    "Regenerate Shields": {
        "type": "task_roll",
        "requires_reserve_power": True,
        "roll": {
            "attribute": "control",
            "discipline": "engineering",
            "difficulty": 2,
            "focus_eligible": True,
        },
        "on_success": {
            # Custom: restore shields
        }
    },

    # ===== COMMAND ACTIONS (Beta) =====

    "Rally": {
        "type": "task_roll",
        "roll": {
            "attribute": "presence",
            "discipline": "command",
            "difficulty": 0,
            "focus_eligible": True,
        },
        "on_success": {
            "generate_momentum": True,
        }
    },
}


def get_action_config(action_name: str) -> Optional[ActionConfig]:
    """Get the configuration for an action by name."""
    return ACTION_CONFIGS.get(action_name)


def is_buff_action(action_name: str) -> bool:
    """Check if an action is a simple buff action."""
    config = get_action_config(action_name)
    return config is not None and config.get("type") == "buff"


def is_task_roll_action(action_name: str) -> bool:
    """Check if an action requires a task roll."""
    config = get_action_config(action_name)
    return config is not None and config.get("type") == "task_roll"
