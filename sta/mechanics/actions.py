"""Action definitions for starship combat by bridge position."""

from dataclasses import dataclass, field
from typing import Optional, Callable
from sta.models.enums import Position, ActionType


@dataclass
class Action:
    """Definition of a combat action."""
    name: str
    action_type: ActionType
    positions: list[Position]  # Which positions can use this action
    description: str

    # Task requirements
    difficulty: int = 0
    attribute: Optional[str] = None  # e.g., "control", "daring"
    discipline: Optional[str] = None  # e.g., "conn", "security"

    # Ship assistance (for assisted tasks)
    assisted_by_system: Optional[str] = None  # e.g., "engines", "weapons"
    assisted_by_department: Optional[str] = None  # e.g., "conn", "security"

    # Special requirements
    requires_reserve_power: bool = False
    requires_prepare: bool = False
    momentum_cost: int = 0
    threat_cost: int = 0

    # Effects
    effect_notes: str = ""


# Standard Minor Actions (available to all positions)
STANDARD_MINOR_ACTIONS = [
    Action(
        name="Change Position",
        action_type=ActionType.MINOR,
        positions=list(Position),
        description="Move to any bridge station or ship location. Arrive at start of next turn.",
    ),
    Action(
        name="Interact",
        action_type=ActionType.MINOR,
        positions=list(Position),
        description="Interact with environment object. Complex interactions may require major action.",
    ),
    Action(
        name="Prepare",
        action_type=ActionType.MINOR,
        positions=list(Position),
        description="Prepare for or set up a task. Required before some actions.",
    ),
    Action(
        name="Restore",
        action_type=ActionType.MINOR,
        positions=list(Position),
        description="Minor repairs/adjustments to restore system after disruption.",
    ),
]

# Standard Major Actions (available to all positions)
STANDARD_MAJOR_ACTIONS = [
    Action(
        name="Assist",
        action_type=ActionType.MAJOR,
        positions=list(Position),
        description="Grant ally advantage on their next task.",
    ),
    Action(
        name="Create Trait",
        action_type=ActionType.MAJOR,
        positions=list(Position),
        description="Create, change, or remove a trait.",
        difficulty=2,
    ),
    Action(
        name="Override",
        action_type=ActionType.MAJOR,
        positions=list(Position),
        description="Attempt action from another position. Difficulty +1.",
        effect_notes="Add +1 to base difficulty of the action being attempted.",
    ),
    Action(
        name="Pass",
        action_type=ActionType.MAJOR,
        positions=list(Position),
        description="Choose not to attempt a task this turn.",
        difficulty=0,
    ),
    Action(
        name="Ready",
        action_type=ActionType.MAJOR,
        positions=list(Position),
        description="Prepare a major action as a reaction to a trigger.",
    ),
]

# Command Station Actions
COMMAND_ACTIONS = [
    Action(
        name="Direct",
        action_type=ActionType.MAJOR,
        positions=[Position.CAPTAIN],
        description="Select bridge ally who immediately attempts major action. Assist with 1d20.",
        attribute="control",
        discipline="command",
        momentum_cost=1,
        effect_notes="Assisted ally takes immediate major action.",
    ),
    Action(
        name="Rally",
        action_type=ActionType.MAJOR,
        positions=[Position.CAPTAIN],
        description="Inspire crew to generate Momentum.",
        difficulty=0,
        attribute="presence",
        discipline="command",
        effect_notes="Successes beyond difficulty become Momentum.",
    ),
]

# Helm Station Actions
HELM_MINOR_ACTIONS = [
    Action(
        name="Impulse",
        action_type=ActionType.MINOR,
        positions=[Position.HELM],
        description="Move up to 2 zones using impulse engines. Moving only 1 zone reduces terrain cost by 1.",
    ),
    Action(
        name="Thrusters",
        action_type=ActionType.MINOR,
        positions=[Position.HELM],
        description="Fine adjustments within current zone. Can safely move into Contact.",
    ),
]

HELM_MAJOR_ACTIONS = [
    Action(
        name="Attack Pattern",
        action_type=ActionType.MAJOR,
        positions=[Position.HELM],
        description="Fly steadily for targeting. Assist each ship attack until next turn. Attacks against ship: Difficulty -1.",
        attribute="control",
        discipline="conn",
        effect_notes="Ship attacks assisted. Enemy attacks vs this ship are easier.",
    ),
    Action(
        name="Evasive Action",
        action_type=ActionType.MAJOR,
        positions=[Position.HELM],
        description="Unpredictable maneuvering. Attacks vs ship become opposed tasks. Ship's own attacks: Difficulty +1.",
        attribute="daring",
        discipline="conn",
        assisted_by_system="structure",
        assisted_by_department="conn",
        effect_notes="If you win opposed roll, move 1 zone. Cannot combine with Defensive Fire.",
    ),
    Action(
        name="Maneuver",
        action_type=ActionType.MAJOR,
        positions=[Position.HELM],
        description="Careful flight control to generate Momentum for difficult terrain.",
        difficulty=0,
        attribute="control",
        discipline="conn",
        assisted_by_system="engines",
        assisted_by_department="conn",
    ),
    Action(
        name="Ram",
        action_type=ActionType.MAJOR,
        positions=[Position.HELM],
        description="Move into Contact with enemy at Close range and inflict collision damage.",
        difficulty=2,
        attribute="daring",
        discipline="conn",
        assisted_by_system="engines",
        assisted_by_department="conn",
        effect_notes="Both ships take each other's collision damage. Ramming adds Intense quality.",
    ),
    Action(
        name="Warp",
        action_type=ActionType.MAJOR,
        positions=[Position.HELM],
        description="Go to warp. Move zones equal to Engines score or leave battlefield.",
        difficulty=1,
        attribute="control",
        discipline="conn",
        assisted_by_system="engines",
        assisted_by_department="conn",
        requires_reserve_power=True,
        requires_prepare=True,
    ),
]

