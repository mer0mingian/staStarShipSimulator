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
    ship_assist_system: str  # e.g., "structure", "weapons" - ship system for assist die
    ship_assist_department: str  # e.g., "engineering", "security" - ship department for assist die


class ActionSuccessConfig(TypedDict, total=False):
    """What happens on successful task roll."""
    generate_momentum: bool
    patch_breach: bool
    restore_power: bool
    create_effect: Optional[EffectConfig]


class ActionConfig(TypedDict, total=False):
    """Configuration for a complete action."""
    type: Literal["buff", "task_roll", "resource_action", "toggle", "special"]

    # For buff actions
    effect: Optional[EffectConfig]

    # For task roll actions
    roll: Optional[TaskRollConfig]
    on_success: Optional[ActionSuccessConfig]
    on_failure: Optional[dict]

    # For toggle actions
    toggles: Optional[str]  # e.g., "shields_raised" - which ship property to toggle

    # Resource requirements
    requires_reserve_power: bool
    requires_flag: Optional[str]  # e.g., "shields_raised"

    # System requirements - which ship system this action relies on
    # If the system is destroyed (breaches >= half Scale), action is unavailable
    # Breach potency on this system adds to task difficulty
    requires_system: Optional[str]  # e.g., "weapons", "sensors", "engines", "structure"

    # Cost
    momentum_cost: int
    threat_cost: int


# ===== ACTION CONFIGURATIONS =====
# Define all actions as declarative configurations

