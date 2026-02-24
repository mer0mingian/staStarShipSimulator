"""Character data model for STA."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Attributes:
    """Character attributes (typically 7-12 each, max 15)."""

    control: int = 7
    fitness: int = 7
    daring: int = 7
    insight: int = 7
    presence: int = 7
    reason: int = 7

    def total(self) -> int:
        """Sum of all attributes."""
        return (
            self.control
            + self.fitness
            + self.daring
            + self.insight
            + self.presence
            + self.reason
        )

    def get(self, name: str) -> int:
        """Get attribute by name."""
        return getattr(self, name.lower())


@dataclass
class Disciplines:
    """Character disciplines (typically 1-5 each)."""

    command: int = 1
    conn: int = 1
    engineering: int = 1
    medicine: int = 1
    science: int = 1
    security: int = 1

    def total(self) -> int:
        """Sum of all disciplines."""
        return (
            self.command
            + self.conn
            + self.engineering
            + self.medicine
            + self.science
            + self.security
        )

    def get(self, name: str) -> int:
        """Get discipline by name."""
        return getattr(self, name.lower())


@dataclass
class Character:
    """A player or NPC character."""

    name: str
    attributes: Attributes
    disciplines: Disciplines
    talents: list[str] = field(default_factory=list)
    focuses: list[str] = field(default_factory=list)
    stress: int = 5
    stress_max: int = 5
    determination: int = 1
    determination_max: int = 3
    rank: Optional[str] = None
    species: Optional[str] = None
    role: Optional[str] = None

    # Extended fields
    character_type: str = "support"  # main, support, npc
    pronouns: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    values: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    environment: Optional[str] = None
    upbringing: Optional[str] = None
    career_path: Optional[str] = None

    def target_number(self, attribute: str, discipline: str) -> int:
        """Calculate target number for a task (attribute + discipline)."""
        return self.attributes.get(attribute) + self.disciplines.get(discipline)

    def focus_applies(self, focus: str) -> bool:
        """Check if a focus applies (case-insensitive partial match)."""
        focus_lower = focus.lower()
        return any(focus_lower in f.lower() for f in self.focuses)

    def critical_range(self, discipline: str) -> int:
        """
        Get the critical success range for a discipline.
        Rolls at or below this value count as 2 successes when focus applies.
        """
        return self.disciplines.get(discipline)
