"""
Ship movement mechanics for STA tactical combat.

Implements Conn station movement actions:
- Impulse: Minor action, move up to 2 hexes
- Thrusters: Minor action, enter/exit contact in same hex

Movement costs are paid in Momentum (or Threat for player's benefit to GM).
Hazardous terrain deals damage if Threat is used instead of Momentum.
"""

from dataclasses import dataclass
from typing import Optional

from sta.models.combat import HexCoord, TacticalMap, HexTile
from sta.models.enums import TerrainType


@dataclass
class MovementResult:
    """Result of a movement action."""
    success: bool
    message: str
    new_position: Optional[HexCoord] = None
    momentum_cost: int = 0
    threat_added: int = 0
    hazard_damage: int = 0  # Challenge dice if moving through hazardous terrain with Threat
    path: list[HexCoord] = None  # Hexes traversed

    def __post_init__(self):
        if self.path is None:
            self.path = []


@dataclass
class ValidMove:
    """A valid destination for movement."""
    coord: HexCoord
    cost: int  # Momentum cost to reach this hex
    path: list[HexCoord]  # Path taken (for cost calculation)
    terrain: TerrainType


def get_neighbors(coord: HexCoord) -> list[HexCoord]:
    """Get all 6 adjacent hex coordinates."""
    return coord.neighbors()


def calculate_path_cost(path: list[HexCoord], tactical_map: TacticalMap) -> int:
    """
    Calculate the total Momentum cost for a path.

    Cost is based on the terrain of hexes ENTERED (not the starting hex).
    Per STA rules, cost is paid when leaving difficult terrain.
    """
    if len(path) <= 1:
        return 0

    total_cost = 0
    # Cost is for entering each hex after the first
    for i in range(1, len(path)):
        tile = tactical_map.get_tile(path[i])
        if tile:
            total_cost += tile.terrain.movement_cost

    return total_cost


def get_valid_impulse_moves(
    start: HexCoord,
    tactical_map: TacticalMap,
    max_distance: int = 2,
    momentum_available: int = 6,
    discount_single_hex: bool = True
) -> list[ValidMove]:
    """
    Get all valid destinations for Impulse movement.

    Args:
        start: Starting hex coordinate
        tactical_map: The tactical map
        max_distance: Maximum hex distance (default 2 for Impulse)
        momentum_available: Available momentum to spend
        discount_single_hex: If True, -1 terrain cost when moving only 1 hex

    Returns:
        List of valid moves with costs
    """
    valid_moves = []
    visited = {(start.q, start.r): (0, [start])}  # (q,r) -> (cost, path)

    # BFS to find all reachable hexes within distance
    frontier = [(start, 0, [start])]  # (coord, distance, path)

    while frontier:
        current, dist, path = frontier.pop(0)

        if dist >= max_distance:
            continue

        for neighbor in get_neighbors(current):
            key = (neighbor.q, neighbor.r)

            # Check if valid hex on map
            if not tactical_map.is_valid_coord(neighbor):
                continue

            # Calculate cost to enter this hex
            tile = tactical_map.get_tile(neighbor)
            enter_cost = tile.terrain.movement_cost if tile else 0
            new_path = path + [neighbor]
            new_distance = dist + 1

            # Calculate total cost for this path
            total_cost = calculate_path_cost(new_path, tactical_map)

            # Apply single-hex discount
            if discount_single_hex and new_distance == 1:
                total_cost = max(0, total_cost - 1)

            # Check if we've found a better path to this hex
            if key not in visited or total_cost < visited[key][0]:
                visited[key] = (total_cost, new_path)
                frontier.append((neighbor, new_distance, new_path))

    # Convert visited hexes to ValidMove objects (excluding start)
    # Only include moves the player can actually afford
    for (q, r), (cost, path) in visited.items():
        if q == start.q and r == start.r:
            continue

        # Skip moves that cost more momentum than available
        # (Player can use Maneuver action to generate momentum if needed)
        if cost > momentum_available:
            continue

        coord = HexCoord(q, r)
        tile = tactical_map.get_tile(coord)
        terrain = tile.terrain if tile else TerrainType.OPEN

        valid_moves.append(ValidMove(
            coord=coord,
            cost=cost,
            path=path,
            terrain=terrain
        ))

    return valid_moves


