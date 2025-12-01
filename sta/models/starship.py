"""Starship data model for STA."""

from dataclasses import dataclass, field
from typing import Optional
from .enums import DamageType, WeaponDelivery, Range, SystemType


@dataclass
class Systems:
    """Ship systems (typically 7-12 each)."""
    comms: int = 7
    computers: int = 7
    engines: int = 7
    sensors: int = 7
    structure: int = 7
    weapons: int = 7

    def total(self) -> int:
        """Sum of all systems."""
        return (
            self.comms + self.computers + self.engines +
            self.sensors + self.structure + self.weapons
        )

    def get(self, name: str) -> int:
        """Get system by name."""
        return getattr(self, name.lower())


@dataclass
class Departments:
    """Ship departments (typically 0-5 each, represent crew expertise)."""
    command: int = 0
    conn: int = 0
    engineering: int = 0
    medicine: int = 0
    science: int = 0
    security: int = 0

    def total(self) -> int:
        """Sum of all departments."""
        return (
            self.command + self.conn + self.engineering +
            self.medicine + self.science + self.security
        )

    def get(self, name: str) -> int:
        """Get department by name."""
        return getattr(self, name.lower())


@dataclass
class Weapon:
    """A starship weapon."""
    name: str
    weapon_type: DamageType  # energy, torpedo
    damage: int  # Base damage before weapons rating bonus
    range: Range = Range.MEDIUM
    qualities: list[str] = field(default_factory=list)
    delivery: Optional[WeaponDelivery] = None  # For energy weapons
    requires_calibration: bool = False

    @property
    def attack_difficulty(self) -> int:
        """Base difficulty for attack rolls."""
        if self.weapon_type == DamageType.TORPEDO:
            return 3
        return 2


@dataclass
class Breach:
    """A hull breach or system damage."""
    system: SystemType
    potency: int = 1  # Stacks - "Hull Breach 2" means potency=2

    def __str__(self) -> str:
        return f"{self.system.value.title()} Breach ({self.potency})"


@dataclass
class Starship:
    """A starship (player or enemy)."""
    name: str
    ship_class: str
    scale: int
    systems: Systems
    departments: Departments
    weapons: list[Weapon] = field(default_factory=list)
    talents: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    breaches: list[Breach] = field(default_factory=list)
    shields: int = 0
    shields_max: int = 0
    resistance: int = 0
    crew_support: int = 0
    has_reserve_power: bool = True
    registry: Optional[str] = None

    def __post_init__(self):
        """Calculate derived values."""
        if self.shields_max == 0:
            # Default shields = Structure + Security
            self.shields_max = self.systems.structure + self.departments.security
        if self.shields == 0:
            self.shields = self.shields_max
        if self.resistance == 0:
            self.resistance = self.scale

    def weapons_damage_bonus(self) -> int:
        """Calculate damage bonus from Weapons system rating."""
        weapons = self.systems.weapons
        if weapons <= 6:
            return 0
        elif weapons <= 8:
            return 1
        elif weapons <= 10:
            return 2
        elif weapons <= 12:
            return 3
        return 4

    def get_breach_potency(self, system: SystemType) -> int:
        """Get total breach potency for a system."""
        return sum(b.potency for b in self.breaches if b.system == system)

    def is_system_disabled(self, system: SystemType) -> bool:
        """Check if a system is disabled (breach potency >= system rating)."""
        return self.get_breach_potency(system) >= self.systems.get(system.value)

    def add_breach(self, system: SystemType, potency: int = 1) -> None:
        """Add or increase a breach on a system."""
        for breach in self.breaches:
            if breach.system == system:
                breach.potency += potency
                return
        self.breaches.append(Breach(system=system, potency=potency))

    def take_damage(self, damage: int) -> dict:
        """
        Apply damage to the ship. Shields absorb first, then hull.
        Returns a dict with damage breakdown.
        """
        result = {
            "total_damage": damage,
            "shield_damage": 0,
            "hull_damage": 0,
            "shields_remaining": self.shields,
            "breaches_caused": 0
        }

        # Shields absorb damage first
        if self.shields > 0:
            shield_absorbed = min(self.shields, damage)
            self.shields -= shield_absorbed
            damage -= shield_absorbed
            result["shield_damage"] = shield_absorbed
            result["shields_remaining"] = self.shields

        # Remaining damage hits hull (reduced by resistance)
        if damage > 0:
            hull_damage = max(0, damage - self.resistance)
            result["hull_damage"] = hull_damage

            # Every 5 hull damage causes a breach
            if hull_damage >= 5:
                breaches = hull_damage // 5
                result["breaches_caused"] = breaches

        return result
