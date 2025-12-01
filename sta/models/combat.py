"""Combat and encounter data models for STA."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid

from .enums import Position, Range, ActionType
from .character import Character
from .starship import Starship


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
