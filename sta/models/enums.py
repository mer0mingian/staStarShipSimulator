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


class TerrainType(Enum):
    """Types of space terrain for tactical map hexes.

    Each terrain type has a momentum cost to leave and may have
    special properties (hazardous, blocks visibility).
    """
    OPEN = "open"                        # No effects, 0 momentum
    DEBRIS_FIELD = "debris_field"        # 1 Momentum, hazardous
    DUST_CLOUD = "dust_cloud"            # 1 Momentum, blocks visibility
    PLANETARY_GRAVITY = "planetary_gravity"  # 1 Momentum
    ASTEROID_FIELD = "asteroid_field"    # 1 Momentum, hazardous
    DENSE_NEBULA = "dense_nebula"        # 2 Momentum, blocks visibility
    STELLAR_GRAVITY = "stellar_gravity"  # 2 Momentum

    @property
    def movement_cost(self) -> int:
        """Momentum cost to leave this terrain type."""
        costs = {
            TerrainType.OPEN: 0,
            TerrainType.DEBRIS_FIELD: 1,
            TerrainType.DUST_CLOUD: 1,
            TerrainType.PLANETARY_GRAVITY: 1,
            TerrainType.ASTEROID_FIELD: 1,
            TerrainType.DENSE_NEBULA: 2,
            TerrainType.STELLAR_GRAVITY: 2,
        }
        return costs.get(self, 0)

    @property
    def is_hazardous(self) -> bool:
        """Whether adding Threat instead of Momentum causes damage."""
        return self in {TerrainType.DEBRIS_FIELD, TerrainType.ASTEROID_FIELD}

    @property
    def blocks_visibility(self) -> bool:
        """Whether this terrain blocks long-range visibility."""
        return self in {TerrainType.DUST_CLOUD, TerrainType.DENSE_NEBULA}


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


class CrewQuality(Enum):
    """
    NPC ship crew quality levels.

    Per STA 2e rules, NPC ships don't have individual crew members.
    Instead, they have a Crew Quality that provides attribute and
    department ratings for all tasks. NPC crew are always considered
    to have an applicable Focus (crits on 1s AND 2s).
    """
    BASIC = "basic"           # Attribute 8, Department 1
    PROFICIENT = "proficient" # Attribute 9, Department 2
    TALENTED = "talented"     # Attribute 10, Department 3
    EXCEPTIONAL = "exceptional"  # Attribute 11, Department 4

    @property
    def attribute(self) -> int:
        """Get the attribute rating for this crew quality."""
        return {
            CrewQuality.BASIC: 8,
            CrewQuality.PROFICIENT: 9,
            CrewQuality.TALENTED: 10,
            CrewQuality.EXCEPTIONAL: 11,
        }[self]

    @property
    def department(self) -> int:
        """Get the department rating for this crew quality."""
        return {
            CrewQuality.BASIC: 1,
            CrewQuality.PROFICIENT: 2,
            CrewQuality.TALENTED: 3,
            CrewQuality.EXCEPTIONAL: 4,
        }[self]

    @property
    def target_number(self) -> int:
        """Get the target number (attribute + department) for task rolls."""
        return self.attribute + self.department

    @property
    def has_focus(self) -> bool:
        """NPC crew always have an applicable focus."""
        return True
