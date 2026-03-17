# Test Organization and Markers

This document describes how to organize and run tests using pytest markers in the STA Starship Simulator project.

## Overview

Tests are organized by feature area using pytest markers. This allows you to run specific groups of tests without running the entire test suite.

## Running Test Groups

### Run Scene Lifecycle Tests
```bash
pytest -m scene_lifecycle
```

### Run Scene Activation Tests
```bash
pytest -m scene_activation
```

### Run Scene Termination Tests
```bash
pytest -m scene_termination
```

### Run Combat Tests
```bash
pytest -m combat
```

### Run Turn Enforcement Tests
```bash
pytest -m turn_enforcement
```

### Run Turn Order Tests
```bash
pytest -m turn_order
```

### Run All Action Tests
```bash
pytest -m actions
```

### Run Specific Station Action Tests
```bash
# Tactical/Security actions
pytest -m action_tactical

# Command actions
pytest -m action_command

# Conn/Helm actions
pytest -m action_conn

# Engineering actions
pytest -m action_engineering

# Science actions
pytest -m action_science
```

### Run Character Tests
```bash
pytest -m characters
```

### Run Ship Tests
```bash
pytest -m ships
```

### Run Campaign Tests
```bash
# All campaign tests
pytest -m campaign

# Campaign resources only
pytest -m campaign_resources
```

### Run Session/Token Tests
```bash
pytest -m session
```

### Run Visibility Tests
```bash
pytest -m visibility
```

### Run Logging Tests
```bash
pytest -m logging
```

## Excluding Test Groups

### Skip Slow Tests
```bash
pytest -m "not slow"
```

### Skip All Scene Tests
```bash
pytest -m "not scene_lifecycle and not scene_activation and not scene_termination"
```

## Combining Markers

### Run Multiple Groups (OR logic)
```bash
# Run either scene or combat tests
pytest -m "scene_lifecycle or combat"
```

### Run Multiple Groups (AND logic)
```bash
# Run tests that have both markers
pytest -m "scene_lifecycle and api"
```

### Complex Combinations
```bash
# Run scene tests but not slow ones
pytest -m "scene_lifecycle and not slow"

# Run actions but skip tactical
pytest -m "actions and not action_tactical"
```

## Available Markers

| Marker | Description |
|--------|-------------|
| `scene_lifecycle` | Tests for scene state transitions (draft→ready→active→completed) |
| `scene_activation` | Tests for scene activation endpoint |
| `scene_termination` | Tests for scene termination/completion endpoint |
| `scene_management` | Tests for scene CRUD and general scene operations |
| `scene_config` | Tests for scene configuration and settings |
| `scene_connections` | Tests for scene connections and transitions |
| `scene_participants` | Tests for scene participant management |
| `scene_ships` | Tests for scene ship management |
| `combat` | Tests for combat encounters and battle mechanics |
| `turn_enforcement` | Tests for turn order and enforcement rules |
| `turn_order` | Tests for turn order management |
| `actions` | Tests for action execution and effects |
| `action_tactical` | Tests for tactical/security station actions |
| `action_command` | Tests for command station actions |
| `action_conn` | Tests for conn station actions |
| `action_engineering` | Tests for engineering station actions |
| `action_science` | Tests for science station actions |
| `characters` | Tests for character management |
| `character_claiming` | Tests for character claiming in multiplayer |
| `ships` | Tests for ship management |
| `campaign` | Tests for campaign management |
| `campaign_resources` | Tests for campaign resources (momentum, threat) |
| `personnel_encounter` | Tests for personnel encounters |
| `api` | Tests for REST API endpoints |
| `vtt` | Tests for VTT (Virtual Table Top) integration |
| `universe` | Tests for universe/library integration |
| `session` | Tests for session/token management |
| `visibility` | Tests for visibility/privacy controls |
| `logging` | Tests for action logging |
| `slow` | Tests that take longer to run |

## Adding Markers to Tests

To add a marker to a test class, use the `@pytest.mark.<marker_name>` decorator:

```python
@pytest.mark.scene_lifecycle
class TestDraftToReady:
    """Tests for POST /api/scenes/{id}/transition-to-ready."""
    
    @pytest.mark.asyncio
    async def test_transition_to_ready_success(self, ...):
        # Test code here
        pass
```

To add a marker to a specific test function:

```python
class TestSomeClass:
    @pytest.mark.scene_lifecycle
    async def test_specific_feature(self, ...):
        # Test code here
        pass
```

## Backward Compatibility

All existing test runs continue to work without modification:

```bash
# Run all tests (unchanged)
pytest tests/

# Run specific file (unchanged)
pytest tests/test_scene_lifecycle.py
```

## Best Practices

1. **Add markers to test classes** rather than individual tests for consistency
2. **Use descriptive marker names** that match feature areas
3. **Keep markers focused** - prefer multiple specific markers over one general marker
4. **Document new markers** in the markers table above
5. **Use the `slow` marker** for tests that take more than a few seconds to run
