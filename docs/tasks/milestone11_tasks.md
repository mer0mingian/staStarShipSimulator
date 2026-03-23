# Milestone 11 Tasks - Logging & Observability Implementation Guide

## Overview
This document provides detailed specifications for Milestone 11 - adding comprehensive logging infrastructure to trace user-observed behavior during testing and production debugging.

**Critical**: Agents implementing these tasks need to understand what user behaviors should be traceable. The goal is to make debugging and testing easier by seeing what's happening in the application.

---

## Branch Information
- **Feature Branch:** `feature/m11-logging`
- **Base Branch:** `main`
- **Model:** `opencode/minimax-m2.5-free`

---

## Status: 📋 Planned

---

## Why Logging Matters

When testing locally, you need to answer questions like:
- "Why did this dice roll fail?" → Log the dice roll input, Target Number, and result
- "Why can't this player spend Determination?" → Log the Determination state and attempt
- "Why did the scene fail to activate?" → Log the scene data and error
- "What did the GM do just before the error?" → Log GM actions
- "Why is the player stress not updating?" → Log stress changes

Currently, there's minimal logging - just werkzeug HTTP server logs set to ERROR. This makes debugging user-reported issues difficult.

---

## Implementation Plan

| Order | Task Description | Status | Agent Type |
| :---: | :--- | :---: | :--- |
| 1 | Create centralized logging module | ⏳ Pending | `python-dev` |
| 2 | Add request/response middleware | ⏳ Pending | `python-dev` |
| 3 | Implement game action loggers | ⏳ Pending | `python-dev` |
| 4 | Add GM action logging | ⏳ Pending | `python-dev` |
| 5 | Configure log levels | ⏳ Pending | `python-dev` |
| 6 | Tests and verification | ⏳ Pending | `python-dev` |
| 7 | Create user stories and E2E tests | ⏳ Pending | `explore` + `python-dev` |

---

## Detailed Task Specifications

### Task M11.1: Create Centralized Logging Module
**Agent**: `python-dev`
**Estimated Time**: ~2 hours

#### Requirements:

**A. Create new file `sta/logging.py`** with the following structure:

```python
"""Centralized logging configuration for STA VTT."""
import logging
import os
import sys
from typing import Optional

# Define logger names as constants for consistency
LOG_REQUESTS = "sta.requests"
LOG_DICE = "sta.dice"
LOG_GAME = "sta.game"
LOG_GM = "sta.gm"
LOG_COMBAT = "sta.combat"
LOG_ERRORS = "sta.errors"

# Default format - structured for easy parsing
LOG_FORMAT = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: Optional[str] = None) -> None:
    """Setup application-wide logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to LOG_LEVEL env var or DEBUG.
    """
    log_level = level or os.environ.get("LOG_LEVEL", "DEBUG")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given name.
    
    Args:
        name: Logger name (e.g., 'sta.dice')
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Initialize on import
setup_logging()
```

**B. Create utility helper functions** - add to `sta/logging.py`:

