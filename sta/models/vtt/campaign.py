from typing import List, Optional
from pydantic import BaseModel, Field


class Campaign(BaseModel):
    id: str
    name: str
    description: str = ""

    # GM Identity (Name/Password combo as per requirements)
    gm_name: str

    # Shared Resource Pools (as per rules, Momentum/Threat can carry over or be reset)
    # This is the "Campaign Wide" pool, but can be overridden per scene if needed
    momentum: int = Field(default=0, ge=0, le=6)
    threat: int = 0

    # Campaign Content
    scenes: List[str] = []  # List of Scene IDs
    universe_library_ref: Optional[str] = None  # Link to Universe Library

    # Players in this campaign
    players: List[str] = []  # List of Player IDs/Names

    # Campaign Settings
    # ... (Time period, setting specifics, etc.)


class UniverseLibrary(BaseModel):
    """
    Universe Library - acts as a library for Chars, Ships, Items, Documents
    that can be shared between Campaigns by a single GM.
    """

    id: str
    gm_name: str  # Identity based, not user management

    chars: List[str] = []  # IDs of Chars in library
    ships: List[str] = []  # IDs of Ships in library
    items: List[str] = []  # IDs of Items in library
    documents: List[str] = []  # IDs of Documents in library


class TemplateLibrary(BaseModel):
    """
    Template Library - source of pregenerated content.
    Only accessible by GM.
    """

    id: str

    # Standard Templates (Starfleet, Klingon, etc.)
    # Or custom templates created by GMs
    pass
