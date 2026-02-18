# Milestone 1 - Extended: Scene Management

## Conceptual Model

```
Campaign
├── Scenes (new first-class entity)
│   ├── id, name, type, status
│   ├── Stardate, picture, traits, challenges
│   ├── Optional: Map, NPCs
│   └── Optional: Combat data (if type=encounter)
```

## Database Changes

### Update SceneRecord
```python
class SceneRecord(Base):
    __tablename__ = "scenes"
    
    id: PK
    campaign_id: FK to campaigns (required)
    encounter_id: FK to encounters (nullable - only if combat scene)
    
    # Basic info
    name: String
    scene_type: Enum  # 'narrative', 'starship_combat', 'personnel_combat', 'social'
    status: String    # 'draft', 'active', 'completed'
    
    # Scene content
    stardate: String
    scene_picture_url: String
    scene_traits_json: Text
    challenges_json: Text
    characters_present_json: Text  # Character IDs in scene
    
    # Map (optional)
    has_map: Boolean
    tactical_map_json: Text
    
    # NPCs in scene
    npcs_json: Text  # [{name, description, visible_to_players, picture_url}]
    
    # Presentation
    show_picture: Boolean
    active_picture_index: Integer  # Index in gallery
    
    created_at, updated_at
```

### New Table: ScenePictureRecord
```python
class ScenePictureRecord(Base):
    __tablename__ = "scene_pictures"
    
    id: PK
    scene_id: FK to scenes
    filename: String  # Stored filename
    original_name: String  # User's original filename
    is_active: Boolean  # Currently displayed
    order_index: Integer
    uploaded_at: DateTime
```

### New Table: CharacterTraitRecord
```python
class CharacterTraitRecord(Base):
    __tablename__ = "character_traits"
    
    id: PK
    character_id: FK to characters
    trait_name: String
    source: String  # 'gm_added', 'scene_effect', 'earned'
    scene_id: FK to scenes (nullable - if from specific scene)
    is_temporary: Boolean
    created_at: DateTime
```

## UI Changes

### Campaign Dashboard (GM)
- Add "Create Scene" button next to "Start Encounter"
- Combine draft scenes + draft encounters in bottom section
- Visual indicators: 
  - Scene icon 🎬 for narrative scenes
  - Ship icon 🚀 for starship combat
  - Person icon 👤 for personnel combat
  - Speech icon 💬 for social scenes

### Scene Editor (GM) - Non-Encounter
- Tabs: Overview, NPCs, Pictures, Map (optional)
- Overview: Stardate, Traits, Challenges, Player Ship (optional)
- NPCs: List with visibility toggle, add/remove
- Pictures: Gallery view, upload button, set active
- Map: Same hex editor as encounter (optional)

### Viewscreen - Non-Encounter
- Show scene picture (full or overlay)
- Stardate prominent
- Scene traits displayed
- Visible NPCs listed
- No combat UI elements

## Questions Pending
1. Scene types: Enum or boolean flags?
2. NPC source: From manifest or on-the-fly?
3. Picture storage: Local files or URLs?
4. Scene activation: How does it work?
5. Character traits: Temporary or permanent?
