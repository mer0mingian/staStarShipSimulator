"""Enumerations for STA game concepts."""

from enum import Enum, auto


class Position(Enum):
    """Bridge crew positions."""
    CAPTAIN = "captain"
    HELM = "helm"
    TACTICAL = "tactical"
    OPERATIONS = "operations"
    ENGINEERING = "engineering"
    SCIENCE = "science"
    MEDICAL = "medical"


class Range(Enum):
    """Distance between ships in zones."""
    CONTACT = "contact"  # Docked/landed
    CLOSE = "close"      # Same zone (0 zones)
    MEDIUM = "medium"    # Adjacent zone (1 zone)
    LONG = "long"        # 2 zones away
    EXTREME = "extreme"  # 3+ zones away


class ActionType(Enum):
    """Types of actions characters can take."""
    MINOR = "minor"
    MAJOR = "major"


class DamageType(Enum):
    """Types of damage weapons can deal."""
    ENERGY = "energy"
    TORPEDO = "torpedo"
    KINETIC = "kinetic"


class WeaponDelivery(Enum):
    """Weapon delivery systems for energy weapons."""
    CANNONS = "cannons"
    BANKS = "banks"
    ARRAYS = "arrays"
    SPINAL_LANCE = "spinal_lance"


class SystemType(Enum):
    """Ship systems that can be targeted/damaged."""
    COMMS = "comms"
    COMPUTERS = "computers"
    ENGINES = "engines"
    SENSORS = "sensors"
    STRUCTURE = "structure"
    WEAPONS = "weapons"


class DepartmentType(Enum):
    """Ship departments."""
    COMMAND = "command"
    CONN = "conn"
    ENGINEERING = "engineering"
    MEDICINE = "medicine"
    SCIENCE = "science"
    SECURITY = "security"
