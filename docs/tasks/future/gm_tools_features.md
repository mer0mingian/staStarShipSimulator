# GM Tools Features for VTT

## Entities & Properties

### Entity: Scene
- **Properties**:
  - `id`: Integer (Primary Key)
  - `campaign_id`: Integer (Foreign Key)
  - `name`: String
  - `description`: String
  - `status`: Enum (Active, Archived, Connected)
  - `turn_order`: JSON (List of participant IDs)
- **Logic**: Container for gameplay.

### Entity: Scene Trait (Situation)
- **Properties**:
  - `id`: Integer
  - `scene_id`: Integer
  - `name`: String
  - `description`: String
  - `potency`: Integer
- **Link**: 1:Many with Scene

### Entity: Participant
- **Properties**:
  - `id`: Integer
  - `scene_id`: Integer
  - `character_id`: Integer (nullable)
  - `ship_id`: Integer (nullable)
  - `type`: Enum (PC, NPC, Ship)
- **Link**: 1:Many with Scene

## Threat Pool
### Entity: Campaign Resource
- **Properties**:
  - `campaign_id`: Integer
  - `momentum`: Integer (max 6)
  - `threat`: Integer (GM pool)
- **Logic**: Global resources for the campaign session.

## Extended Tasks
### Entity: Extended Task
- **Properties**:
  - `id`: Integer
  - `scene_id`: Integer
  - `name`: String
  - `work_track`: Integer (current progress)
  - `difficulty`: Integer
  - `magnitude`: Integer
  - `resistance`: Integer
  - `breakthrough_effects`: JSON
- **Logic**: Multi-step task resolution.

## NPC System
### Entity: NPC Category Logic
- **Properties**:
  - `category`: Enum (Minor, Notable, Major)
  - `stress_enabled`: Boolean
  - `personal_threat_pool`: Integer
  - `values_count`: Integer
- **Logic**: Defines behavior rules for NPC types.
