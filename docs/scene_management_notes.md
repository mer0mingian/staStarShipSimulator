# Milestone 1 - Extended: Scene Management

## Conceptual Model

```
Campaign
├── Scenes (first-class entity)
│   ├── Type: narrative, starship_encounter, personal_encounter, social_encounter
│   ├── Content: Stardate, picture, traits, challenges
│   ├── Optional: Map (not for social)
│   └── Optional: Combat data (encounter types only)

NPC Archive (global)
└── Campaign NPCs (selected from archive or created fresh)
    └── Scene NPCs (present in current scene)
```

---

## Database Schema

### SceneRecord (Updated)
```python
class SceneRecord(Base):
    __tablename__ = "scenes"
    
    id: PK
    campaign_id: FK to campaigns (required)
    encounter_id: FK to encounters (nullable - only for combat scenes)
    
    name: String
    scene_type: Enum  # 'narrative', 'starship_encounter', 'personal_encounter', 'social_encounter'
    status: String    # 'draft', 'active', 'completed'
    
    stardate: String
    scene_picture_url: String
    scene_traits_json: Text  # Location/equipment/circumstantial traits
    challenges_json: Text
    characters_present_json: Text
    
    has_map: Boolean  # False for social encounters
    tactical_map_json: Text
    
    show_picture: Boolean
    active_picture_id: FK to scene_pictures (nullable)
    
    created_at, updated_at
```

### ScenePictureRecord (New)
```python
class ScenePictureRecord(Base):
    __tablename__ = "scene_pictures"
    
    id: PK
    scene_id: FK to scenes
    filename: String  # Stored filename (uploads/)
    original_name: String
    url: String  # External URL (if not uploaded)
    is_active: Boolean
    order_index: Integer
    uploaded_at: DateTime
```

### NPCRecord (New - Global Archive)
```python
class NPCRecord(Base):
    __tablename__ = "npc_archive"
    
    id: PK
    name: String
    npc_type: Enum  # 'major', 'notable', 'minor', 'npc_crew'
    
    # Minimal stats (for major/notable)
    attributes_json: Text  # Optional
    disciplines_json: Text  # Optional
    stress: Integer
    stress_max: Integer
    
    # Extended fields
    appearance: Text
    motivation: Text
    affiliation: String
    location: String
    picture_url: String
    notes: Text
    
    # For NPC Ship crew
    ship_id: FK to starships (nullable)
    
    created_at, updated_at
```

### CampaignNPCRecord (New - Campaign Manifest)
```python
class CampaignNPCRecord(Base):
    __tablename__ = "campaign_npcs"
    
    id: PK
    campaign_id: FK to campaigns
    npc_id: FK to npc_archive
    is_visible_to_players: Boolean
    added_at: DateTime
```

### SceneNPCRecord (New - NPCs in Scene)
```python
class SceneNPCRecord(Base):
    __tablename__ = "scene_npcs"
    
    id: PK
    scene_id: FK to scenes
    npc_id: FK to npc_archive (nullable - can be on-the-fly)
    
    # On-the-fly NPC fields
    quick_name: String
    quick_description: Text
    
    is_visible_to_players: Boolean
    order_index: Integer
```

### CharacterTraitRecord (New)
```python
class CharacterTraitRecord(Base):
    __tablename__ = "character_traits"
    
    id: PK
    character_id: FK to characters (required)
    trait_name: String
    description: Text (nullable)
    source: String  # 'gm', 'player', 'scene', 'campaign' - for tracking only
    scene_id: FK to scenes (nullable - if originated from scene)
    is_active: Boolean  # Can be toggled off when no longer true
    created_at: DateTime
```

---

## Scene Types

| Type | Map | Combat | NPCs Visible | Notes |
|------|-----|--------|--------------|-------|
| narrative | Optional | No | Yes | General roleplay scene |
| starship_encounter | Yes | Yes | Yes | Ship-to-ship combat |
| personal_encounter | Yes | Yes | Yes | Character-scale combat |
| social_encounter | No | No | Yes | Social conflict/interaction |

---

## Trait System

Traits exist in two contexts:
1. **Scene Traits** - Location, equipment, circumstantial (stored on SceneRecord)
2. **Character Traits** - Personal conditions (stored on CharacterTraitRecord)

Both GM and Player can:
- Add new traits to their character
- Remove/toggle inactive traits
- View trait history

---

## Implementation Order

1. **Phase 1: Database Schema**
   - [ ] Update SceneRecord with scene_type, status, has_map
   - [ ] Create ScenePictureRecord
   - [ ] Create NPCRecord (archive)
   - [ ] Create CampaignNPCRecord
   - [ ] Create SceneNPCRecord
   - [ ] Create CharacterTraitRecord

2. **Phase 2: Scene CRUD**
   - [ ] Create scene route/template
   - [ ] Edit scene route/template
   - [ ] Scene type-specific UI

3. **Phase 3: NPC System**
   - [ ] NPC archive management
   - [ ] Add NPCs to campaign
   - [ ] Add NPCs to scene

4. **Phase 4: Picture System**
   - [ ] File upload handling
   - [ ] Gallery UI
   - [ ] Picture activation

5. **Phase 5: Character Traits**
   - [ ] Add/remove traits UI
   - [ ] Trait display on viewscreen
   - [ ] Player self-service trait management

6. **Phase 6: Scene Activation**
   - [ ] Activate scene endpoint
   - [ ] Player notification
   - [ ] Viewscreen transition
