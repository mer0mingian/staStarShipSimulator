# Ship Features for VTT

## Entities & Properties

### Entity: Ship (Base)
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `class`: String
  - `mission_profile`: String
  - `scale`: Integer (1-7)
  - `resistance`: Integer (derived)
  - `shields_current`: Integer
  - `shields_max`: Integer
  - `crew_quality`: Integer (2-5 for NPC ships)
  - `reserve_power_used`: Boolean (once per scene)
- **Logic**: Represents both Player and NPC vessels.

### Entity: Ship System Set
- **Properties**:
  - `ship_id`: Integer (Foreign Key)
  - `comms`: Integer (0-10)
  - `computers`: Integer (0-10)
  - `engines`: Integer (0-10)
  - `sensors`: Integer (0-10)
  - `structure`: Integer (0-10)
  - `weapons`: Integer (0-10)
- **Link**: 1:1 with Ship

### Entity: Ship Department Set
- **Properties**:
  - `ship_id`: Integer (Foreign Key)
  - `command`: Integer (0-4)
  - `conn`: Integer (0-4)
  - `engineering`: Integer (0-4)
  - `medicine`: Integer (0-4)
  - `science`: Integer (0-4)
  - `security`: Integer (0-4)
- **Link**: 1:1 with Ship

### Entity: Ship Trait
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `description`: String
  - `category`: Enum (Equipment, Location)
- **Link**: Many:Many with Ship (via `ship_traits`)

### Entity: Ship Talent
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `description`: String
- **Link**: Many:Many with Ship (via `ship_talents`)

### Entity: Ship Weapon
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `type`: Enum (Energy, Torpedo, Tractor Beam)
  - `damage`: Integer
  - `range`: Enum (Close, Medium, Long, Extreme)
  - `qualities`: List[String]
- **Link**: Many:Many with Ship (via `ship_weapons`)

## Management
### Entity: Reserve Power
- **Properties**:
  - `ship_id`: Integer
  - `available`: Boolean (reset per scene)
- **Logic**: Used for Regenerate Shields, Reroute Power, Warp.

### Entity: Small Craft
- **Properties**:
  - `ship_id`: Integer
  - `readiness`: Integer (Scale - 1)
- **Logic**: Tracks active small craft limit.
