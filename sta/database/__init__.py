"""Database layer for STA Starship Simulator."""

from .db import init_db, get_session, engine
from .schema import (
    CharacterRecord,
    StarshipRecord,
    EncounterRecord,
    CombatLogRecord,
    CampaignRecord,
    CampaignPlayerRecord,
    CampaignShipRecord,
    SceneRecord,
    NPCRecord,
    CampaignNPCRecord,
    SceneNPCRecord,
    CharacterTraitRecord,
    PersonnelEncounterRecord,
)
from .vtt_schema import (
    VTTCharacterRecord,
    VTTShipRecord,
    UniverseLibraryRecord,
    UniverseItemRecord,
    TraitRecord,
    TalentRecord,
    WeaponRecord,
)

__all__ = [
    "init_db",
    "get_session",
    "engine",
    "CharacterRecord",
    "StarshipRecord",
    "EncounterRecord",
    "CombatLogRecord",
    "CampaignRecord",
    "CampaignPlayerRecord",
    "CampaignShipRecord",
    "SceneRecord",
    "NPCRecord",
    "CampaignNPCRecord",
    "SceneNPCRecord",
    "CharacterTraitRecord",
    "PersonnelEncounterRecord",
    "VTTCharacterRecord",
    "VTTShipRecord",
    "UniverseLibraryRecord",
    "UniverseItemRecord",
    "TraitRecord",
    "TalentRecord",
    "WeaponRecord",
]