def execute_impulse_move(
    start: HexCoord,
    destination: HexCoord,
    tactical_map: TacticalMap,
    momentum_available: int,
    use_threat: bool = False
) -> MovementResult:
    """
    Execute an Impulse movement action.

    Args:
        start: Starting position
        destination: Target hex
        tactical_map: The tactical map
        momentum_available: Available momentum
        use_threat: If True, add Threat instead of spending Momentum

    Returns:
        MovementResult with success status and costs
    """
    # Get valid moves
    valid_moves = get_valid_impulse_moves(
        start, tactical_map,
        max_distance=2,
        momentum_available=momentum_available
    )

    # Find the destination in valid moves
    target_move = None
    for move in valid_moves:
        if move.coord.q == destination.q and move.coord.r == destination.r:
            target_move = move
            break

    if not target_move:
        distance = start.distance_to(destination)
        if distance > 2:
            return MovementResult(
                success=False,
                message=f"Destination is {distance} hexes away (max 2 for Impulse)"
            )
        if not tactical_map.is_valid_coord(destination):
            return MovementResult(
                success=False,
                message="Destination is outside map bounds"
            )
        return MovementResult(
            success=False,
            message="Cannot reach destination"
        )

    cost = target_move.cost

    # Check if we can pay the cost
    if not use_threat and cost > momentum_available:
        return MovementResult(
            success=False,
            message=f"Insufficient Momentum (need {cost}, have {momentum_available})"
        )

    # Calculate hazard damage if using Threat through hazardous terrain
    hazard_damage = 0
    if use_threat and cost > 0:
        # Check path for hazardous terrain
        for hex_coord in target_move.path[1:]:  # Skip starting hex
            tile = tactical_map.get_tile(hex_coord)
            if tile and tile.is_hazardous:
                # Per STA rules: 2 Challenge Dice per hazardous hex when using Threat
                hazard_damage += 2

    return MovementResult(
        success=True,
        message=f"Moved to ({destination.q}, {destination.r})" +
                (f" - {cost} Momentum spent" if not use_threat and cost > 0 else "") +
                (f" - {cost} Threat added" if use_threat and cost > 0 else "") +
                (f" - {hazard_damage} hazard damage!" if hazard_damage > 0 else ""),
        new_position=destination,
        momentum_cost=cost if not use_threat else 0,
        threat_added=cost if use_threat else 0,
        hazard_damage=hazard_damage,
        path=target_move.path
    )


def get_valid_thruster_moves(
    start: HexCoord,
    ships_in_hex: list[str],  # Names of other ships in same hex
    currently_in_contact: Optional[str] = None
) -> list[dict]:
    """
    Get valid Thrusters actions (enter/exit contact).

    Thrusters allows:
    - Enter Contact with another ship in the same hex
    - Exit Contact if currently docked/landed

    Args:
        start: Current position
        ships_in_hex: List of ship names in the same hex
        currently_in_contact: Ship name if currently in contact

    Returns:
        List of valid thrusters actions
    """
    actions = []

    # If in contact, can exit
    if currently_in_contact:
        actions.append({
            "type": "exit_contact",
            "target": currently_in_contact,
            "description": f"Break contact with {currently_in_contact}"
        })

    # Can enter contact with any ship in same hex (if not already in contact)
    if not currently_in_contact:
        for ship_name in ships_in_hex:
            actions.append({
                "type": "enter_contact",
                "target": ship_name,
                "description": f"Enter contact with {ship_name}"
            })

    return actions


def execute_thrusters_action(
    action_type: str,
    target_ship: str,
    currently_in_contact: Optional[str] = None
) -> MovementResult:
    """
    Execute a Thrusters action (enter/exit contact).

    Args:
        action_type: "enter_contact" or "exit_contact"
        target_ship: Name of ship to dock with or undock from
        currently_in_contact: Current contact status

    Returns:
        MovementResult with success status
    """
    if action_type == "enter_contact":
        if currently_in_contact:
            return MovementResult(
                success=False,
                message=f"Already docked with {currently_in_contact}"
            )
        return MovementResult(
            success=True,
            message=f"Docked with {target_ship}",
            momentum_cost=0
        )

    elif action_type == "exit_contact":
        if currently_in_contact != target_ship:
            return MovementResult(
                success=False,
                message=f"Not docked with {target_ship}"
            )
        return MovementResult(
            success=True,
            message=f"Undocked from {target_ship}",
            momentum_cost=0
        )

    return MovementResult(
        success=False,
        message=f"Unknown thrusters action: {action_type}"
    )


def get_range_category(distance: int) -> str:
    """
    Convert hex distance to STA range category.

    Distance mapping:
    - 0 hexes = Close
    - 1 hex = Medium
    - 2 hexes = Long
    - 3+ hexes = Extreme

    Note: Contact is a special state (docked/landed), not a distance.
    """
    if distance == 0:
        return "close"
    elif distance == 1:
        return "medium"
    elif distance == 2:
        return "long"
    else:
        return "extreme"