```python
def log_request_detail(logger: logging.Logger, method: str, path: str, 
                       status_code: int = None, duration: float = None,
                       user_id: int = None, campaign_id: int = None):
    """Log HTTP request with context.
    
    Args:
        logger: The requests logger
        method: HTTP method
        path: Request path
        status_code: Response status code (if available)
        duration: Request duration in seconds (if available)
        user_id: ID of user making request (if available)
        campaign_id: ID of campaign context (if available)
    """
    parts = [f"METHOD: {method}", f"PATH: {path}"]
    if status_code:
        parts.append(f"STATUS: {status_code}")
    if duration:
        parts.append(f"DURATION: {duration:.3f}s")
    if user_id:
        parts.append(f"USER: {user_id}")
    if campaign_id:
        parts.append(f"CAMPAIGN: {campaign_id}")
    
    logger.info(" | ".join(parts))


def log_character_action(logger: logging.Logger, character_id: int, character_name: str,
                         action: str, details: dict):
    """Log character-related action.
    
    Args:
        logger: Game logger
        character_id: Character ID
        character_name: Character name
        action: Action type (dice_roll, value_interaction, stress_change, etc.)
        details: Dict of action-specific details
    """
    parts = [f"CHAR_ID: {character_id}", f"CHAR_NAME: {character_name}", f"ACTION: {action}"]
    for key, value in details.items():
        parts.append(f"{key.upper()}: {value}")
    
    logger.info(" | ".join(parts))


def log_gm_action(logger: logging.Logger, campaign_id: int, user_id: int,
                 action: str, details: dict):
    """Log GM action.
    
    Args:
        logger: GM logger
        campaign_id: Campaign ID
        user_id: GM user ID
        action: Action type (threat_spend, scene_change, etc.)
        details: Dict of action-specific details
    """
    parts = [f"CAMPAIGN: {campaign_id}", f"GM_USER: {user_id}", f"ACTION: {action}"]
    for key, value in details.items():
        parts.append(f"{key.upper()}: {value}")
    
    logger.info(" | ".join(parts))


def log_error_detail(logger: logging.Logger, error: Exception, context: dict):
    """Log error with full context.
    
    Args:
        logger: Error logger
        error: Exception that occurred
        context: Dict of context information
    """
    parts = [f"ERROR: {type(error).__name__}", f"MESSAGE: {str(error)}"]
    for key, value in context.items():
        parts.append(f"{key.upper()}: {value}")
    
    logger.error(" | ".join(parts), exc_info=True)
```

---

### Task M11.2: Add Request/Response Middleware
**Agent**: `python-dev`
**Estimated Time**: ~2 hours

#### Requirements:

**Modify `sta/web/app.py`**:

1. **Import the logging module** at the top:
```python
from sta.logging import get_logger, LOG_REQUESTS, setup_logging
import time
```

2. **Initialize logging** in `create_app()` before app setup:
```python
# Initialize logging (reads LOG_LEVEL env var)
setup_logging()
```

3. **Add middleware after app creation** (before router registration):
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = get_logger(LOG_REQUESTS)
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"→ {request.method} {request.url.path}")
    
    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        # Log errors
        logger.error(f"ERROR: {request.method} {request.url.path} | {type(e).__name__}: {str(e)}")
        raise
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(f"← {request.method} {request.url.path} | {response.status_code} | {duration:.3f}s")
    
    return response
```

4. **Important Security Rules**:
   - Never log `Authorization` header or any tokens
   - Never log request bodies containing passwords
   - Truncate any logged body to first 200 characters
   - Never log binary data

---

### Task M11.3: Implement Game Action Loggers
**Agent**: `python-dev`
**Estimated Time**: ~3 hours

#### Requirements:

**A. Dice Roll Logger - Modify `sta/mechanics/dice.py`**:

1. **Add import** at the top (after existing imports):
```python
from sta.logging import get_logger, LOG_DICE
```

2. **Add logging to `task_roll()` function** - after dice are rolled but before returning result:
```python
def task_roll(...) -> TaskResult:
    # ... existing code ...
    
    rolls = roll_d20(total_dice)
    successes = count_successes(rolls, target_number, focus_value)
    complications = count_complications(rolls)
    
    # NEW: Log the dice roll
    logger = get_logger(LOG_DICE)
    logger.info(
        f"CHAR_ID: {character_id} | CHAR_NAME: {character_name} | "
        f"ATTR: {attribute} | DISCIPLINE: {discipline} | TN: {target_number} | "
        f"DIFFICULTY: {difficulty} | FOCUS: {focus} | "
        f"ROLLS: {rolls} | SUCCESSES: {successes} | COMPLICATIONS: {complications} | "
        f"MOMENTUM: {max(0, successes - difficulty) if successes >= difficulty else 0}"
    )
    
    return TaskResult(...)
