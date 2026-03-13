# Combat Features for VTT

## Entities & Properties

### Entity: Scene (Combat Context)
- **Properties**:
  - `id`: Integer (Primary Key)
  - `name`: String
  - `status`: Enum (Active, Archived, Connected)
  - `turn_order`: List[Character IDs]
  - `current_turn_index`: Integer
  - `zones`: List[Zone IDs]
- **Logic**: Manages battlefield state.

### Entity: Zone
- **Properties**:
  - `id`: Integer (Primary Key)
  - `scene_id`: Integer (Foreign Key)
  - `name`: String
  - `description`: String
  - `traits`: List[Trait IDs]
- **Logic**: Abstract spatial unit for Personal Combat.

### Entity: Initiative Slot
- **Properties**:
  - `character_id`: Integer
  - `position`: Integer
  - `keep_initiative`: Boolean (momentum spend)
- **Link**: 1:Many with Scene

### Entity: Action Execution
- **Properties**:
  - `id`: Integer
  - `character_id`: Integer
  - `action_type`: Enum (Minor, Major)
  - `name`: String (Aim, Attack, etc.)
  - `target_id`: Integer (optional)
  - `timestamp`: DateTime
- **Logic**: Tracks actions per turn.

### Entity: Attack Roll
- **Properties**:
  - `id`: Integer
  - `character_id`: Integer
  - `weapon_id`: Integer
  - `target_id`: Integer
  - `attribute`: Enum (Control, Daring, etc.)
  - `department`: Enum (Security, etc.)
  - `difficulty`: Integer
  - `roll_result`: List[Int] (d20s)
  - `successes`: Integer
  - `complications`: Integer
- **Logic**: Resolves attacks.

### Entity: Weapon
- **Properties**:
  - `id`: Integer
  - `name`: String
  - `type`: Enum (Melee, Ranged)
  - `injury`: Enum (Stun, Deadly)
  - `severity`: Integer (1-5)
  - `size`: Enum (1H, 2H)
  - `qualities`: List[String] (Accurate, Area, etc.)
- **Link**: Many:Many with Character (via inventory)

### Entity: Injury
- **Properties**:
  - `id`: Integer
  - `character_id`: Integer
  - `severity`: Integer (1-5)
  - `type`: String (e.g., "Broken Arm")
  - `trait_id`: Integer (linked Trait)
- **Logic**: Mechanical effect on character.

### Entity: Resource Pool (Scene)
- **Properties**:
  - `scene_id`: Integer
  - `momentum`: Integer (max 6)
  - `threat`: Integer (GM pool)
- **Logic**: Shared resources for the scene.

### Entity: Determination (Character)
- **Properties**:
  - `character_id`: Integer
  - `current`: Integer (max 3)
- **Logic**: Player resource for re-rolls etc.

## Social Conflict
### Entity: Social Encounter
- **Properties**:
  - `id`: Integer
  - `scene_id`: Integer
  - `active_char_id`: Integer
  - `reactive_char_id`: Integer
  - `tool`: Enum (Deception, Evidence, Intimidation, Negotiation)
- **Logic**: Opposed task resolution.

## Starship Combat
### Entity: Ship Combat Context
- **Properties**:
  - `scene_id`: Integer
  - `distance`: Enum (Contact, Close, Medium, Long, Extreme)
  - `ship_ids`: List[Integer]
- **Logic**: Manages ship positions and range.
