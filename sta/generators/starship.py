"""Random starship generator for STA."""

import random
from typing import Optional
from sta.models.starship import Starship, Systems, Departments, Weapon
from sta.models.enums import DamageType, Range, CrewQuality
from .data import (
    SHIP_CLASSES, SHIP_TALENTS, WEAPON_TEMPLATES,
    SHIP_NAMES_FEDERATION, SHIP_NAMES_KLINGON, SHIP_NAMES_ROMULAN
)


def get_weapon(name: str) -> Weapon:
    """Create a Weapon from a template name."""
    template = WEAPON_TEMPLATES.get(name)
    if template is None:
        # Default phaser if unknown
        template = WEAPON_TEMPLATES["Phaser Banks"]

    damage_type = DamageType.TORPEDO if template["type"] == "torpedo" else DamageType.ENERGY
    range_map = {"close": Range.CLOSE, "medium": Range.MEDIUM, "long": Range.LONG}

    return Weapon(
        name=name,
        weapon_type=damage_type,
        damage=template["damage"],
        range=range_map.get(template["range"], Range.MEDIUM),
        qualities=template.get("qualities", []),
        requires_calibration="Calibration" in template.get("qualities", []),
    )


def random_ship_name(faction: str = "Federation") -> str:
    """Generate a random ship name with appropriate prefix."""
    if faction == "Klingon":
        return f"IKS {random.choice(SHIP_NAMES_KLINGON)}"
    elif faction == "Romulan":
        return f"IRW {random.choice(SHIP_NAMES_ROMULAN)}"
    else:
        return f"USS {random.choice(SHIP_NAMES_FEDERATION)}"


def random_registry(ship_class: str) -> str:
    """Generate a random registry number."""
    # Constitution class: 1700-1799
    # Most others: 1000-99999
    base = random.randint(1000, 79999)
    return f"NCC-{base}"


def generate_starship(
    name: str | None = None,
    ship_class: str | None = None,
    registry: str | None = None,
    talent_count: int = 2,
    faction: str = "Federation",
    crew_quality: Optional[CrewQuality] = None,
) -> Starship:
    """
    Generate a fully random starship.

    Args:
        name: Ship name (random if None)
        ship_class: Ship class (random if None)
        registry: Registry number (random if None)
        talent_count: Number of talents to assign
        faction: Ship faction (Federation, Klingon, Romulan)
        crew_quality: NPC crew quality (None for player ships)

    Returns:
        A randomly generated Starship
    """
    # Filter classes by faction if specified
    available_classes = {
        k: v for k, v in SHIP_CLASSES.items()
        if v.get("faction", "Federation") == faction or faction == "any"
    }

    # If no faction-specific classes, use all
    if not available_classes:
        available_classes = SHIP_CLASSES

    if ship_class is None:
        ship_class = random.choice(list(available_classes.keys()))

    class_data = SHIP_CLASSES.get(ship_class, SHIP_CLASSES["Constitution"])

    if name is None:
        name = random_ship_name(class_data.get("faction", "Federation"))

    if registry is None:
        registry = random_registry(ship_class)

    # Create systems from class data
    sys_data = class_data["systems"]
    systems = Systems(
        comms=sys_data["comms"],
        computers=sys_data["computers"],
        engines=sys_data["engines"],
        sensors=sys_data["sensors"],
        structure=sys_data["structure"],
        weapons=sys_data["weapons"],
    )

    # Create departments from class data
    dept_data = class_data["departments"]
    departments = Departments(
        command=dept_data["command"],
        conn=dept_data["conn"],
        engineering=dept_data["engineering"],
        medicine=dept_data["medicine"],
        science=dept_data["science"],
        security=dept_data["security"],
    )

    # Create weapons
    weapons = [get_weapon(w) for w in class_data.get("weapons", [])]

    # Pick random talents
    talents = random.sample(SHIP_TALENTS, min(talent_count, len(SHIP_TALENTS)))

    # Build traits
    traits = [
        f"{class_data.get('faction', 'Federation')} Starship",
        f"{ship_class}-class",
    ]

    return Starship(
        name=name,
        ship_class=ship_class,
        scale=class_data["scale"],
        systems=systems,
        departments=departments,
        weapons=weapons,
        talents=talents,
        traits=traits,
        registry=registry,
        crew_quality=crew_quality,
    )


def generate_enemy_ship(
    difficulty: str = "standard",
    faction: str | None = None,
    crew_quality: Optional[CrewQuality] = None,
) -> Starship:
    """
    Generate an enemy ship appropriate for combat.

    Args:
        difficulty: "easy", "standard", or "hard"
        faction: Enemy faction (random if None)
        crew_quality: NPC crew quality (defaults based on difficulty if None)

    Returns:
        An enemy Starship (with crew_quality set for NPC rolls)
    """
    if faction is None:
        faction = random.choice(["Klingon", "Romulan"])

    # Pick class based on difficulty and faction
    if faction == "Klingon":
        if difficulty == "easy":
            ship_class = "Bird-of-Prey"
        elif difficulty == "hard":
            ship_class = "D7 Battlecruiser"
        else:
            ship_class = random.choice(["Bird-of-Prey", "D7 Battlecruiser"])
    elif faction == "Romulan":
        ship_class = "Warbird"
    else:
        # Generic enemy
        ship_class = random.choice(["Bird-of-Prey", "D7 Battlecruiser", "Warbird"])

    # Default crew quality based on difficulty if not specified
    if crew_quality is None:
        crew_quality = {
            "easy": CrewQuality.PROFICIENT,
            "standard": CrewQuality.TALENTED,
            "hard": CrewQuality.EXCEPTIONAL,
        }.get(difficulty, CrewQuality.TALENTED)

    return generate_starship(
        ship_class=ship_class,
        faction=faction,
        talent_count=1 if difficulty == "easy" else 2,
        crew_quality=crew_quality,
    )
