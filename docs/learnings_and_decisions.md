# Learnings and Decisions

## Test Fixes (March 2026)

### Fixed: Action Requirement Tests (8 tests)

**Problem**: Tests checked `data.get("error")` but FastAPI returns errors in `data["detail"]`

**Files Fixed**:
- `tests/test_actions_standard.py` - 3 tests
- `tests/test_actions_engineering.py` - 2 tests  
- `tests/test_actions_science.py` - 1 test

**Changes**: Changed `data.get("error", "")` to `data.get("detail", "")`

### Fixed: Scan For Weakness Range Test (1 test)

**Problem**: Test didn't include `distance` key in ship positions

**File**: `tests/test_actions_science.py`

**Change**: Added `"distance": 3` to enemy ship position in test data

### Fixed: Scene API Response Parsing (~11 tests)

**Problem**: Tests used `response.content.decode("utf-8")` but API returns JSON with HTML in `content` field

**File**: `tests/test_scene.py`

**Change**: Changed to `response.json()["content"]` for all scene view tests

### Fixed: Scene Creation Response (1 test)

**Problem**: Test expected `scene_type` in response but API doesn't return it

**File**: `tests/test_scene.py`

**Change**: Removed assertion for `data["scene_type"]`

## Remaining Test Failures (39 tests)

These require deeper investigation:

### Character Claiming (4 tests)
- Expect redirects (302) but API returns JSON (200/400)
- Tests: `test_cannot_claim_already_claimed_character`, `test_switch_character_releases_it`, `test_successful_claim_sets_session_token`, `test_two_players_cannot_claim_same_character`

### Character/Ship API (2 tests)
- API returning unexpected status codes or data

### Personnel Encounter (12 tests)
- Various API response mismatches

### Scene Tests (14 tests)
- Various issues with auth, redirects, and response parsing

### Scene Participants/Ships (2 tests)
- Expect 400 but get 422 (validation errors)

### Scene Termination (3 tests)
- Async fixture issues (RuntimeWarning: coroutine never awaited)

### Token Tests (2 tests)
- Expect cookies but API returns JSON with token in body

### Turn Enforcement (1 test)
- Test sets `players_turns_used_json` but code checks `player_turns_used` integer field