# Operations/Engineering Station Actions
OPERATIONS_MAJOR_ACTIONS = [
    Action(
        name="Damage Control",
        action_type=ActionType.MAJOR,
        positions=[Position.OPERATIONS, Position.ENGINEERING],
        description="Direct repair team to patch a breach.",
        difficulty=2,  # +1 per Potency of breach
        attribute="presence",
        discipline="engineering",
        effect_notes="Success patches breach (removes penalties) but doesn't fully repair.",
    ),
    Action(
        name="Regain Power",
        action_type=ActionType.MAJOR,
        positions=[Position.OPERATIONS, Position.ENGINEERING],
        description="Restore Reserve Power. Difficulty +1 each attempt per scene.",
        difficulty=1,
        attribute="control",
        discipline="engineering",
        effect_notes="May Succeed at Cost.",
    ),
    Action(
        name="Regenerate Shields",
        action_type=ActionType.MAJOR,
        positions=[Position.OPERATIONS, Position.ENGINEERING],
        description="Restore shields equal to Engineering rating, +2 per Momentum spent.",
        difficulty=2,  # 3 if shields at 0
        attribute="control",
        discipline="engineering",
        assisted_by_system="structure",
        assisted_by_department="engineering",
        requires_reserve_power=True,
    ),
    Action(
        name="Reroute Power",
        action_type=ActionType.MAJOR,
        positions=[Position.OPERATIONS, Position.ENGINEERING],
        description="Reroute Reserve Power to boost a specific system for next action.",
        requires_reserve_power=True,
    ),
    Action(
        name="Transport",
        action_type=ActionType.MAJOR,
        positions=[Position.OPERATIONS, Position.ENGINEERING],
        description="Operate transporters remotely. Difficulty +1 if from bridge.",
        effect_notes="From bridge: +1 Difficulty",
    ),
]

# Sensor Operations/Science Station Actions
SCIENCE_MINOR_ACTIONS = [
    Action(
        name="Calibrate Sensors",
        action_type=ActionType.MINOR,
        positions=[Position.SCIENCE],
        description="Fine-tune sensors. Next Sensor action: ignore one trait OR re-roll 1d20.",
    ),
    Action(
        name="Launch Probe",
        action_type=ActionType.MINOR,
        positions=[Position.SCIENCE],
        description="Launch probe to any zone within Long range. Sensor actions may use probe's location.",
    ),
]

SCIENCE_MAJOR_ACTIONS = [
    Action(
        name="Reveal",
        action_type=ActionType.MAJOR,
        positions=[Position.SCIENCE],
        description="Scan for cloaked/concealed vessels within Long range.",
        difficulty=3,
        attribute="reason",
        discipline="science",
        assisted_by_system="sensors",
        assisted_by_department="science",
        effect_notes="Revealed vessel: attacks vs it at +2 Difficulty until it moves.",
    ),
    Action(
        name="Scan For Weakness",
        action_type=ActionType.MAJOR,
        positions=[Position.SCIENCE],
        description="Find weakness in enemy vessel for next attack.",
        difficulty=2,
        attribute="control",
        discipline="science",
        assisted_by_system="sensors",
        assisted_by_department="security",
        effect_notes="Next attack vs that ship: damage +2 OR gains Piercing.",
    ),
    Action(
        name="Sensor Sweep",
        action_type=ActionType.MAJOR,
        positions=[Position.SCIENCE],
        description="Scan a zone for information on ships, objects, phenomena.",
        difficulty=1,  # +1 per range beyond Close
        attribute="reason",
        discipline="science",
        assisted_by_system="sensors",
        assisted_by_department="science",
        effect_notes="Spend Momentum for additional details.",
    ),
]

# Tactical Station Actions
TACTICAL_MINOR_ACTIONS = [
    Action(
        name="Calibrate Weapons",
        action_type=ActionType.MINOR,
        positions=[Position.TACTICAL],
        description="Fine-tune weapons. Next attack: damage +1.",
    ),
    Action(
        name="Raise/Lower Shields",
        action_type=ActionType.MINOR,
        positions=[Position.TACTICAL],
        description="Raise shields to max or lower to 0. Raised shields required for protection.",
    ),
    Action(
        name="Arm/Disarm Weapons",
        action_type=ActionType.MINOR,
        positions=[Position.TACTICAL],
        description="Arm weapons for attacks (detectable) or disarm them.",
    ),
    Action(
        name="Targeting Solution",
        action_type=ActionType.MINOR,
        positions=[Position.TACTICAL],
        description="Lock onto enemy within Long range. Next attack: re-roll d20 OR choose system hit.",
    ),
]