ACTION_CONFIGS: dict[str, ActionConfig] = {
    # ===== TACTICAL ACTIONS =====

    "Calibrate Weapons": {
        "type": "buff",
        "requires_system": "weapons",
        "effect": {
            "applies_to": "attack",
            "duration": "next_action",
            "damage_bonus": 1,
        }
    },

    "Targeting Solution": {
        "type": "buff",
        "requires_system": "weapons",
        "effect": {
            "applies_to": "attack",
            "duration": "next_action",
            "can_reroll": True,
            "can_choose_system": True,
        }
    },

    "Modulate Shields": {
        "type": "task_roll",
        "requires_system": "structure",
        "roll": {
            "attribute": "control",
            "discipline": "engineering",
            "difficulty": 1,
            "focus_eligible": True,
            "ship_assist_system": "structure",
            "ship_assist_department": "engineering",
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
        "requires_system": "sensors",
        "effect": {
            "applies_to": "sensor",
            "duration": "next_action",
            "can_reroll": True,
        }
    },

    "Scan For Weakness": {
        "type": "task_roll",
        "requires_system": "sensors",
        "roll": {
            "attribute": "control",
            "discipline": "science",
            "difficulty": 2,
            "focus_eligible": True,
            "ship_assist_system": "sensors",
            "ship_assist_department": "security",
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
        "requires_system": "sensors",
        "roll": {
            "attribute": "reason",
            "discipline": "science",
            "difficulty": 1,
            "focus_eligible": True,
            "ship_assist_system": "sensors",
            "ship_assist_department": "science",
        },
        "on_success": {
            "generate_momentum": True,
        }
    },

    # ===== CONN/HELM ACTIONS =====

    "Attack Pattern": {
        "type": "buff",
        "requires_system": "engines",
        "effect": {
            "applies_to": "all",  # Affects ship's attacks and enemies attacking the ship
            "duration": "end_of_round",
            "difficulty_modifier": -1,  # Allies get -1 difficulty on attacks (easier)
        }
    },

    "Evasive Action": {
        "type": "buff",
        "requires_system": "engines",
        "effect": {
            "applies_to": "defense",
            "duration": "end_of_round",
            # This is complex - enemy attacks become opposed, ship's attacks get +1 difficulty
            # We'll handle this specially in the fire endpoint
        }
    },

    "Defensive Fire": {
        "type": "special",  # Special because it requires weapon selection and stores weapon_index
        "requires_system": "weapons",
        "effect": {
            "applies_to": "defense",
            "duration": "next_turn",  # Lasts until player's next turn
            # When active, enemy attacks become opposed rolls
            # Uses Daring + Security, assisted by Weapons + Security
            # If defender wins: attack misses, can spend 2 Momentum to counterattack
        },
        # Cannot be used if Evasive Action is active
        "blocks": ["Evasive Action"],
        "blocked_by": ["Evasive Action"],
    },

    "Maneuver": {
        "type": "task_roll",
        "requires_system": "engines",
        "roll": {
            "attribute": "control",
            "discipline": "conn",
            "difficulty": 2,  # Variable based on terrain
            "focus_eligible": True,
            "ship_assist_system": "engines",
            "ship_assist_department": "conn",
        },
        "on_success": {
            "generate_momentum": True,
        }
    },

    "Ram": {
        "type": "special",  # Special because it deals damage to BOTH ships
        "requires_system": "engines",
        "roll": {
            "attribute": "daring",
            "discipline": "conn",
            "difficulty": 2,
            "focus_eligible": True,
            "ship_assist_system": "engines",
            "ship_assist_department": "conn",
        },
        # Collision damage is calculated dynamically based on Scale
        # Ramming adds Intense quality, and collision has Piercing + Devastating
    },

    # ===== ENGINEERING ACTIONS =====

    "Damage Control": {
        "type": "task_roll",
        # Note: Damage Control doesn't require a specific system - it's about patching breaches
        # The difficulty is modified by the breach potency being repaired, handled specially
        "roll": {
            "attribute": "presence",
            "discipline": "engineering",
            "difficulty": 2,  # + breach potency of target system
            "focus_eligible": True,
        },
        "on_success": {
            "patch_breach": True,
        }
    },

    "Regain Power": {
        "type": "task_roll",
        "requires_system": "engines",
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
        "requires_system": "structure",
        "roll": {
            "attribute": "control",
            "discipline": "engineering",
            "difficulty": 2,
            "focus_eligible": True,
            "ship_assist_system": "structure",
            "ship_assist_department": "engineering",
        },
        "on_success": {
            # Custom: restore shields
        }
    },

    "Reroute Power": {
        "type": "special",  # Special because it requires selecting a target system
        "requires_reserve_power": True,
        "requires_system": "engines",
        # Player selects a system (comms, computers, engines, sensors, structure, weapons)
        # Next action using that system gets -1 Difficulty
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

    # ===== TOGGLE ACTIONS =====

    "Raise Shields": {
        "type": "toggle",
        "toggles": "shields_raised",
    },

    "Lower Shields": {
        "type": "toggle",
        "toggles": "shields_raised",
    },

    "Arm Weapons": {
        "type": "toggle",
        "toggles": "weapons_armed",
    },

    "Disarm Weapons": {
        "type": "toggle",
        "toggles": "weapons_armed",
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


def is_toggle_action(action_name: str) -> bool:
    """Check if an action is a toggle action."""
    config = get_action_config(action_name)
    return config is not None and config.get("type") == "toggle"


# ===== NPC ACTIONS =====
# Actions that NPC ships can perform. NPCs cannot use actions that:
# - Require individual crew members (Assist, Direct, Rally)
# - Require Reserve Power (NPCs don't have Reserve Power per rules)
#   - Regain Power, Regenerate Shields, Reroute Power, Warp

NPC_ACTIONS: dict[str, list[str]] = {
    "tactical_minor": [
        "Calibrate Weapons",
        "Targeting Solution",
        "Raise Shields",
        "Lower Shields",
        "Arm Weapons",
        "Disarm Weapons",
    ],
    "tactical_major": [
        "Fire",  # Special - handled separately
        "Modulate Shields",
        "Defensive Fire",
    ],
    "conn_minor": [],
    "conn_major": [
        "Attack Pattern",
        "Evasive Action",
        "Maneuver",
        "Ram",
    ],
    "engineering_minor": [],
    "engineering_major": [
        "Damage Control",
        # Note: No Regain Power, Regenerate Shields (require Reserve Power)
    ],
    "science_minor": [
        "Calibrate Sensors",
    ],
    "science_major": [
        "Scan For Weakness",
        "Sensor Sweep",
    ],
}

# Flat list of all NPC actions
ALL_NPC_ACTIONS = []
for category in NPC_ACTIONS.values():
    ALL_NPC_ACTIONS.extend(category)


def is_npc_action(action_name: str) -> bool:
    """Check if an action is available to NPC ships."""
    return action_name in ALL_NPC_ACTIONS or action_name == "Fire"


def get_npc_actions_by_category() -> dict[str, list[str]]:
    """Get NPC actions organized by category."""
    return NPC_ACTIONS


# ===== BREACH SYSTEM HELPERS =====
# These functions help check if actions are available and calculate breach modifiers

# Map special actions (not in ACTION_CONFIGS) to their required systems
SPECIAL_ACTION_SYSTEMS: dict[str, str] = {
    "Fire": "weapons",
    "Tractor Beam": "structure",
    "Warp": "engines",
    "Impulse": "engines",
    "Thrusters": "engines",
}


def get_action_required_system(action_name: str) -> Optional[str]:
    """
    Get the ship system required by an action.

    Returns the system name (e.g., "weapons", "sensors") or None if no system required.
    """
    # Check ACTION_CONFIGS first
    config = get_action_config(action_name)
    if config and config.get("requires_system"):
        return config.get("requires_system")

    # Check special actions
    if action_name in SPECIAL_ACTION_SYSTEMS:
        return SPECIAL_ACTION_SYSTEMS[action_name]

    return None


def is_action_available(action_name: str, ship) -> tuple[bool, Optional[str]]:
    """
    Check if an action is available given the ship's breach status.

    Args:
        action_name: Name of the action
        ship: Starship model with breach data

    Returns:
        Tuple of (is_available, reason_if_unavailable)
        - (True, None) if action is available
        - (False, "System DESTROYED") if the required system is destroyed
    """
    required_system = get_action_required_system(action_name)

    if not required_system:
        return (True, None)

    # Import here to avoid circular imports
    from sta.models.enums import SystemType

    try:
        system_type = SystemType(required_system)
        if ship.is_system_destroyed(system_type):
            return (False, f"{required_system.upper()} DESTROYED")
    except ValueError:
        # Unknown system type, allow the action
        pass

    return (True, None)


def get_breach_difficulty_modifier(action_name: str, ship) -> int:
    """
    Get the difficulty modifier from breaches for an action.

    Per the rules, breach potency on a system increases the difficulty
    of tasks that use that system.

    Args:
        action_name: Name of the action
        ship: Starship model with breach data

    Returns:
        The difficulty modifier (0 or positive integer)
    """
    required_system = get_action_required_system(action_name)

    if not required_system:
        return 0

    # Import here to avoid circular imports
    from sta.models.enums import SystemType

    try:
        system_type = SystemType(required_system)
        return ship.get_breach_potency(system_type)
    except ValueError:
        return 0


def get_all_actions_availability(ship) -> dict[str, dict]:
    """
    Get availability status for all configured actions.

    Args:
        ship: Starship model with breach data

    Returns:
        Dict mapping action names to their availability info:
        {
            "action_name": {
                "available": True/False,
                "reason": None or "SYSTEM DESTROYED",
                "breach_modifier": int,
                "required_system": str or None
            }
        }
    """
    result = {}

    # Check all actions in ACTION_CONFIGS
    for action_name in ACTION_CONFIGS:
        available, reason = is_action_available(action_name, ship)
        result[action_name] = {
            "available": available,
            "reason": reason,
            "breach_modifier": get_breach_difficulty_modifier(action_name, ship) if available else 0,
            "required_system": get_action_required_system(action_name),
        }

    # Check special actions
    for action_name in SPECIAL_ACTION_SYSTEMS:
        available, reason = is_action_available(action_name, ship)
        result[action_name] = {
            "available": available,
            "reason": reason,
            "breach_modifier": get_breach_difficulty_modifier(action_name, ship) if available else 0,
            "required_system": get_action_required_system(action_name),
        }

    return result
