from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from .types import (
    Attribute,
    Department,
    System,
    CharState,
    NpcCategory,
    SceneStatus,
    TraitCategory,
    TalentCategory,
    PcCategory,
    Attributes,
    Departments,
    Systems,
)


class Trait(BaseModel):
    category: TraitCategory
    name: str
    description: str
    potency: int = Field(default=1, ge=1)


class TalentCondition(BaseModel):
    description: str
    # Logic for when the talent is active (simplified for now)
    active: bool = True


class Talent(BaseModel):
    player_selectable: bool
    category: TalentCategory
    conditions: List[TalentCondition] = []
    description: str
    # Reference to automated logic/handler (e.g. "action_config.py#fire_weapons")
    game_mechanic_ref: Optional[str] = None


class Weapon(BaseModel):
    name: str
    type: str  # Melee or Ranged
    injury: str  # Stun, Deadly
    severity: int
    size: str  # 1H or 2H
    qualities: List[str] = []
    cost: str  # Opportunity cost, e.g. "Opportunity 1"


class Attack(BaseModel):
    name: str
    # Derived from Weapon table
    weapon_ref: Optional[Weapon] = None
    # Or custom attack properties
    type: str
    injury_severity: int
    size: str


class Character(BaseModel):
    id: str
    name: str

    # Generic Char Properties
    stress: int = Field(default=0, ge=0)
    images: List[str] = []
    description: str = ""

    # Attributes & Departments (Tuples of 6)
    attributes: Attributes = (7, 7, 7, 7, 7, 7)
    departments: Departments = (1, 1, 1, 1, 1, 1)

    # Traits & Talents
    traits: List[Trait] = []
    talents: List[Talent] = []

    # Species & Role
    species: str = "Human"
    role: str = ""

    # Equipment & Attacks
    equipment: List[Trait] = []  # Equipment is a Trait with category Equipment
    attacks: List[Attack] = []

    # State
    state: CharState = CharState.OK


class Npc(Character):
    npc_category: NpcCategory = NpcCategory.MINOR
    personal_threat: int = Field(default=0, ge=0, le=24)
    location: str = ""

    # NPC Specific Backgrounds (Simplified)
    archetype: Optional[str] = None
    upbringing: Optional[str] = None
    environment: Optional[str] = None
    affiliation: Optional[str] = None


class Pc(Character):
    category: PcCategory = PcCategory.MAIN

    # PC Specific Logs
    personal_logs: List[str] = []
    mission_logs: List[str] = []
    scene_logs: List[str] = []  # Which scenes was the character part of?
    background: str = ""


class Ship(BaseModel):
    id: str
    name: str
    ship_class: str
    scale: int = Field(ge=1, le=7)
    resistance: int = 0

    # Systems & Departments
    systems: Systems = {
        System.COMMS: 1,
        System.COMPUTERS: 1,
        System.ENGINES: 1,
        System.SENSORS: 1,
        System.STRUCTURE: 1,
        System.WEAPONS: 1,
    }
    departments: Departments = (1, 1, 1, 1, 1, 1)

    # Power & Shields
    power_current: int = 0
    power_max: int = 0
    shields_current: int = 0
    shields_max: int = 0

    # NPC Specific
    crew_quality: Optional[int] = Field(default=None, ge=2, le=5)

    # Traits & Talents
    traits: List[Trait] = []
    talents: List[Talent] = []
    weapons: List[Weapon] = []


class Scene(BaseModel):
    id: str
    campaign_id: str
    name: str
    description: str = ""
    status: SceneStatus = SceneStatus.CONNECTED

    # Resource Pools
    momentum: int = Field(default=0, ge=0, le=6)
    threat: int = 0

    # Participants
    player_chars: List[str] = []  # List of PC IDs
    non_player_chars: List[str] = []  # List of NPC IDs
    ships: List[Ship] = []  # Embedded ship objects for scene context

    # Situation Traits
    situation_traits: List[Trait] = []

    # Initiative / Turn Order
    initiative_order: List[str] = []  # List of participant IDs

    # Logs
    logs: List[str] = []
