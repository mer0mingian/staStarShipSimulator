"""Random character generator for STA."""

import random
from sta.models.character import Character, Attributes, Disciplines
from sta.models.enums import Position
from .data import (
    FOCUSES, GENERAL_TALENTS, SPECIES, RANKS,
    FIRST_NAMES, LAST_NAMES
)


def random_attributes(total: int = 56) -> Attributes:
    """
    Generate random attributes totaling approximately the given amount.
    Each attribute will be between 7 and 12.
    """
    # Start with base values
    values = [7, 7, 7, 7, 7, 7]  # 42 total
    remaining = total - 42

    # Distribute remaining points randomly
    while remaining > 0:
        idx = random.randint(0, 5)
        if values[idx] < 12:
            values[idx] += 1
            remaining -= 1

    random.shuffle(values)
    return Attributes(
        control=values[0],
        fitness=values[1],
        daring=values[2],
        insight=values[3],
        presence=values[4],
        reason=values[5]
    )


def random_disciplines(total: int = 16) -> Disciplines:
    """
    Generate random disciplines totaling approximately the given amount.
    Each discipline will be between 1 and 5.
    """
    # Start with base values
    values = [1, 1, 1, 1, 1, 1]  # 6 total
    remaining = total - 6

    # Distribute remaining points randomly
    while remaining > 0:
        idx = random.randint(0, 5)
        if values[idx] < 5:
            values[idx] += 1
            remaining -= 1

    random.shuffle(values)
    return Disciplines(
        command=values[0],
        conn=values[1],
        engineering=values[2],
        medicine=values[3],
        science=values[4],
        security=values[5]
    )


def random_name(species: str) -> str:
    """Generate a random name based on species."""
    first_names = FIRST_NAMES.get(species, FIRST_NAMES["Human"])
    last_names = LAST_NAMES.get(species, [])

    first = random.choice(first_names)

    if last_names:
        if species == "Bajoran":
            # Bajoran names: family name first
            return f"{random.choice(last_names)} {first}"
        else:
            return f"{first} {random.choice(last_names)}"
    return first


def random_focuses(disciplines: Disciplines, count: int = 4) -> list[str]:
    """
    Generate random focuses, weighted toward higher disciplines.
    """
    # Weight disciplines by their value
    discipline_names = ["command", "conn", "engineering", "medicine", "science", "security"]
    weights = [
        disciplines.command,
        disciplines.conn,
        disciplines.engineering,
        disciplines.medicine,
        disciplines.science,
        disciplines.security,
    ]

    focuses = []
    used_focuses = set()

    for _ in range(count):
        # Pick a discipline weighted by value
        disc = random.choices(discipline_names, weights=weights)[0]
        available = [f for f in FOCUSES[disc] if f not in used_focuses]

        if available:
            focus = random.choice(available)
            focuses.append(focus)
            used_focuses.add(focus)

    return focuses


def random_talents(count: int = 2) -> list[str]:
    """Generate random talents from the general talent pool."""
    return random.sample(GENERAL_TALENTS, min(count, len(GENERAL_TALENTS)))


def random_position() -> Position:
    """Pick a random bridge position."""
    return random.choice(list(Position))


def generate_character(
    name: str | None = None,
    species: str | None = None,
    rank: str | None = None,
    position: Position | None = None,
    attribute_total: int = 56,
    discipline_total: int = 16,
    talent_count: int = 2,
    focus_count: int = 4,
) -> Character:
    """
    Generate a fully random character.

    Args:
        name: Character name (random if None)
        species: Character species (random if None)
        rank: Character rank (random if None)
        position: Bridge position (random if None)
        attribute_total: Total attribute points to distribute
        discipline_total: Total discipline points to distribute
        talent_count: Number of talents to assign
        focus_count: Number of focuses to assign

    Returns:
        A randomly generated Character
    """
    # Pick species first since it affects name
    if species is None:
        species = random.choice(SPECIES)

    if name is None:
        name = random_name(species)

    if rank is None:
        rank = random.choice(RANKS)

    if position is None:
        position = random_position()

    attributes = random_attributes(attribute_total)
    disciplines = random_disciplines(discipline_total)
    focuses = random_focuses(disciplines, focus_count)
    talents = random_talents(talent_count)

    # Calculate stress based on Fitness
    base_stress = 5 + (attributes.fitness - 7) // 2
    if "Tough" in talents:
        base_stress += 2

    return Character(
        name=name,
        attributes=attributes,
        disciplines=disciplines,
        talents=talents,
        focuses=focuses,
        stress=base_stress,
        stress_max=base_stress,
        rank=rank,
        species=species,
        role=position.value.title(),
    )
