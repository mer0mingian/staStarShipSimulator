"""SQLAlchemy table definitions for STA Starship Simulator."""

import json
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from sta.models.character import Character, Attributes, Disciplines
from sta.models.starship import Starship, Systems, Departments, Weapon, Breach
from sta.models.combat import Encounter, ShipCombatant
from sta.models.enums import Position, DamageType, Range, SystemType, CrewQuality


class Base(DeclarativeBase):
    pass


class CharacterRecord(Base):
    """Database record for a character."""
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    species: Mapped[Optional[str]] = mapped_column(String(50))
    rank: Mapped[Optional[str]] = mapped_column(String(50))
    role: Mapped[Optional[str]] = mapped_column(String(50))

    # Attributes stored as JSON
    attributes_json: Mapped[str] = mapped_column(Text)
    # Disciplines stored as JSON
    disciplines_json: Mapped[str] = mapped_column(Text)

    talents_json: Mapped[str] = mapped_column(Text, default="[]")
    focuses_json: Mapped[str] = mapped_column(Text, default="[]")

    stress: Mapped[int] = mapped_column(Integer, default=5)
    stress_max: Mapped[int] = mapped_column(Integer, default=5)
    determination: Mapped[int] = mapped_column(Integer, default=1)
    determination_max: Mapped[int] = mapped_column(Integer, default=3)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_model(self) -> Character:
        """Convert database record to Character model."""
        attrs = json.loads(self.attributes_json)
        discs = json.loads(self.disciplines_json)

        return Character(
            name=self.name,
            attributes=Attributes(**attrs),
            disciplines=Disciplines(**discs),
            talents=json.loads(self.talents_json),
            focuses=json.loads(self.focuses_json),
            stress=self.stress,
            stress_max=self.stress_max,
            determination=self.determination,
            determination_max=self.determination_max,
            rank=self.rank,
            species=self.species,
            role=self.role,
        )

    @classmethod
    def from_model(cls, char: Character) -> "CharacterRecord":
        """Create database record from Character model."""
        return cls(
            name=char.name,
            species=char.species,
            rank=char.rank,
            role=char.role,
            attributes_json=json.dumps({
                "control": char.attributes.control,
                "fitness": char.attributes.fitness,
                "daring": char.attributes.daring,
                "insight": char.attributes.insight,
                "presence": char.attributes.presence,
                "reason": char.attributes.reason,
            }),
            disciplines_json=json.dumps({
                "command": char.disciplines.command,
                "conn": char.disciplines.conn,
                "engineering": char.disciplines.engineering,
                "medicine": char.disciplines.medicine,
                "science": char.disciplines.science,
                "security": char.disciplines.security,
            }),
            talents_json=json.dumps(char.talents),
            focuses_json=json.dumps(char.focuses),
            stress=char.stress,
            stress_max=char.stress_max,
            determination=char.determination,
            determination_max=char.determination_max,
        )


