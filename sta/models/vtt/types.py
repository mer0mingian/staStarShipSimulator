from enum import Enum
from typing import List, Dict, Tuple
from pydantic import BaseModel, Field


class Attribute(str, Enum):
    CONTROL = "Control"
    DARING = "Daring"
    FITNESS = "Fitness"
    INSIGHT = "Insight"
    PRESENCE = "Presence"
    REASON = "Reason"


class Department(str, Enum):
    COMMAND = "Command"
    CONN = "Conn"
    ENGINEERING = "Engineering"
    MEDICINE = "Medicine"
    SCIENCE = "Science"
    SECURITY = "Security"


class System(str, Enum):
    COMMS = "Comms"
    COMPUTERS = "Computers"
    ENGINES = "Engines"
    SENSORS = "Sensors"
    STRUCTURE = "Structure"
    WEAPONS = "Weapons"


class CharState(str, Enum):
    OK = "Ok"
    DEFEATED = "Defeated"
    FATIGUED = "Fatigued"
    DEAD = "Dead"


class NpcCategory(str, Enum):
    MAJOR = "Major"
    NOTABLE = "Notable"
    MINOR = "Minor"


class SceneStatus(str, Enum):
    ACTIVE = "Active"
    ARCHIVED = "Archived"
    CONNECTED = "Connected"


class TraitCategory(str, Enum):
    CHARACTER = "Character"
    LOCATION = "Location"
    SITUATION = "Situation"
    EQUIPMENT = "Equipment"


class TalentCategory(str, Enum):
    TALENT = "Talent"
    SPECIAL_RULE = "Special Rule"
    SPECIES_ABILITY = "Species Ability"


class WeaponType(str, Enum):
    MELEE = "Melee"
    RANGED = "Ranged"


class InjuryType(str, Enum):
    STUN = "Stun"
    DEADLY = "Deadly"


class WeaponSize(str, Enum):
    ONE_HANDED = "1H"
    TWO_HANDED = "2H"


class PcCategory(str, Enum):
    MAIN = "Main"
    SIDE = "Side"


# Derived Types
Attributes = Tuple[
    int, int, int, int, int, int
]  # Control, Daring, Fitness, Insight, Presence, Reason
Departments = Tuple[
    int, int, int, int, int, int
]  # Command, Conn, Engineering, Medicine, Science, Security
Systems = Dict[System, int]
