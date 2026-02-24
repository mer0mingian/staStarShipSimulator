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

    # Extended character fields
    character_type: Mapped[Optional[str]] = mapped_column(
        String(20), default="support"
    )  # main, support, npc
    pronouns: Mapped[Optional[str]] = mapped_column(String(50))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Values, equipment (stored as JSON)
    values_json: Mapped[str] = mapped_column(Text, default="[]")
    equipment_json: Mapped[str] = mapped_column(Text, default="[]")

    # Background fields
    environment: Mapped[Optional[str]] = mapped_column(String(100))
    upbringing: Mapped[Optional[str]] = mapped_column(String(100))
    career_path: Mapped[Optional[str]] = mapped_column(String(100))

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

    @classmethod
    def from_model(cls, char: Character) -> "CharacterRecord":
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


class StarshipRecord(Base):
    """Database record for a starship."""

    __tablename__ = "starships"

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
    has_reserve_power: Mapped[bool] = mapped_column(default=True)
    shields_raised: Mapped[bool] = mapped_column(default=False)
    weapons_armed: Mapped[bool] = mapped_column(default=False)
    # NPC ships have a crew quality; None/null for player ships
    crew_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

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


class EncounterRecord(Base):
    """Database record for a combat encounter."""

    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Campaign association (nullable for backward compatibility)
    campaign_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True
    )
    # Encounter lifecycle status: draft, active, completed
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Foreign keys
    player_ship_id: Mapped[Optional[int]] = mapped_column(ForeignKey("starships.id"))
    player_character_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("characters.id")
    )
    player_position: Mapped[str] = mapped_column(String(20), default="captain")

    # Enemy ships stored as JSON array of ship IDs
    enemy_ship_ids_json: Mapped[str] = mapped_column(Text, default="[]")

    # Combat state
    momentum: Mapped[int] = mapped_column(Integer, default=0)
    threat: Mapped[int] = mapped_column(Integer, default=0)
    round: Mapped[int] = mapped_column(Integer, default=1)
    current_turn: Mapped[str] = mapped_column(String(20), default="player")
    is_active: Mapped[bool] = mapped_column(default=True)

    # Turn tracking - ships_turns_used is JSON dict: {"ship_id": turns_used}
    # Each ship gets Scale turns per round
    ships_turns_used_json: Mapped[str] = mapped_column(Text, default="{}")
    player_turns_used: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Legacy: kept for backward compat
    player_turns_total: Mapped[int] = mapped_column(
        Integer, default=1
    )  # Legacy: kept for backward compat

    # Multi-player turn tracking - JSON dict: {"player_id": {"acted": bool, "acted_at": "timestamp"}}
    players_turns_used_json: Mapped[str] = mapped_column(Text, default="{}")

    # Track who currently has claimed the turn (for race condition prevention)
    current_player_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    turn_claimed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )

    # Active effects stored as JSON
    active_effects_json: Mapped[str] = mapped_column(Text, default="[]")

    # Pending attack waiting for player defensive roll (JSON or null)
    # Structure: {"attacker_index": int, "weapon_index": int, "bonus_dice": int, "timestamp": str}
    pending_attack_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )

    # Tactical map data (hex grid with terrain)
    # Structure: {"radius": int, "tiles": [{"coord": {"q": int, "r": int}, "terrain": str, "traits": []}]}
    tactical_map_json: Mapped[str] = mapped_column(Text, default="{}")

    # Ship positions on the tactical map
    # Structure: {"player": {"q": int, "r": int}, "enemy_0": {"q": int, "r": int}, ...}
    ship_positions_json: Mapped[str] = mapped_column(Text, default="{}")

    # Viewscreen audio settings (GM-controlled)
    viewscreen_audio_enabled: Mapped[bool] = mapped_column(default=True)

    # Hailing state (JSON or null)
    # Structure: {"active": bool, "initiator": "player|gm", "target": str, "from_ship": str, "to_ship": str, "channel_open": bool, "timestamp": str}
    hailing_state_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


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


class CampaignRecord(Base):
    """Database record for a campaign."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(50), unique=True)  # UUID for URLs
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Active ship assignment (FK to starships)
    active_ship_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("starships.id"), nullable=True
    )

    # Campaign state
    is_active: Mapped[bool] = mapped_column(default=True)

    # GM password (hashed) - default is "ENGAGE1"
    gm_password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Enemy turn multiplier - scales enemy ship turns (default 0.5 = half of Scale)
    # e.g., Scale 6 ship with 0.5 multiplier gets 3 turns per round
    enemy_turn_multiplier: Mapped[Optional[float]] = mapped_column(
        default=0.5, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class CampaignPlayerRecord(Base):
    """A player in a campaign (session-based, no auth)."""

    __tablename__ = "campaign_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    character_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("characters.id"), nullable=True
    )

    # Player identity (session-based)
    player_name: Mapped[str] = mapped_column(String(50))  # Display name
    # session_token is None for unclaimed characters, set when a player claims them
    session_token: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )

    # Bridge position assignment
    position: Mapped[str] = mapped_column(String(20), default="captain")
    # Pending position change (takes effect at start of next turn)
    pending_position: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )

    is_gm: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CampaignShipRecord(Base):
    """A ship available to a campaign (ship pool)."""

    __tablename__ = "campaign_ships"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    ship_id: Mapped[int] = mapped_column(ForeignKey("starships.id"))

    # Metadata
    is_available: Mapped[bool] = mapped_column(
        default=True
    )  # Can be assigned as active
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SceneRecord(Base):
    """Scene information - first-class entity for narrative context."""

    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(primary_key=True)

    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    encounter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("encounters.id"), nullable=True, unique=True
    )

    name: Mapped[str] = mapped_column(String(100), default="New Scene")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scene_type: Mapped[str] = mapped_column(
        String(30), default="narrative"
    )  # narrative, starship_encounter, personal_encounter, social_encounter
    status: Mapped[str] = mapped_column(
        String(20), default="draft"
    )  # draft, active, completed

    stardate: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    scene_traits_json: Mapped[str] = mapped_column(Text, default="[]")
    challenges_json: Mapped[str] = mapped_column(Text, default="[]")
    characters_present_json: Mapped[str] = mapped_column(Text, default="[]")

    has_map: Mapped[bool] = mapped_column(default=False)
    tactical_map_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class NPCRecord(Base):
    """NPC Archive - global NPC database."""

    __tablename__ = "npc_archive"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    npc_type: Mapped[str] = mapped_column(
        String(20), default="minor"
    )  # major, notable, minor, npc_crew

    attributes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disciplines_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stress: Mapped[int] = mapped_column(Integer, default=5)
    stress_max: Mapped[int] = mapped_column(Integer, default=5)

    appearance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    motivation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    affiliation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ship_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("starships.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class CampaignNPCRecord(Base):
    """NPCs assigned to a campaign (manifest)."""

    __tablename__ = "campaign_npcs"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    npc_id: Mapped[int] = mapped_column(ForeignKey("npc_archive.id"))

    is_visible_to_players: Mapped[bool] = mapped_column(default=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SceneNPCRecord(Base):
    """NPCs present in a scene."""

    __tablename__ = "scene_npcs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    npc_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("npc_archive.id"), nullable=True
    )

    quick_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quick_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_visible_to_players: Mapped[bool] = mapped_column(default=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)


class CharacterTraitRecord(Base):
    """Traits assigned to characters."""

    __tablename__ = "character_traits"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))

    trait_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(50), default="gm"
    )  # gm, player, scene, campaign

    scene_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scenes.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