TACTICAL_MAJOR_ACTIONS = [
    Action(
        name="Fire",
        action_type=ActionType.MAJOR,
        positions=[Position.TACTICAL],
        description="Attack with energy weapon or torpedo.",
        difficulty=2,  # 3 for torpedoes
        attribute="control",
        discipline="security",
        assisted_by_system="weapons",
        assisted_by_department="security",
        effect_notes="Torpedoes: Difficulty 3, add 1 Threat. See weapon damage and qualities.",
    ),
    Action(
        name="Defensive Fire",
        action_type=ActionType.MAJOR,
        positions=[Position.TACTICAL],
        description="Use energy weapon defensively. Attacks vs ship become opposed.",
        attribute="daring",
        discipline="security",
        assisted_by_system="weapons",
        assisted_by_department="security",
        effect_notes="Success: spend 2 Momentum to counterattack. Cannot combine with Evasive Action.",
    ),
    Action(
        name="Modulate Shields",
        action_type=ActionType.MAJOR,
        positions=[Position.TACTICAL],
        description="Increase Resistance by 2 until next turn. Cannot use if shields at 0.",
        effect_notes="Resistance +2 until your next turn.",
    ),
    Action(
        name="Tractor Beam",
        action_type=ActionType.MAJOR,
        positions=[Position.TACTICAL],
        description="Immobilize target at Close range until they break free.",
        difficulty=2,
        attribute="control",
        discipline="security",
        assisted_by_system="structure",
        assisted_by_department="security",
        effect_notes="Target must succeed at task (Difficulty = tractor strength) to break free.",
    ),
]

# Communications Station Actions
COMMS_MAJOR_ACTIONS = [
    Action(
        name="Hail",
        action_type=ActionType.MAJOR,
        positions=[Position.OPERATIONS],
        description="Open communications with another vessel or coordinate with allied ships.",
    ),
    Action(
        name="Jam Communications",
        action_type=ActionType.MAJOR,
        positions=[Position.OPERATIONS],
        description="Create interference trait affecting enemy communications.",
        difficulty=2,
        attribute="reason",
        discipline="science",
        assisted_by_system="comms",
        assisted_by_department="science",
    ),
]

# Medical Station Actions (typically not on bridge, but available)
MEDICAL_MAJOR_ACTIONS = [
    Action(
        name="Triage",
        action_type=ActionType.MAJOR,
        positions=[Position.MEDICAL],
        description="Coordinate medical response to crew casualties.",
        attribute="presence",
        discipline="medicine",
    ),
]


def get_actions_for_position(position: Position) -> dict[str, list[Action]]:
    """Get all available actions for a bridge position."""
    actions = {
        "minor": list(STANDARD_MINOR_ACTIONS),
        "major": list(STANDARD_MAJOR_ACTIONS),
    }

    # Add position-specific actions
    if position == Position.CAPTAIN:
        actions["major"].extend(COMMAND_ACTIONS)

    elif position == Position.HELM:
        actions["minor"].extend(HELM_MINOR_ACTIONS)
        actions["major"].extend(HELM_MAJOR_ACTIONS)

    elif position == Position.TACTICAL:
        actions["minor"].extend(TACTICAL_MINOR_ACTIONS)
        actions["major"].extend(TACTICAL_MAJOR_ACTIONS)

    elif position == Position.OPERATIONS:
        actions["major"].extend(OPERATIONS_MAJOR_ACTIONS)
        actions["major"].extend(COMMS_MAJOR_ACTIONS)

    elif position == Position.ENGINEERING:
        actions["major"].extend(OPERATIONS_MAJOR_ACTIONS)

    elif position == Position.SCIENCE:
        actions["minor"].extend(SCIENCE_MINOR_ACTIONS)
        actions["major"].extend(SCIENCE_MAJOR_ACTIONS)

    elif position == Position.MEDICAL:
        actions["major"].extend(MEDICAL_MAJOR_ACTIONS)

    return actions


def get_action_by_name(name: str, position: Position) -> Optional[Action]:
    """Find a specific action by name for a position."""
    actions = get_actions_for_position(position)
    for action in actions["minor"] + actions["major"]:
        if action.name.lower() == name.lower():
            return action
    return None


# All actions combined for reference
ALL_ACTIONS = (
    STANDARD_MINOR_ACTIONS +
    STANDARD_MAJOR_ACTIONS +
    COMMAND_ACTIONS +
    HELM_MINOR_ACTIONS +
    HELM_MAJOR_ACTIONS +
    OPERATIONS_MAJOR_ACTIONS +
    SCIENCE_MINOR_ACTIONS +
    SCIENCE_MAJOR_ACTIONS +
    TACTICAL_MINOR_ACTIONS +
    TACTICAL_MAJOR_ACTIONS +
    COMMS_MAJOR_ACTIONS +
    MEDICAL_MAJOR_ACTIONS
)
