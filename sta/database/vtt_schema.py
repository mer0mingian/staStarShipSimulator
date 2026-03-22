"""VTT-specific SQLAlchemy models for STA Starship Simulator."""

import json
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from sta.database.schema import Base
from sta.models.character import Character, Attributes, Disciplines
from sta.models.starship import Starship, Systems, Departments, Weapon, Breach
from sta.models.enums import DamageType, Range, SystemType, CrewQuality


class VTTCharacterRecord(Base):
    """VTT-specific character record with enhanced features for virtual tabletop use."""

    __tablename__ = "vtt_characters"

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

    # Extended character fields
    character_type: Mapped[Optional[str]] = mapped_column(
        String(20), default="support"
    )  # main, support, npc
    pronouns: Mapped[Optional[str]] = mapped_column(String(50))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Values, equipment (stored as JSON)
    # Values now include session tracking: [{"name": str, "description": str, "used_this_session": bool}]
    values_json: Mapped[str] = mapped_column(Text, default="[]")
    equipment_json: Mapped[str] = mapped_column(Text, default="[]")

    # Background fields
    environment: Mapped[Optional[str]] = mapped_column(String(100))
    upbringing: Mapped[Optional[str]] = mapped_column(String(100))
    career_path: Mapped[Optional[str]] = mapped_column(String(100))

    # VTT-specific fields
    token_url: Mapped[Optional[str]] = mapped_column(String(500))
    token_scale: Mapped[float] = mapped_column(Float, default=1.0)
    is_visible_to_players: Mapped[bool] = mapped_column(Boolean, default=True)
    vtt_position_json: Mapped[str] = mapped_column(
        Text, default="{}"
    )  # Token position data
    vtt_status_effects_json: Mapped[str] = mapped_column(
        Text, default="[]"
    )  # Active status effects

    # Character state (Ok, Fatigued, Injured, Dead)
    state: Mapped[str] = mapped_column(String(20), default="Ok")

    # Campaign and scene associations
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"))
    scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

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
            character_type=self.character_type or "support",
            pronouns=self.pronouns,
            avatar_url=self.avatar_url,
            description=self.description,
            values=json.loads(self.values_json) if self.values_json else [],
            equipment=json.loads(self.equipment_json) if self.equipment_json else [],
            environment=self.environment,
            upbringing=self.upbringing,
            career_path=self.career_path,
        )

    def validate_vtt_constraints(self) -> list[str]:
        """Validate VTT-specific constraints for character."""
        errors = []

        # Validate attribute ranges (7-12 for humanoids)
        attrs = json.loads(self.attributes_json)
        for attr_name, value in attrs.items():
            if not (7 <= value <= 12):
                errors.append(
                    f"Attribute {attr_name} must be between 7-12, got {value}"
                )

        # Validate discipline ranges (0-5)
        discs = json.loads(self.disciplines_json)
        for disc_name, value in discs.items():
            if not (0 <= value <= 5):
                errors.append(
                    f"Discipline {disc_name} must be between 0-5, got {value}"
                )

        # Validate stress ranges
        if not (0 <= self.stress <= self.stress_max):
            errors.append(
                f"Stress must be between 0-{self.stress_max}, got {self.stress}"
            )

        # Validate determination ranges
        if not (0 <= self.determination <= self.determination_max):
            errors.append(
                f"Determination must be between 0-{self.determination_max}, got {self.determination}"
            )

        return errors

    @classmethod
    def from_model(cls, char: Character) -> "VTTCharacterRecord":
        """Create database record from Character model."""
        return cls(
            name=char.name,
            species=char.species,
            rank=char.rank,
            role=char.role,
            attributes_json=json.dumps(
                {
                    "control": char.attributes.control,
                    "fitness": char.attributes.fitness,
                    "daring": char.attributes.daring,
                    "insight": char.attributes.insight,
                    "presence": char.attributes.presence,
                    "reason": char.attributes.reason,
                }
            ),
            disciplines_json=json.dumps(
                {
                    "command": char.disciplines.command,
                    "conn": char.disciplines.conn,
                    "engineering": char.disciplines.engineering,
                    "medicine": char.disciplines.medicine,
                    "science": char.disciplines.science,
                    "security": char.disciplines.security,
                }
            ),
            talents_json=json.dumps(char.talents),
            focuses_json=json.dumps(char.focuses),
            stress=char.stress,
            stress_max=char.stress_max,
            determination=char.determination,
            determination_max=char.determination_max,
            character_type=char.character_type,
            pronouns=char.pronouns,
            avatar_url=char.avatar_url,
            description=char.description,
            values_json=json.dumps(char.values),
            equipment_json=json.dumps(char.equipment),
            environment=char.environment,
            upbringing=char.upbringing,
            career_path=char.career_path,
        )


