# Legacy Code Index

This document inventories all legacy components that will be replaced or deprecated during the VTT transition.

## Table of Contents

- [Database Tables](#database-tables)
- [Model Classes](#model-classes)
- [Route Endpoints](#route-endpoints)
- [Configuration Files](#configuration-files)
- [Utility Scripts](#utility-scripts)
- [Migration Plan](#migration-plan)

## Database Tables

### Legacy Combat Tables (to be deprecated)

1. **characters** - Legacy character storage
   - Location: `sta/database/schema.py:19`
   - Status: Will be replaced by VTT Character model
   - Migration: Data can be flushed per user confirmation

2. **starships** - Legacy starship storage  
   - Location: `sta/database/schema.py:140`
   - Status: Will be replaced by VTT Ship model
   - Migration: Data can be flushed per user confirmation

3. **encounters** - Legacy combat encounter storage
   - Location: `sta/database/schema.py:283`
   - Status: Will be replaced by VTT Scene model
   - Migration: Data can be flushed per user confirmation

4. **campaigns** - Partial campaign implementation
   - Location: `sta/database/schema.py:397`
   - Status: Needs enhancement for full VTT features
   - Migration: Enhance in-place, preserve existing data

5. **campaign_players** - Player-campaign associations
   - Location: `sta/database/schema.py:430`
   - Status: Needs enhancement for VTT player management
   - Migration: Enhance in-place

6. **campaign_ships** - Ship-campaign associations
   - Location: `sta/database/schema.py:462`
   - Status: Needs enhancement for VTT ship management
   - Migration: Enhance in-place

7. **scenes** - Partial scene implementation
   - Location: `sta/database/schema.py:478`
   - Status: Needs enhancement for full VTT scene features
   - Migration: Enhance in-place

8. **npc_archive** - NPC storage
   - Location: `sta/database/schema.py:521`
   - Status: Needs integration with VTT Character model
   - Migration: Enhance in-place

### Tables to Preserve

1. **campaign_npcs** - NPC-campaign associations
2. **scene_npcs** - NPC-scene associations
3. **character_traits** - Trait system

## Model Classes

### Legacy Model Classes (to be deprecated)

1. **Character** - Legacy character model
   - Location: `sta/models/character.py:61`
   - Status: Replace with `sta/models/vtt/models.py:Character`
   - Usage: Used in legacy combat system

2. **Starship** - Legacy starship model
   - Location: `sta/models/starship.py:86`
   - Status: Replace with `sta/models/vtt/models.py:Ship`
   - Usage: Used in legacy combat system

3. **Encounter** - Legacy combat encounter
   - Location: `sta/models/combat.py:10`
   - Status: Replace with `sta/models/vtt/models.py:Scene`
   - Usage: Used in legacy combat routes

4. **CharacterRecord** - Legacy database model
   - Location: `sta/database/schema.py:19`
   - Status: Replace with VTT CharacterRecord
   - Usage: Database ORM for characters

5. **StarshipRecord** - Legacy database model
   - Location: `sta/database/schema.py:140`
   - Status: Replace with VTT ShipRecord
   - Usage: Database ORM for starships

6. **EncounterRecord** - Legacy database model
   - Location: `sta/database/schema.py:283`
   - Status: Replace with VTT SceneRecord
   - Usage: Database ORM for encounters

### Model Classes to Preserve/Enhance

1. **CampaignRecord** - Partial campaign model
   - Location: `sta/database/schema.py:397`
   - Status: Enhance for full VTT features

2. **SceneRecord** - Partial scene model
   - Location: `sta/database/schema.py:478`
   - Status: Enhance for full VTT features

3. **NPCRecord** - NPC model
   - Location: `sta/database/schema.py:521`
   - Status: Integrate with VTT Character model

## Route Endpoints

### Legacy Route Files

1. **api.py** - Main API routes
   - Location: `sta/web/routes/api.py`
   - Status: Contains legacy combat endpoints
   - Migration: Gradually replace with VTT endpoints

2. **encounters.py** - Combat encounter routes
   - Location: `sta/web/routes/encounters.py`
   - Status: Legacy combat system
   - Migration: Replace with VTT scene routes

3. **campaigns.py** - Partial campaign routes
   - Location: `sta/web/routes/campaigns.py`
   - Status: Needs enhancement for VTT features
   - Migration: Enhance in-place

4. **scenes.py** - Partial scene routes
   - Location: `sta/web/routes/scenes.py`
   - Status: Needs enhancement for VTT features
   - Migration: Enhance in-place

### Specific Legacy Endpoints

1. `/api/encounter/*` - All combat encounter endpoints
2. `/api/combat/*` - Combat-specific endpoints
3. `/api/turn/*` - Turn management endpoints
4. `/api/action/*` - Legacy action endpoints

## Configuration Files

### Configuration Files to Review

1. **opencode.json** - OpenCode configuration
   - Location: `/opencode.json`
   - Status: Needs model configuration updates
   - Action: Add VTT development models

2. **AGENTS.md** - Agent instructions
   - Location: `/AGENTS.md`
   - Status: Needs updates for VTT workflow
   - Action: Add legacy management instructions

3. **requirements.txt** - Python dependencies
   - Location: `/requirements.txt`
   - Status: Review for VTT requirements
   - Action: Add any missing dependencies

## Utility Scripts

### Migration and Update Scripts

1. **migrate_calibrate_weapons.py** - Legacy migration script
   - Location: `/migrate_calibrate_weapons.py`
   - Status: Legacy combat migration
   - Action: Review for VTT relevance

2. **migrate_tactical_map.py** - Tactical map migration
   - Location: `/migrate_tactical_map.py`
   - Status: Legacy combat migration
   - Action: Review for VTT relevance

3. **migrate_to_effects_system.py** - Effects system migration
   - Location: `/migrate_to_effects_system.py`
   - Status: Legacy combat migration
   - Action: Review for VTT relevance

4. **updater.py** - Database updater
   - Location: `sta/updater.py`
   - Status: Legacy database updates
   - Action: Enhance for VTT schema migration

## Migration Plan

### Phase 1: Inventory and Documentation (COMPLETE)
- ✅ Create legacy index
- ✅ Document all legacy components
- ✅ Identify preservation vs. replacement targets

### Phase 2: New VTT Schema Creation
- Create new database tables for VTT models
- Implement new ORM classes
- Add migration scripts for schema changes

### Phase 3: Feature Implementation
- Implement Campaign management
- Implement Scene management
- Implement Character/Ship CRUD
- Implement Combat integration

### Phase 4: Legacy Deprecation
- Mark legacy endpoints as deprecated
- Add warnings to legacy code
- Provide migration guides

### Phase 5: Cleanup and Removal
- Remove deprecated code after VTT system stable
- Delete legacy database tables
- Remove legacy configuration

### Phase 6: Final Validation
- Ensure all tests pass
- Verify no regressions
- Confirm user acceptance

## Removal Checklist

Use this checklist when removing legacy components:

- [ ] Component is no longer used in any active code path
- [ ] All tests pass without the component
- [ ] Documentation has been updated
- [ ] Users have been notified (if applicable)
- [ ] Backup exists (git history)
- [ ] Removal approved by user

## Update Instructions

This document should be updated whenever:

1. New legacy components are discovered
2. Migration status changes for any component
3. Removal decisions are made
4. New dependencies on legacy code are found

**Update Format**:
```markdown
### [Component Type]

**Component Name** - Brief description
- Location: file path
- Status: current status (preserve/enhance/replace/remove)
- Migration: migration approach
- Notes: any additional information
```