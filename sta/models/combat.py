"""Combat and encounter data models for STA."""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
import uuid

from .enums import Position, Range, ActionType
from .character import Character
from .starship import Starship


@dataclass
class ActiveEffect:
    """A temporary effect active during combat.

    Examples:
    - Calibrate Weapons: damage_bonus=1, applies_to="attack", duration="next_action"
    - Modulate Shields: resistance_bonus=2, applies_to="defense", duration="end_of_turn"
    - Targeting Solution: can_reroll=True, applies_to="attack", duration="next_action"
    """
    source_action: str  # Name of the action that created this effect
    applies_to: str  # What this effect applies to: "attack", "defense", "sensor", "all"
    duration: Literal["next_action", "end_of_turn", "end_of_round"]  # How long it lasts
    source_ship: Optional[str] = None  # Name of the ship that created this effect (for NPC effects)

    # Effect modifiers (at least one should be set)
    damage_bonus: int = 0
    resistance_bonus: int = 0
    difficulty_modifier: int = 0  # Positive = harder, negative = easier
    can_reroll: bool = False
    can_choose_system: bool = False  # For targeted attacks
    piercing: bool = False  # Ignore resistance

    # Special data for specific actions
    weapon_index: Optional[int] = None  # For Defensive Fire - which weapon to use for counterattack
    is_opposed: bool = False  # For Defensive Fire / Evasive Action - attacks become opposed rolls

    # Metadata
    created_round: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def applies_to_action(self, action_type: str) -> bool:
        """Check if this effect applies to a given action type."""
        return self.applies_to == "all" or self.applies_to == action_type

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source_action": self.source_action,
            "source_ship": self.source_ship,
            "applies_to": self.applies_to,
            "duration": self.duration,
            "damage_bonus": self.damage_bonus,
            "resistance_bonus": self.resistance_bonus,
            "difficulty_modifier": self.difficulty_modifier,
            "can_reroll": self.can_reroll,
            "can_choose_system": self.can_choose_system,
            "piercing": self.piercing,
            "weapon_index": self.weapon_index,
            "is_opposed": self.is_opposed,
            "created_round": self.created_round,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActiveEffect":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            source_action=data["source_action"],
            source_ship=data.get("source_ship"),
            applies_to=data["applies_to"],
            duration=data["duration"],
            damage_bonus=data.get("damage_bonus", 0),
            resistance_bonus=data.get("resistance_bonus", 0),
            difficulty_modifier=data.get("difficulty_modifier", 0),
            can_reroll=data.get("can_reroll", False),
            can_choose_system=data.get("can_choose_system", False),
            piercing=data.get("piercing", False),
            weapon_index=data.get("weapon_index"),
            is_opposed=data.get("is_opposed", False),
            created_round=data.get("created_round", 1),
        )


@dataclass
class TaskResult:
    """Result of a 2d20 task roll."""
    rolls: list[int]
    target_number: int
    successes: int
    complications: int
    difficulty: int
    focus_value: Optional[int] = None
    momentum_generated: int = 0
    succeeded: bool = False
    # Ship assistance fields (optional, used for ship-assisted rolls)
    ship_target_number: Optional[int] = None
    ship_roll: Optional[int] = None
    ship_successes: int = 0

    def __post_init__(self):
        """Calculate if the task succeeded."""
        self.succeeded = self.successes >= self.difficulty
        if self.succeeded:
            self.momentum_generated = max(0, self.successes - self.difficulty)