class VTTShipRecord(Base):
    """VTT-specific starship record with enhanced features for virtual tabletop use."""

    __tablename__ = "vtt_ships"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    ship_class: Mapped[str] = mapped_column(String(50))
    ship_registry: Mapped[Optional[str]] = mapped_column(String(20))
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
    has_reserve_power: Mapped[bool] = mapped_column(Boolean, default=True)
    shields_raised: Mapped[bool] = mapped_column(Boolean, default=False)
    weapons_armed: Mapped[bool] = mapped_column(Boolean, default=False)
    # NPC ships have a crew quality; None/null for player ships
    crew_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # VTT-specific fields
    token_url: Mapped[Optional[str]] = mapped_column(String(500))
    token_scale: Mapped[float] = mapped_column(Float, default=1.0)
    is_visible_to_players: Mapped[bool] = mapped_column(Boolean, default=True)
    vtt_position_json: Mapped[str] = mapped_column(
        Text, default="{}"
    )  # Ship position on tactical map
    vtt_status_effects_json: Mapped[str] = mapped_column(
        Text, default="[]"
    )  # Active status effects
    vtt_facing_direction: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # Ship facing (e.g., "forward", "port")

    # Campaign and scene associations
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"))
    scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

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
            registry=self.ship_registry,
            crew_quality=crew_quality_enum,
        )
        return ship

    def validate_vtt_constraints(self) -> list[str]:
        """Validate VTT-specific constraints for ship."""
        errors = []

        # Validate system ranges (7-12)
        systems = json.loads(self.systems_json)
        for system_name, value in systems.items():
            if not (7 <= value <= 12):
                errors.append(f"System {system_name} must be between 7-12, got {value}")

        # Validate department ranges (0-5)
        departments = json.loads(self.departments_json)
        for dept_name, value in departments.items():
            if not (0 <= value <= 5):
                errors.append(
                    f"Department {dept_name} must be between 0-5, got {value}"
                )

        # Validate scale (1-7)
        if not (1 <= self.scale <= 7):
            errors.append(f"Scale must be between 1-7, got {self.scale}")

        # Validate shields
        if self.shields_max < 0:
            errors.append(f"Shields max cannot be negative, got {self.shields_max}")
        if self.shields < 0 or self.shields > self.shields_max:
            errors.append(
                f"Shields must be between 0-{self.shields_max}, got {self.shields}"
            )

        return errors

    @classmethod
    def from_model(cls, ship: Starship) -> "VTTShipRecord":
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
            {"system": b.system.value, "potency": b.potency} for b in ship.breaches
        ]

        return cls(
            name=ship.name,
            ship_class=ship.ship_class,
            ship_registry=ship.registry,
            scale=ship.scale,
            systems_json=json.dumps(
                {
                    "comms": ship.systems.comms,
                    "computers": ship.systems.computers,
                    "engines": ship.systems.engines,
                    "sensors": ship.systems.sensors,
                    "structure": ship.systems.structure,
                    "weapons": ship.systems.weapons,
                }
            ),
            departments_json=json.dumps(
                {
                    "command": ship.departments.command,
                    "conn": ship.departments.conn,
                    "engineering": ship.departments.engineering,
                    "medicine": ship.departments.medicine,
                    "science": ship.departments.science,
                    "security": ship.departments.security,
                }
            ),
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


class UniverseLibraryRecord(Base):
    """Global library of game elements for VTT use."""

    __tablename__ = "universe_library"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(
        String(50)
    )  # species, faction, location, etc.
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    reference_data_json: Mapped[str] = mapped_column(
        Text, default="{}"
    )  # Additional metadata

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class UniverseItemRecord(Base):
    """Library of reusable characters and ships for campaign use."""

    __tablename__ = "universe_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))  # pcs, npcs, creatures, ships
    item_type: Mapped[str] = mapped_column(String(20))  # character, ship
    data_json: Mapped[str] = mapped_column(Text)  # Full serialized character/ship data
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class TraitRecord(Base):
    """Individual trait definition for characters and ships."""

    __tablename__ = "traits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text)
    trait_type: Mapped[str] = mapped_column(String(50))  # character, ship, weapon, etc.
    game_effects_json: Mapped[str] = mapped_column(
        Text, default="{}"
    )  # Mechanical effects
    is_positive: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class TalentRecord(Base):
    """Individual talent definition for characters."""

    __tablename__ = "talents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text)
    discipline: Mapped[str] = mapped_column(String(20))  # Associated discipline
    rank: Mapped[int] = mapped_column(Integer, default=1)  # Talent rank/level
    game_effects_json: Mapped[str] = mapped_column(
        Text, default="{}"
    )  # Mechanical effects

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class WeaponRecord(Base):
    """Individual weapon definition for ships and characters."""

    __tablename__ = "weapons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    weapon_type: Mapped[str] = mapped_column(String(20))  # energy, torpedo, kinetic
    damage: Mapped[int] = mapped_column(Integer, default=0)
    range: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # close, medium, long, extreme
    qualities_json: Mapped[str] = mapped_column(Text, default="[]")  # Special qualities
    description: Mapped[Optional[str]] = mapped_column(Text)
    requires_calibration: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_system: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # cannons, banks, etc.

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class LogEntryRecord(Base):
    """Log entries for character narrative tracking.

    Supports three types of logs:
    - PERSONAL: Character roleplay notes visible to all other players
    - MISSION: Auto-generated entries for scene/mission events
    - VALUE: Auto-generated entries for Value interactions
    """

    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(
        ForeignKey("vtt_characters.id"), nullable=False
    )
    log_type: Mapped[str] = mapped_column(
        String(20), default="MISSION"
    )  # PERSONAL, MISSION, VALUE
    content: Mapped[str] = mapped_column(Text, default="")
    event_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # e.g., "scene_enter", "scene_exit", "value_challenged", "value_complied"
    character_name: Mapped[str] = mapped_column(
        String(100)
    )  # Denormalized for easier queries
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # User who created this entry (for PERSONAL logs)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "character_id": self.character_id,
            "log_type": self.log_type,
            "content": self.content,
            "event_type": self.event_type,
            "character_name": self.character_name,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