class StarshipRecord(Base):
    """Database record for a starship."""
    __tablename__ = "starships"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    ship_class: Mapped[str] = mapped_column(String(50))
    registry: Mapped[Optional[str]] = mapped_column(String(20))
    scale: Mapped[int] = mapped_column(Integer)

    # Systems stored as JSON
    systems_json: Mapped[str] = mapped_column(Text)
    # Departments stored as JSON
    departments_json: Mapped[str] = mapped_column(Text)

    weapons_json: Mapped[str] = mapped_column(Text, default="[]")
    talents_json: Mapped[str] = mapped_column(Text, default="[]")
    traits_json: Mapped[str] = mapped_column(Text, default="[]")
    breaches_json: Mapped[str] = mapped_column(Text, default="[]")

    shields: Mapped[int] = mapped_column(Integer, default=0)
    shields_max: Mapped[int] = mapped_column(Integer, default=0)
    resistance: Mapped[int] = mapped_column(Integer, default=0)
    has_reserve_power: Mapped[bool] = mapped_column(default=True)
    shields_raised: Mapped[bool] = mapped_column(default=False)
    weapons_armed: Mapped[bool] = mapped_column(default=False)
    # NPC ships have a crew quality; None/null for player ships
    crew_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_model(self) -> Starship:
        """Convert database record to Starship model."""
        sys_data = json.loads(self.systems_json)
        dept_data = json.loads(self.departments_json)
        weapons_data = json.loads(self.weapons_json)
        breaches_data = json.loads(self.breaches_json)

        weapons = [
            Weapon(
                name=w["name"],
                weapon_type=DamageType(w["weapon_type"]),
                damage=w["damage"],
                range=Range(w["range"]),
                qualities=w.get("qualities", []),
                requires_calibration=w.get("requires_calibration", False),
            )
            for w in weapons_data
        ]

        breaches = [
            Breach(system=SystemType(b["system"]), potency=b["potency"])
            for b in breaches_data
        ]

        # Convert crew_quality string to enum if present
        crew_quality_enum = None
        if self.crew_quality:
            crew_quality_enum = CrewQuality(self.crew_quality)

        ship = Starship(
            name=self.name,
            ship_class=self.ship_class,
            scale=self.scale,
            systems=Systems(**sys_data),
            departments=Departments(**dept_data),
            weapons=weapons,
            talents=json.loads(self.talents_json),
            traits=json.loads(self.traits_json),
            breaches=breaches,
            shields=self.shields,
            shields_max=self.shields_max,
            resistance=self.resistance,
            has_reserve_power=self.has_reserve_power,
            shields_raised=self.shields_raised,
            weapons_armed=self.weapons_armed,
            registry=self.registry,
            crew_quality=crew_quality_enum,
        )
        return ship

    @classmethod
    def from_model(cls, ship: Starship) -> "StarshipRecord":
        """Create database record from Starship model."""
        weapons_data = [
            {
                "name": w.name,
                "weapon_type": w.weapon_type.value,
                "damage": w.damage,
                "range": w.range.value,
                "qualities": w.qualities,
                "requires_calibration": w.requires_calibration,
            }
            for w in ship.weapons
        ]

        breaches_data = [
            {"system": b.system.value, "potency": b.potency}
            for b in ship.breaches
        ]

        return cls(
            name=ship.name,
            ship_class=ship.ship_class,
            registry=ship.registry,
            scale=ship.scale,
            systems_json=json.dumps({
                "comms": ship.systems.comms,
                "computers": ship.systems.computers,
                "engines": ship.systems.engines,
                "sensors": ship.systems.sensors,
                "structure": ship.systems.structure,
                "weapons": ship.systems.weapons,
            }),
            departments_json=json.dumps({
                "command": ship.departments.command,
                "conn": ship.departments.conn,
                "engineering": ship.departments.engineering,
                "medicine": ship.departments.medicine,
                "science": ship.departments.science,
                "security": ship.departments.security,
            }),
            weapons_json=json.dumps(weapons_data),
            talents_json=json.dumps(ship.talents),
            traits_json=json.dumps(ship.traits),
            breaches_json=json.dumps(breaches_data),
            shields=ship.shields,
            shields_max=ship.shields_max,
            resistance=ship.resistance,
            has_reserve_power=ship.has_reserve_power,
            shields_raised=ship.shields_raised,
            weapons_armed=ship.weapons_armed,
            crew_quality=ship.crew_quality.value if ship.crew_quality else None,
        )


class EncounterRecord(Base):
    """Database record for a combat encounter."""
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))

    # Foreign keys
    player_ship_id: Mapped[Optional[int]] = mapped_column(ForeignKey("starships.id"))
    player_character_id: Mapped[Optional[int]] = mapped_column(ForeignKey("characters.id"))
    player_position: Mapped[str] = mapped_column(String(20), default="captain")

    # Enemy ships stored as JSON array of ship IDs
    enemy_ship_ids_json: Mapped[str] = mapped_column(Text, default="[]")

    # Combat state
    momentum: Mapped[int] = mapped_column(Integer, default=0)
    threat: Mapped[int] = mapped_column(Integer, default=0)
    round: Mapped[int] = mapped_column(Integer, default=1)
    current_turn: Mapped[str] = mapped_column(String(20), default="player")
    is_active: Mapped[bool] = mapped_column(default=True)

    # Active effects stored as JSON
    active_effects_json: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CombatLogRecord(Base):
    """Database record for combat log entries."""
    __tablename__ = "combat_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id"))
    round: Mapped[int] = mapped_column(Integer)

    actor_name: Mapped[str] = mapped_column(String(100))
    actor_type: Mapped[str] = mapped_column(String(20))  # "player" or "enemy"
    ship_name: Mapped[str] = mapped_column(String(100))

    action_name: Mapped[str] = mapped_column(String(50))
    action_type: Mapped[str] = mapped_column(String(10))  # "minor" or "major"
    description: Mapped[str] = mapped_column(Text)

    # Task result stored as JSON
    task_result_json: Mapped[Optional[str]] = mapped_column(Text)

    damage_dealt: Mapped[int] = mapped_column(Integer, default=0)
    momentum_spent: Mapped[int] = mapped_column(Integer, default=0)
    threat_spent: Mapped[int] = mapped_column(Integer, default=0)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
