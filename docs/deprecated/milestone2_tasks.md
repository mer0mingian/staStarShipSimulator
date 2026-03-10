# Milestone 2: Campaign Management - Implementation Tasks

## Overview
Milestone 2 focuses on Campaign Management with GM controls and player access. Much of the campaign infrastructure already exists - this task list focuses on gaps and enhancements.

## Branch Information
- **Branch**: `feature/m2-campaign-management` (create from `feature/m1-database-schema`)
- **Worktree**: `/home/mer0/m2-worktree`

## Current State Assessment

### Already Implemented (✅)
- Campaign CRUD templates and basic routes
- Campaign creation (`/campaign/new`)
- GM home page (`/campaign/gm`)
- Player home page (`/campaign/player`)
- Campaign joining (`/campaign/<id>/join`)
- GM login (`/campaign/<id>/gm-login`)
- Player/character switching
- Campaign players API (`/api/campaign/<id>/players`)
- Campaign ships API (`/api/campaign/<id>/ships`)
- Campaign NPCs API (`/api/campaign/<id>/npcs`)
- Scene management within campaigns
- Encounter management within campaigns

### Needs Implementation (❌)
- Universe Library API (new)
- Resource pool management (Momentum/Threat at campaign level)
- VTT character/ship integration with campaigns
- Session token system improvements

---

## Task 2.1: Resource Pool Management (Campaign-Level)

### Description
Implement resource pool management for campaigns - tracking Momentum and Threat at the campaign level.

### Steps
1. **Add columns to CampaignRecord**:
   - `momentum`: Integer, default 0, max 6
   - `threat`: Integer, default 0

2. **Create API endpoints**:
   - `GET /api/campaign/<id>/resources` - Get campaign momentum/threat
   - `POST /api/campaign/<id>/momentum` - Add/subtract momentum
   - `POST /api/campaign/<id>/threat` - Add/subtract threat

3. **Create tests**:
   - `tests/test_campaign_resources.py`

### Files to Modify
- `sta/database/schema.py` - Add columns to CampaignRecord
- `sta/web/routes/campaigns.py` - Add resource endpoints

### Verification
```bash
.venv/bin/python -m pytest tests/test_campaign_resources.py -v
```

---

## Task 2.2: Universe Library API

### Description
Create Universe Library for managing reusable characters, ships, and items across campaigns.

### Steps
1. **Create new route file**:
   - `sta/web/routes/universe.py`

2. **Implement endpoints**:
   - `GET /api/universe` - List all library items
   - `POST /api/universe/characters` - Add character to library
   - `POST /api/universe/ships` - Add ship to library
   - `GET /api/universe/<category>` - Filter by category (pcs, npcs, creatures, ships)
   - `GET /api/universe/<id>` - Get specific item
   - `PUT /api/universe/<id>` - Update item
   - `DELETE /api/universe/<id>` - Delete item

3. **Create tests**:
   - `tests/test_universe_library.py`

### Files to Create
- `sta/web/routes/universe.py` (new)
- `tests/test_universe_library.py` (new)

### Files to Modify
- `sta/web/routes/__init__.py` - Register blueprint

### Verification
```bash
.venv/bin/python -m pytest tests/test_universe_library.py -v
```

---

## Task 2.3: VTT Character/Ship Integration

### Description
Integrate new VTT schema characters and ships with campaign management.

### Steps
1. **Add VTT foreign keys to campaign associations**:
   - Add `vtt_character_id` to CampaignPlayerRecord
   - Add `vtt_ship_id` to CampaignShipRecord

2. **Create endpoints to link VTT entities**:
   - `POST /api/campaign/<id>/link-character` - Link VTT character to campaign player
   - `POST /api/campaign/<id>/link-ship` - Link VTT ship to campaign

3. **Create migration for schema changes**:
   - Add columns to existing tables

4. **Create tests**:
   - `tests/test_vtt_campaign_integration.py`

### Files to Modify
- `sta/database/schema.py` - Add foreign key columns
- `sta/web/routes/campaigns.py` - Add linking endpoints
- `sta/database/migrations/versions/` - New migration

### Verification
```bash
.venv/bin/python -m pytest tests/test_vtt_campaign_integration.py -v
```

---

## Task 2.4: Session Token System Enhancement

### Description
Improve session token system for more secure player identification.

### Steps
1. **Add token expiration**:
   - Add `token_expires_at` to CampaignPlayerRecord

2. **Add refresh endpoint**:
   - `POST /api/campaign/<id>/refresh-token` - Refresh session token

3. **Create tests**:
   - `tests/test_session_tokens.py`

### Files to Modify
- `sta/database/schema.py`
- `sta/web/routes/campaigns.py`

### Verification
```bash
.venv/bin/python -m pytest tests/test_session_tokens.py -v
```

---

## Test Execution

### Run all M2 tests
```bash
.venv/bin/python -m pytest tests/test_campaign_resources.py tests/test_universe_library.py tests/test_vtt_campaign_integration.py tests/test_session_tokens.py -v
```

### Run all tests
```bash
.venv/bin/python -m pytest tests/ -v
```

---

## Success Criteria

- [ ] Campaign resource pools (Momentum/Threat) working
- [ ] Universe Library API functional
- [ ] VTT character/ship integration with campaigns
- [ ] Session token system enhanced
- [ ] All tests passing
- [ ] Legacy code still functional

---

## Timeline Estimate
- Task 2.1: 2-3 hours
- Task 2.2: 3-4 hours  
- Task 2.3: 3-4 hours
- Task 2.4: 1-2 hours
- **Total: ~10-13 hours**

---

## Dependencies
- Task 2.3 depends on Task 2.2 (Universe Library must exist first)
- Other tasks can be parallelized

---

## Agent Assignment

**Primary Agent**: python-dev (using skill: python-dev, model: opencode/minimax-m2.5-free)

**Workflow**:
1. Create worktree: `git worktree add ../m2-worktree feature/m1-database-schema`
2. Create branch: `git checkout -b feature/m2-campaign-management`
3. Implement tasks in order (2.1 → 2.2 → 2.3 → 2.4)
4. Run tests after each task
5. Commit after each task completion
6. Push and create PR to main when complete