```

3. **Add logging to `assist_task_roll()`** with ship assistance details

4. **Add logging to `resolve_action()`** in M10.11 extended dice logic:
```python
logger.info(
    f"CHAR_ID: {char_id} | CHAR_NAME: {char_name} | "
    f"RESOLVE_ACTION | ATTR: {attribute} | DISCIPLINE: {discipline} | "
    f"TN: {target_number} | ROLLS: {rolls} | BASE_SUCCESSES: {base_successes} | "
    f"MODIFIERS_APPLIED: {[m.type.value for m in talent_modifiers]} | "
    f"FINAL_SUCCESSES: {final_successes} | COMPLICATIONS: {final_complications} | "
    f"SUCCEEDED: {succeeded} | MOMENTUM: {momentum}"
)
```

**B. Value Interaction Logger - Modify `sta/web/routes/characters_router.py`**:

1. **Add import** at the top:
```python
from sta.logging import get_logger, LOG_GAME, log_character_action
from sta.web.routes import characters_router  # import router for name
```

2. **Log Value interactions** in relevant endpoints:
```python
# In value_interaction endpoint
logger = get_logger(LOG_GAME)
logger.info(
    f"CHAR_ID: {char_id} | CHAR_NAME: {char_name} | "
    f"VALUE: {value_name} | ACTION: {action} | "
    f"DET_BEFORE: {determination_before} | DET_AFTER: {determination_after} | "
    f"VALUE_STATUS: {new_value_status}"
)
```

**C. Stress/Resource Logger** - Same file, log stress changes:
```python
logger.info(
    f"CHAR_ID: {char_id} | CHAR_NAME: {char_name} | "
    f"STRESS_CHANGE | BEFORE: {old_stress} | AFTER: {new_stress} | "
    f"MAX: {stress_max} | REASON: {reason}"
)
```

**D. Momentum Logger**:
```python
logger.info(
    f"CHAR_ID: {char_id} | CHAR_NAME: {char_name} | "
    f"MOMENTUM_CHANGE | BEFORE: {old_momentum} | AFTER: {new_momentum} | "
    f"REASON: {reason}"
)
```

---

### Task M11.4: Add GM Action Logging
**Agent**: `python-dev`
**Estimated Time**: ~2 hours

#### Requirements:

**A. Threat Logger - Modify `sta/web/routes/api_router.py`**:

1. **Add imports** at the top:
```python
from sta.logging import get_logger, LOG_GM
```

2. **Log Threat spends** - find `POST /encounter/{id}/threat/spend` endpoint:
```python
logger = get_logger(LOG_GM)
logger.info(
    f"CAMPAIGN: {campaign_id} | ENCOUNTER: {encounter_id} | "
    f"GM_ACTION: THREAT_SPEND | TYPE: {spend_type} | "
    f"AMOUNT: {amount} | THREAT_COST: {threat_cost} | "
    f"GM_USER: {gm_user_id}"
)
```

3. **Log Threat claiming** (Momentum → Threat):
```python
logger.info(
    f"CAMPAIGN: {campaign_id} | GM_ACTION: CLAIM_THREAT | "
    f"MOMENTUM_CONVERTED: {momentum_spent} | THREAT_GAINED: {threat_gained} | "
    f"GM_USER: {gm_user_id}"
)
```

**B. Scene Management Logger - Modify `sta/web/routes/scenes_router.py`**:

1. **Add import** at top:
```python
from sta.logging import get_logger, LOG_GM
```

2. **Log scene state changes**:
```python
logger = get_logger(LOG_GM)
logger.info(
    f"CAMPAIGN: {campaign_id} | SCENE: {scene_id} | SCENE_NAME: {scene_name} | "
    f"GM_ACTION: SCENE_{action.upper()} | "
    f"GM_USER: {gm_user_id}"
)
# Actions: created, updated, activated, deactivated, completed, deleted
```

**C. NPC/Ship Spawning - Same file**:
```python
logger.info(
    f"ENCOUNTER: {encounter_id} | "
    f"GM_ACTION: SPAWN_NPC | NPC_TYPE: {npc_type} | "
    f"NAME: {npc_name} | DIFFICULTY: {difficulty}"
)
```

**D. Trait Application - Same file**:
```python
logger.info(
    f"SCENE: {scene_id} | "
    f"GM_ACTION: TRAIT_ADDED | TRAIT_NAME: {trait_name} | "
    f"EFFECT: {trait_effect} | POTENCY: {potency}"
)
```

---

### Task M11.5: Configure Log Levels
**Agent**: `python-dev`
**Estimated Time**: ~1 hour

#### Requirements:

**A. Enhance `sta/logging.py`** with environment-specific configuration:

```python
def setup_logging(level: Optional[str] = None) -> None:
    """Setup application-wide logging with environment-specific config."""
    env = os.environ.get("ENVIRONMENT", "development")
    log_level = level or os.environ.get("LOG_LEVEL", "DEBUG")
    
    # Determine handlers based on environment
    handlers = []
    
    # Console handler - always add
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Add format
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # Production: Add file handler for persistent logs
    if env == "production":
        log_dir = os.environ.get("LOG_DIR", "/var/log/sta")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(f"{log_dir}/sta.log")
        file_handler.setLevel(logging.INFO)  # Less verbose in files
        file_handler.setFormatter(console_formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Configure domain-specific levels
    domain_levels = {
        "sta.requests": logging.INFO,       # Less verbose in production
        "sta.dice": logging.DEBUG,
        "sta.game": logging.DEBUG,
        "sta.gm": logging.DEBUG,
        "sta.combat": logging.DEBUG,
        "sta.errors": logging.WARNING,       # Errors only in production
    }
    
    for domain, level in domain_levels.items():
        logger = logging.getLogger(domain)
        if env == "production":
            logger.setLevel(level)
        else:
            logger.setLevel(logging.DEBUG)  # Verbose in dev
    
    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
```

**B. Ensure environment variable support works**:
- Default: `LOG_LEVEL=DEBUG` (local dev)
- Production: `LOG_LEVEL=INFO`

---

### Task M11.6: Tests and Verification
**Agent**: `python-dev`
**Estimated Time**: ~2 hours

#### Requirements:

**A. Create test file `tests/test_logging.py`**:

```python
"""Tests for logging infrastructure."""
import pytest
import logging
from unittest.mock import patch, MagicMock

from sta.logging import (
    get_logger,
    LOG_DICE,
    LOG_GAME,
    LOG_GM,
    LOG_REQUESTS,
    LOG_ERRORS,
    setup_logging,
    log_character_action,
    log_gm_action,
    log_error_detail,
)


class TestLoggingSetup:
    """Test logging initialization."""
    
    def test_setup_logging_creates_console_handler(self):
        """Test that setup_logging creates a console handler."""
        setup_logging("DEBUG")
        root = logging.getLogger()
        assert len(root.handlers) > 0
    
    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns a logger with correct name."""
        logger = get_logger(LOG_DICE)
        assert logger.name == LOG_DICE


class TestLoggingFunctions:
    """Test logging helper functions."""
    
    def test_log_character_action_format(self):
        """Test character action log format."""
        with patch('sta.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_character_action(
                mock_logger, 
                character_id=1, 
                character_name="Kirk",
                action="dice_roll",
                details={"TN": 12, "rolls": [4, 19]}
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "CHAR_ID: 1" in call_args
            assert "CHAR_NAME: Kirk" in call_args
            assert "ACTION: dice_roll" in call_args
    
    def test_log_gm_action_format(self):
        """Test GM action log format."""
        with patch('sta.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_gm_action(
                mock_logger,
                campaign_id=1,
                user_id=10,
                action="threat_spend",
                details={"TYPE": "Trait", "COST": 2}
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "CAMPAIGN: 1" in call_args
            assert "ACTION: threat_spend" in call_args
    
    def test_log_error_detail_includes_exception(self):
        """Test error logging includes exception info."""
        with patch('sta.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            try:
                raise ValueError("test error")
            except ValueError as e:
                log_error_detail(mock_logger, e, {"context": "test"})
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "ERROR: ValueError" in call_args[0][0]
            assert call_args[1]["exc_info"] is True
```

**B. Integration test for middleware**:

```python
class TestRequestMiddleware:
    """Test request/response logging middleware."""
    
    def test_middleware_logs_request(self, client):
        """Test that middleware logs incoming requests."""
        with patch('sta.web.app.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            response = client.get("/")
            
            # Verify logging calls
            assert mock_logger.info.call_count >= 2  # Request + Response
```

**C. Verify logs in integration**:
```python
def test_dice_roll_logs_to_console(self):
    """Integration test - verify dice roll appears in logs."""
    # This test verifies the logging is actually called
    # when performing real dice rolls
    pass
```

---

## Example Log Output

After implementation, console should show:

```
2026-03-23 12:34:56 | sta.requests       | INFO    | → GET /api/campaigns
2026-03-23 12:34:56 | sta.requests       | INFO    | ← GET /api/campaigns | 200 | 0.045s
2026-03-23 12:35:01 | sta.dice           | INFO    | CHAR_ID: 1 | CHAR_NAME: Kirk | ATTR: Daring | DISCIPLINE: Command | TN: 14 | DIFFICULTY: 1 | FOCUS: False | ROLLS: [4, 19, 12] | SUCCESSES: 2 | COMPLICATIONS: 1 | MOMENTUM: 1
2026-03-23 12:35:10 | sta.game           | INFO    | CHAR_ID: 1 | CHAR_NAME: Kirk | VALUE: Duty to Starfleet | ACTION: challenge | DET_BEFORE: 1 | DET_AFTER: 2 | VALUE_STATUS: challenged
2026-03-23 12:35:15 | sta.gm             | INFO    | CAMPAIGN: 1 | ENCOUNTER: 5 | GM_ACTION: THREAT_SPEND | TYPE: Trait | AMOUNT: 1 | THREAT_COST: 2 | GM_USER: 10
2026-03-23 12:35:22 | sta.gm             | INFO    | CAMPAIGN: 1 | SCENE: 3 | SCENE_NAME: Rescue Mission | GM_ACTION: SCENE_ACTIVATED | GM_USER: 10
2026-03-23 12:35:30 | sta.errors         | ERROR   | ERROR: ValueError | MESSAGE: Invalid campaign id | CAMPAIGN: 999 | USER: 5 | Path: /api/campaigns/999
```

---

## Key Files to Modify

| File | Changes |
|------|---------|
| `sta/logging.py` | **NEW** - Centralized logging module |
| `sta/web/app.py` | Add logging middleware, import setup_logging |
| `sta/mechanics/dice.py` | Add dice roll logging |
| `sta/web/routes/characters_router.py` | Add value/stress/momentum logging |
| `sta/web/routes/api_router.py` | Add GM threat logging |
| `sta/web/routes/scenes_router.py` | Add GM scene logging |
| `tests/test_logging.py` | **NEW** - Logging tests |

---

## Subagent Prompt

### Agent 1: Complete Logging Implementation
```
task(
    description="Implement Logging Infrastructure",
    prompt="Execute Tasks M11.1 through M11.6 - Complete logging implementation.\n\nFOCUS:\n1. Create sta/logging.py with centralized logger config\n2. Add request/response middleware to sta/web/app.py\n3. Add game action loggers to dice.py and characters_router.py\n4. Add GM action loggers to api_router.py and scenes_router.py\n5. Configure log levels for dev vs production\n6. Write tests in tests/test_logging.py\n\nREQUIRED IMPLEMENTATION:\n\nA. sta/logging.py:\n- Create constants: LOG_REQUESTS='sta.requests', LOG_DICE='sta.dice', LOG_GAME='sta.game', LOG_GM='sta.gm', LOG_COMBAT='sta.combat', LOG_ERRORS='sta.errors'\n- setup_logging() function with console handler\n- get_logger(name) helper\n- log_character_action(), log_gm_action(), log_error_detail() helpers\n- LOG_FORMAT = \"%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s\"\n\nB. Middleware in sta/web/app.py:\n- Import: from sta.logging import get_logger, LOG_REQUESTS, setup_logging\n- Call setup_logging() in create_app()\n- Add @app.middleware(\"http\") to log all requests\n\nC. Game Action Loggers:\n- In sta/mechanics/dice.py: Log every roll in task_roll(), assisted_task_roll(), resolve_action()\n- Log format: \"CHAR_ID: X | CHAR_NAME: Y | ATTR: A | DISCIPLINE: D | TN: N | ROLLS: [...]\"\n- In sta/web/routes/characters_router.py: Log Value interactions, stress changes, Determination changes\n\nD. GM Action Loggers:\n- In sta/web/routes/api_router.py: Log Threat spends, threat claiming\n- In sta/web/routes/scenes_router.py: Log scene changes (created, updated, activated, completed)\n\nE. Configure:\n- Use LOG_LEVEL env var (default DEBUG)\n- Use ENVIRONMENT env var (development/production)\n\nF. tests/test_logging.py:\n- Test setup_logging creates handlers\n- Test get_logger returns correct name\n- Test helper functions format correctly\n\nRULES:\n- Never log passwords, tokens, Authorization headers, or PII\n- Truncate large request bodies to 200 chars\n- Include character/campaign ID in all game logs\n\nVERIFICATION:\nAfter implementation, run server and verify logs appear:\n  uv run python -c \"from sta.web.app import create_app; create_app()\"\nThen make a dice roll API call and verify log output shows roll details.",
    subagent_type="python-dev",
    model="opencode/minimax-m2.5-free"
)
```

---

## Verification Commands

Before submitting completion feedback, run:

```bash
# Install dependencies
uv venv && uv pip install -r requirements.txt -r requirements-dev.txt

# Run logging tests specifically
uv run pytest tests/test_logging.py -v

# Run full test suite
uv run pytest tests/ -v

# Manual verification - start server and check logs
uv run python -c "
from sta.web.app import create_app
from sta.logging import get_logger, LOG_DICE

# Test logger
logger = get_logger(LOG_DICE)
logger.info('TEST: Logging is working!')

# Create app (triggers middleware setup)
app = create_app()
print('App created, check for log output above')
"

# Run with debug logging
LOG_LEVEL=DEBUG uv run pytest tests/ -v

# Run with production config
LOG_LEVEL=INFO ENVIRONMENT=production uv run pytest tests/ -v
```

All tests must pass before marking tasks complete.

---

### Task M11.7: Create User Stories and E2E Tests
**Agent**: `explore` + `python-dev`
**Estimated Time**: ~4 hours

#### Requirements:

**A. Use brainstorming skill to create user stories** (before coding):

Following the `superpowers:brainstorming` workflow, create user stories for:

1. **Player User Stories**:
   - "As a Player, I want to create a new character so I can join a campaign"
   - "As a Player, I want to roll dice for task resolution so I can attempt actions"
   - "As a Player, I want to manage my Values so I can gain Determination"
   - "As a Player, I want to view my Stress/Determination so I know my resources"
   - "As a Player, I want to view scenes I'm participating in"
   - "As a Player, I want to read other players' Personal Logs"

2. **GM User Stories**:
   - "As a GM, I want to create a campaign so I can host games"
   - "As a GM, I want to create scenes so I can structure the story"
   - "As a GM, I want to manage Threat so I can influence encounters"
   - "As a GM, I want to start/manage encounters so I can run combat"
   - "As a GM, I want to add Traits to scenes so I can modify difficulty"

**B. Transform user stories into E2E tests**:

Using the `superpowers:e2e-testing-patterns` skill, create end-to-end tests that verify:

1. **Character Creation Flow**:
   ```python
   def test_player_can_create_character():
       # 1. Navigate to character creation
       # 2. Select species (e.g., Human)
       # 3. Assign attributes (7-12 range)
       # 4. Assign departments
       # 5. Create values (minimum 2)
       # 6. Save character
       # 7. Verify character appears in library
   ```

2. **Dice Roll Flow**:
   ```python
   def test_player_can_roll_dice():
       # 1. Select character
       # 2. Select attribute + department
       # 3. Click roll
       # 4. Verify successes counted correctly
       # 5. Verify momentum generated
   ```

3. **Value Interaction Flow**:
   ```python
   def test_player_can_use_value():
       # 1. Select character with values
       # 2. Choose value to challenge
       # 3. Add description
       # 4. Verify Determination increases
       # 5. Verify value shows as "Challenged"
   ```

4. **GM Campaign & Scene Flow**:
   ```python
   def test_gm_can_create_and_activate_scene():
       # 1. Create campaign
       # 2. Add players to campaign
       # 3. Create scene with participants
       # 4. Add Traits
       # 5. Activate scene
       # 6. Verify scene shows as active
   ```

5. **Threat Spending Flow**:
   ```python
   def test_gm_can_spend_threat():
       # 1. Start encounter
       # 2. Add trait (spend threat)
       # 3. Verify threat decreases
       # 4. Verify trait affects dice rolls
   ```

**C. Test File Structure**:

Create `tests/e2e/test_user_journeys.py`:

```python
"""End-to-end tests for core user journeys."""
import pytest
from fastapi.testclient import TestClient

# Use pytest-factory pattern for data creation


class TestCharacterCreationJourney:
    """Test character creation from start to finish."""
    
    @pytest.fixture
    def client(self, ...):
        # Create test client with auth
        pass
    
    def test_full_character_creation(self, client):
        """Test complete character creation flow."""
        # 1. Create character via API
        # 2. Assign attributes
        # 3. Assign departments
        # 4. Add values
        # 5. Verify resources calculated correctly
        pass
    
    def test_character_sheet_accessible(self, client, character_id):
        """Test character can be viewed after creation."""
        pass


class TestGameplayJourney:
    """Test actual gameplay flows."""
    
    def test_dice_roll_with_focus(self, client, character_id):
        """Test dice roll with focus applies."""
        pass
    
    def test_value_challenge_grants_determination(self, client):
        """Test Value Challenge mechanic."""
        pass
    
    def test_stress_increases_on_consequence(self, client):
        """Test Stress mechanic."""
        pass


class TestGMJourney:
    """Test GM workflows."""
    
    def test_campaign_creation_flow(self, client):
        """Test GM can create campaign."""
        pass
    
    def test_scene_activation_flow(self, client):
        """Test GM can activate scene."""
        pass
    
    def test_threat_spending(self, client):
        """Test GM spends Threat."""
        pass
```

**D. Add E2E tests for game actions**:

Create `tests/e2e/test_game_actions.py`:

```python
"""E2E tests for game mechanics in action."""
import pytest
from sta.mechanics.dice import task_roll


class TestDiceMechanicsE2E:
    """End-to-end tests for dice mechanics."""
    
    def test_successful_task_roll(self):
        """Task that succeeds generates momentum."""
        result = task_roll(
            attribute=8,  # Daring
            discipline=4,  # Security
            difficulty=1,
            dice_count=2
        )
        assert result.succeeded is not None
        # Log output should show: ROLLS, SUCCESSES, COMPLICATIONS, MOMENTUM
    
    def test_complication_on_high_roll(self):
        """Rolls at 20 cause complications."""
        result = task_roll(
            attribute=7,
            discipline=7,
            difficulty=1,
            dice_count=2
        )
        # Verify complications counted correctly


class TestResourceTrackingE2E:
    """E2E tests for resource tracking."""
    
    def test_determination_increases_on_value_challenge(self):
        """Challenge Value grants Determination."""
        # Log output should show: VALUE: X | ACTION: challenge | DET_BEFORE: 1 | DET_AFTER: 2
        pass
    
    def test_stress_fills_to_max(self):
        """Stress capped at max."""
        pass
```

**E. Priority Tests for End-to-End Coverage**:

These tests should pass for the app to be considered functional:

| Test | Priority | What it verifies |
|------|----------|-------------------|
| Character creation → character visible | Critical | Basic CRUD |
| Dice roll → result returned | Critical | Core mechanic |
| Health check endpoint | Critical | App is running |
| GM can create campaign | Critical | GM workflow |
| GM can create/scene activate | Critical | Scene system |
| Value challenge → Determination | High | Value mechanic |
| Scene traits affect dice | High | Trait system |
| Personal log visible to others | Medium | Social feature |

---

## Subagent Prompts for M11.7

### Agent 1: Create User Stories
```
task(
    description="Create user stories for E2E tests",
    prompt="Use the brainstorming skill to create user stories for the STA VTT app. Focus on:\n\n1. PLAYER actions: Create character, roll dice, manage values/stress/determination, view scenes\n2. GM actions: Create campaign, create/activate scenes, manage threat, run encounters\n\nFor each user story, define:\n- Title (As a [role], I want [goal])\n- Acceptance criteria (Given/When/Then)\n- Priority (Critical/High/Medium/Low)\n\nCreate file: docs/plans/YYYY-MM-DD-user-stories.md\n\nReference: docs/pages_overview.md for current route/template structure.",
    subagent_type="explore",
    model="opencode/minimax-m2.5-free"
)
```

### Agent 2: Implement E2E Tests
```
task(
    description="Implement E2E test suite",
    prompt="Implement E2E tests based on user stories created in M11.7.\n\nCreate tests in:\n- tests/e2e/test_user_journeys.py - Full user flows\n- tests/e2e/test_game_actions.py - Game mechanics\n\nRequired tests:\n1. Character creation flow (Foundation → Identity → Equipment)\n2. Dice roll with Success/Complication counting\n3. Value Challenge grants Determination\n4. GM creates campaign and scene\n5. GM activates scene with Traits\n6. GM spends Threat\n7. Personal log visibility (player sees OTHER players' logs)\n\nUse TestClient from FastAPI for HTTP tests.\nUse pytest fixtures for data setup.\n\nRun tests and fix any failures.",
    subagent_type="python-dev",
    model="opencode/minimax-m2.5-free"
)
```

---

## Summary: M11 Complete Test Coverage

After all M11 tasks, the test suite should include:

| Category | File | Tests |
|----------|------|-------|
| Unit Tests | `tests/test_logging.py` | Logger setup, helper functions |
| Integration | `tests/test_dice.py` | Modified to verify logging |
| E2E Journeys | `tests/e2e/test_user_journeys.py` | Character creation, gameplay, GM |
| E2E Game Actions | `tests/e2e/test_game_actions.py` | Dice, Values, Resources |

Target: All E2E tests for **core functionality must pass** before considering app functional for beta.

---

## Security Considerations

1. **NEVER log these**:
   - Passwords (login passwords, API keys)
   - Session tokens or JWTs
   - Authorization headers
   - Credit card numbers or payment info
   - Real names of players (unless visible in app already)
   - IP addresses (unless security requirement)

2. **Always sanitize**:
   - Truncate bodies > 200 chars
   - Remove known sensitive header names
   - Redact any field marked as "secret" or "password"

3. **Keep context**:
   - Always include character ID if available
   - Always include campaign ID if available  
   - Always include user ID if available (but don't log who they are)