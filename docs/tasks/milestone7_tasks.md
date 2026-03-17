# Milestone 7: Export/Import Features

## Overview
Export/Import functionality for VTT characters, ships, and campaign backups.

## Tasks

### M7.1: VTT Character Export/Import
**Endpoint**: `/api/vtt/characters/import` and `/api/vtt/characters/{id}/export`

Export individual VTT character as JSON:
```json
{
  "name": "Captain Janeway",
  "species": "Human",
  "rank": "Captain",
  "role": "Command",
  "pronouns": "she/her",
  "description": "Captain of Voyager",
  "attributes": {
    "control": 9,
    "fitness": 8,
    "daring": 10,
    "insight": 9,
    "presence": 11,
    "reason": 10
  },
  "disciplines": {
    "command": 4,
    "conn": 2,
    "engineering": 2,
    "medicine": 1,
    "science": 2,
    "security": 2
  },
  "stress": 4,
  "stress_max": 5,
  "determination": 2,
  "determination_max": 3,
  "talents": ["Command Presence", "Resolve"],
  "focuses": ["Astrophysics", "Photonics"],
  "values": ["Integrity", "Discovery"],
  "equipment": ["Commbadge", "Tricorder"],
  "environment": "Indiana",
  "upbringing": "Military Academy",
  "career_path": "Starfleet"
}
```

Import accepts either a single character object or a container with `characters` key:
```json
{
  "characters": [
    {
      "name": "New Character",
      "species": "Vulcan",
      ...
    }
  ]
}
```

**Validation rules**:
- Attributes: 7-12
- Disciplines: 0-5
- Stress: 0 to stress_max
- Required: name, species, attributes, disciplines

### M7.2: VTT Ship Export/Import
**Endpoint**: `/api/vtt/ships/import` and `/api/vtt/ships/{id}/export`

Export individual VTT ship as JSON:
```json
{
  "name": "USS Voyager",
  "ship_class": "Intrepid-class",
  "ship_registry": "NCC-74656",
  "scale": 5,
  "systems": {
    "comms": 8,
    "computers": 10,
    "engines": 11,
    "sensors": 10,
    "structure": 8,
    "weapons": 8
  },
  "departments": {
    "command": 2,
    "conn": 4,
    "engineering": 3,
    "medicine": 3,
    "science": 4,
    "security": 2
  },
  "weapons": [
    {
      "name": "Phasers",
      "weapon_type": "energy",
      "damage": 5,
      "range": "long",
      "qualities": ["reload"],
      "requires_calibration": false
    }
  ],
  "talents": ["Efficient Repairs"],
  "traits": ["Intrepid-class"],
  "shields": 35,
  "shields_max": 35,
  "resistance": 5,
  "has_reserve_power": true,
  "shields_raised": false,
  "weapons_armed": false,
  "crew_quality": null
}
```

Import accepts either a single ship object or container with `ships` key. Also accepts `registry` as alias for `ship_registry`.

**Validation rules**:
- Systems: 7-12
- Departments: 0-5
- Scale: 1-7
- Shields: 0 to shields_max

### M7.3: Full Campaign Backup
**Endpoint**: `/api/backup`

Export all campaign data including characters, NPCs, ships:
```json
{
  "version": "1.0",
  "exported_at": "2025-01-15T10:30:00Z",
  "characters": [...],
  "npcs": [...],
  "ships": [...],
  "campaigns": [...]
}
```

## Implementation Notes
- Implement import validation similar to creation validation
- Support both single-object and container formats for imports
- Provide clear error messages for invalid data
- Preserve existing IDs where applicable for updates