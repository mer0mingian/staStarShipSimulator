from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class HexTile(BaseModel):
    q: int  # Axial coordinate
    r: int  # Axial coordinate
    s: int  # Axial coordinate
    terrain_type: str = "space"
    visibility: str = "clear"
    # content: Optional[str] = None # What's on the tile, e.g. a ship ID


class HexGrid(BaseModel):
    radius: int
    tiles: Dict[str, HexTile] = {}  # "q,r" -> HexTile


class CombatState(BaseModel):
    current_round: int = 0
    turn_order: List[str] = []
    active_combatant_id: Optional[str] = None
