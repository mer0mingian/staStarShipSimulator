# Character Features for VTT

## Entities & Properties

### Entity: Character (Base)
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `description`: String
  - `species`: String
  - `role`: String
  - `images`: List[String]
  - `state`: Enum (Ok, Defeated, Fatigued, Dead)
  - `stress_current`: Integer
  - `stress_max`: Integer (derived from Fitness)

### Entity: Attribute Set
- **Properties**:
  - `control`: Integer (7-12)
  - `daring`: Integer (7-12)
  - `fitness`: Integer (7-12)
  - `insight`: Integer (7-12)
  - `presence`: Integer (7-12)
  - `reason`: Integer (7-12)
- **Link**: 1:1 with Character

### Entity: Department Set
- **Properties**:
  - `command`: Integer (0-5)
  - `conn`: Integer (0-5)
  - `engineering`: Integer (0-5)
  - `medicine`: Integer (0-5)
  - `science`: Integer (0-5)
  - `security`: Integer (0-5)
- **Link**: 1:1 with Character

### Entity: Trait
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `description`: String
  - `category`: Enum (Character, Location, Situation, Equipment)
  - `potency`: Integer (default 1)
- **Link**: Many:Many with Character (via `character_traits`)

### Entity: Talent
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `description`: String
  - `player_selectable`: Boolean
  - `category`: Enum (Talent, Special Rule, Species Ability)
  - `conditions`: String (logic description)
  - `game_mechanic_ref`: String (future handler reference)
- **Link**: Many:Many with Character (via `character_talents`)

### Entity: Value
- **Properties**:
  - `id`: Integer (Primary Key)
  - `text`: String
  - `character_id`: Integer (Foreign Key)
- **Link**: 1:Many with Character

### Entity: Focus
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `character_id`: Integer (Foreign Key)
- **Link**: 1:Many with Character (max 6)

## NPC Specifics
### Entity: NPC (inherits Character)
- **Properties**:
  - `category`: Enum (Major, Notable, Minor)
  - `personal_threat_pool`: Integer (0-24)
  - `location`: String
  - `background`: JSON (Archetype, Upbringing, Environment, etc.)
  - `life_form_origin`: String
  - `body_structure`: String
- **Logic**: Minor NPCs have no Stress, instant defeat on injury.

## PC Specifics
### Entity: PC (inherits Character)
- **Properties**:
  - `category`: Enum (Main, Side)
  - `personal_logs`: List[String]
  - `mission_logs`: List[String]
  - `scene_logs`: List[String]
  - `background_texts`: String
- **Logic**: Main characters have full rules; Side characters have simplified rules.