@dataclass
class CombatAction:
    """A single action taken during combat."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    round: int = 1
    actor_name: str = ""
    actor_type: str = "player"  # "player" or "enemy"
    ship_name: str = ""
    action_name: str = ""
    action_type: ActionType = ActionType.MAJOR
    description: str = ""
    task_result: Optional[TaskResult] = None
    damage_dealt: int = 0
    momentum_spent: int = 0
    threat_spent: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ShipCombatant:
    """A ship participating in combat with its current state."""
    ship: Starship
    faction: str = "player"  # "player" or "enemy"
    zone: int = 0  # Zone position on the map
    has_acted: bool = False
    minor_actions_used: int = 0
    major_actions_used: int = 0
    evasive_action_active: bool = False
    attack_pattern_active: bool = False
    calibrate_weapons_active: bool = False

    @property
    def minor_actions_remaining(self) -> int:
        """Minor actions remaining this turn (base 1)."""
        return max(0, 1 - self.minor_actions_used)

    @property
    def major_actions_remaining(self) -> int:
        """Major actions remaining this turn (base 1)."""
        return max(0, 1 - self.major_actions_used)

    def reset_turn(self) -> None:
        """Reset action counts for a new turn."""
        self.has_acted = False
        self.minor_actions_used = 0
        self.major_actions_used = 0

    def reset_round(self) -> None:
        """Reset round-based effects."""
        self.evasive_action_active = False
        self.attack_pattern_active = False
        self.reset_turn()

    def range_to(self, other: "ShipCombatant") -> Range:
        """Calculate range to another combatant based on zones."""
        distance = abs(self.zone - other.zone)
        if distance == 0:
            return Range.CLOSE
        elif distance == 1:
            return Range.MEDIUM
        elif distance == 2:
            return Range.LONG
        return Range.EXTREME


@dataclass
class Encounter:
    """A combat encounter with all participants and state."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unnamed Encounter"

    # Player ship and character
    player_ship: Optional[ShipCombatant] = None
    player_character: Optional[Character] = None
    player_position: Position = Position.CAPTAIN

    # Enemy ships
    enemy_ships: list[ShipCombatant] = field(default_factory=list)

    # Shared resources
    momentum: int = 0
    momentum_max: int = 6
    threat: int = 0

    # Turn tracking
    round: int = 1
    current_turn: str = "player"  # "player" or "enemy"
    turn_order: list[str] = field(default_factory=list)  # Ship names in order

    # Combat log
    action_log: list[CombatAction] = field(default_factory=list)

    # Active effects (buffs, modifiers, etc.)
    active_effects: list[ActiveEffect] = field(default_factory=list)

    # Encounter state
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def add_momentum(self, amount: int) -> int:
        """Add momentum, respecting the cap. Returns actual amount added."""
        old = self.momentum
        self.momentum = min(self.momentum_max, self.momentum + amount)
        return self.momentum - old

    def spend_momentum(self, amount: int) -> bool:
        """Spend momentum if available. Returns True if successful."""
        if self.momentum >= amount:
            self.momentum -= amount
            return True
        return False

    def add_threat(self, amount: int) -> None:
        """Add to the threat pool."""
        self.threat += amount

    def spend_threat(self, amount: int) -> bool:
        """Spend threat if available. Returns True if successful."""
        if self.threat >= amount:
            self.threat -= amount
            return True
        return False

    def next_turn(self) -> None:
        """Advance to the next turn."""
        if self.current_turn == "player":
            self.current_turn = "enemy"
            if self.player_ship:
                self.player_ship.has_acted = True
        else:
            self.current_turn = "player"
            # Reset all ships for new round
            self.round += 1
            if self.player_ship:
                self.player_ship.reset_round()
            for enemy in self.enemy_ships:
                enemy.reset_round()

    def get_current_actor_ship(self) -> Optional[ShipCombatant]:
        """Get the ship that should act this turn."""
        if self.current_turn == "player":
            return self.player_ship
        # For now, just return first enemy that hasn't acted
        for enemy in self.enemy_ships:
            if not enemy.has_acted:
                return enemy
        return None

    def log_action(self, action: CombatAction) -> None:
        """Add an action to the combat log."""
        action.round = self.round
        self.action_log.append(action)

    def all_enemies_destroyed(self) -> bool:
        """Check if all enemy ships are destroyed (structure disabled)."""
        from .enums import SystemType
        return all(
            enemy.ship.is_system_disabled(SystemType.STRUCTURE)
            for enemy in self.enemy_ships
        )

    def player_ship_destroyed(self) -> bool:
        """Check if player ship is destroyed."""
        from .enums import SystemType
        if self.player_ship:
            return self.player_ship.ship.is_system_disabled(SystemType.STRUCTURE)
        return False

    # ===== Active Effects Management =====

    def add_effect(self, effect: ActiveEffect) -> None:
        """Add an active effect to the encounter."""
        effect.created_round = self.round
        self.active_effects.append(effect)

    def get_effects(self, applies_to: Optional[str] = None) -> list[ActiveEffect]:
        """Get all active effects, optionally filtered by what they apply to."""
        if applies_to is None:
            return self.active_effects
        return [e for e in self.active_effects if e.applies_to_action(applies_to)]

    def clear_effects(self, applies_to: Optional[str] = None, duration: Optional[str] = None) -> list[ActiveEffect]:
        """Clear effects matching the criteria. Returns list of cleared effects."""
        cleared = []
        remaining = []

        for effect in self.active_effects:
            should_clear = True

            if applies_to is not None and not effect.applies_to_action(applies_to):
                should_clear = False
            if duration is not None and effect.duration != duration:
                should_clear = False

            if should_clear:
                cleared.append(effect)
            else:
                remaining.append(effect)

        self.active_effects = remaining
        return cleared

    def clear_turn_effects(self) -> None:
        """Clear all effects that last until end of turn."""
        self.clear_effects(duration="end_of_turn")

    def clear_round_effects(self) -> None:
        """Clear all effects that last until end of round."""
        self.clear_effects(duration="end_of_round")
