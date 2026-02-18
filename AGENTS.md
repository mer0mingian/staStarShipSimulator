# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

## AI Assistant Rules & Project Constraints (CRITICAL)

- **Minimal Changes:** Keep changes to existing files absolutely minimal! This is a private extension to an open-source project, and compatibility with the upstream branch is paramount.
- **Dependency Management:** 
    - Do not introduce additional dependencies unless absolutely necessary.
    - Use `uv` for virtual environment management.
    - Ensure `.venv` is created and used for requirements.
    - Check `.gitignore` to ensure `.venv` is excluded.
- **Reference Files:** Do NOT read or reference `STA2e_Core Rulebook_DIGITAL_v1.1.txt`. Use `starshiprules.md` and other extracted reference files instead.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# Code Style Guidelines

Adherence to consistent code style is crucial for readability and maintainability.

### Imports
- **Ordering:** Imports should be grouped and ordered consistently. A common pattern is:
    1. Standard library imports
    2. Third-party library imports
    3. Local application imports
- **Specificity:** Import only what is necessary. Avoid wildcard imports (`import *`).

### Formatting
- **Indentation:** Use spaces for indentation (e.g., 2 or 4 spaces). Tabs are generally discouraged.
- **Line Length:** Maintain a maximum line length (e.g., 80 or 100 characters) to ensure readability.
- **Brace Style:** Follow the brace style of the surrounding code (e.g., opening brace on the same line or new line).
- **Whitespace:** Use whitespace judiciously to improve readability around operators, after commas, and to separate logical blocks of code.

### Types
- **Type Hinting:** Use type hints (e.g., in Python, TypeScript) to specify expected data types for variables, function parameters, and return values. This improves code clarity and enables static analysis.
- **Consistency:** Be consistent with the type definitions used throughout the project.

### Naming Conventions
- **Variables:** Use camelCase for most variables (e.g., `userName`, `totalCount`).
- **Constants:** Use SCREAMING_SNAKE_CASE for constants (e.g., `MAX_RETRIES`, `API_KEY`).
- **Functions/Methods:** Use camelCase or snake_case depending on the language conventions (e.g., `getUserData()`, `calculate_total()`).
- **Classes:** Use PascalCase (also known as UpperCamelCase) for class names (e.g., `UserProfile`, `DatabaseManager`).
- **Clarity:** Choose descriptive names that clearly indicate the purpose of the variable, function, or class. Avoid overly short or ambiguous names.

### Error Handling
- **Be Explicit:** Handle potential errors gracefully. Use try-catch blocks, error codes, or specific error types as appropriate for the language.
- **Informative Messages:** Error messages should be informative, providing enough context to help diagnose the issue.
- **Avoid Silencing Errors:** Do not swallow errors without proper handling or logging.
- **Consistency:** Follow the established error handling patterns used in the existing codebase.

### Comments
- **Purpose:** Use comments to explain the "why" behind complex logic, non-obvious decisions, or workarounds, rather than the "what."
- **Conciseness:** Keep comments concise and to the point.
- **Maintenance:** Ensure comments are kept up-to-date with code changes.

### General Principles
- **Readability:** Prioritize code that is easy to read and understand.
- **Simplicity:** Favor simpler solutions over overly complex ones.
- **Consistency:** Maintain consistency with the existing codebase's style and patterns.
- **DRY (Don't Repeat Yourself):** Avoid redundant code; abstract common logic into reusable functions or classes.

---

# Project Context (Merged from CLAUDE.md)

## Project Overview

A web-based starship operations and combat simulator for **Star Trek Adventures 2nd Edition** tabletop RPG. This app allows players and game masters to manage starship combat encounters digitally, with each participant accessing the app from their own device (tablet, phone, laptop).

## Core Features

### Player Features
- **Player Profiles**: Create and manage character profiles including:
  - Attributes (Control, Daring, Fitness, Insight, Presence, Reason)
  - Disciplines (Command, Conn, Engineering, Medicine, Science, Security)
  - Talents and special abilities
  - Character role/position on the ship (Captain, Helm, Tactical, Ops, Engineering, Science, Medical)

- **Ship Management**: Enter and track ship details:
  - Ship systems (Comms, Computers, Engines, Sensors, Structure, Weapons)
  - Ship departments (Command, Conn, Engineering, Medicine, Science, Security)
  - Scale, Resistance, crew complement
  - Weapons and special abilities
  - Talents

- **Action Interface**: On their turn, players can:
  - Select their action (major action + minor action)
  - Roll dice using the 2d20 system
  - See results and effects automatically calculated
  - Spend Momentum or add Threat as needed

### Game Master Features
- **Encounter Setup**: Configure combat scenarios including:
  - Enemy ships (stats, weapons, Scale)
  - Environmental zones (nebulae, asteroid fields, planetary bodies)
  - Terrain effects (difficult terrain, hazardous terrain)
  - Starting positions

- **NPC Management**: Control enemy vessels and NPCs
- **Threat Pool**: Manage the Threat pool
- **Override Controls**: Manually adjust values when needed

### Shared View Screen
A display mode for a shared screen/TV showing:
- **Tactical Map**: Zone-based map showing ship positions and terrain
- **Ship Status**:
  - Shield status (forward, aft, port, starboard)
  - Hull breaches and damage
  - System damage/disabled systems
  - Power allocation
- **Resource Pools**:
  - Momentum (group pool, max 6)
  - Threat (GM pool)
- **Turn Order**: Current initiative and whose turn it is

## Game Mechanics Reference

The app implements Star Trek Adventures 2e starship combat rules:

### Distance/Range System
- **Contact**: Docked/landed state
- **Close**: Same zone (0 zones)
- **Medium**: Adjacent zone (1 zone)
- **Long**: 2 zones away
- **Extreme**: 3+ zones away

### Dice System
- **2d20 System**: Roll 2d20, each die at or under target number = success
- **Target Number**: Attribute + Discipline
- **Complications**: Natural 20s generate complications
- **Critical Success**: Natural 1s count as 2 successes
- **Challenge Dice**: d6 for damage (1-2 = 1, 3-4 = 0, 5-6 = 1 + Effect)

### Key Resources
- **Momentum**: Earned from extra successes, spent for benefits (max 6 in pool)
- **Threat**: GM resource, players can add to gain benefits

### Ship Positions & Actions
Each bridge position has specific minor and major actions available:
- **Captain/Command**: Direct, Rally, Assist
- **Helm/Conn**: Maneuver, Evasive Action, Attack Pattern
- **Tactical/Security**: Fire Weapons, Lock On, Target Systems
- **Operations**: Transporters, Power Management, Sensors
- **Engineering**: Damage Control, Boost Power
- **Science**: Scan, Analysis, Modulate Shields

## Technical Architecture

### Stack (TBD - to be decided during implementation)
- Frontend: Web-based SPA (React/Vue/Svelte)
- Backend: Node.js or similar for real-time sync
- Database: For persistent player/ship data
- Real-time: WebSockets for live updates across devices

### Key Technical Requirements
- Mobile-responsive design (tablets are primary use case)
- Real-time synchronization between all connected clients
- Offline capability for dice rolling (nice to have)
- Session/room system for different game tables

## File Reference

- **GitHub Issues** - **Check this first!** Tracks planned features and current development priorities. Use `gh issue list` to see open issues, organized by milestones (Alpha, Beta, v1.0) and labels (station types, core-mechanics, etc.)
- `starshiprules.md` - Extracted starship combat rules from STA 2e Core Rulebook
- `STA2e_Core Rulebook_DIGITAL_v1.1.txt` - Full rulebook text (human reference only, DO NOT READ)
- `ADDING_ACTIONS.md` - Quick guide for adding new actions using the declarative system

## Action Framework (IMPORTANT!)

**The project now uses a declarative, configuration-based system for actions!**

### Why This Matters
Instead of writing ~100 lines of custom code per action, you can now add actions in **~10 lines of configuration** (30 seconds of work!).

### How to Add New Actions

**For simple buff actions** (instant effects, no roll required):
1. Add config to `sta/mechanics/action_config.py`
2. Add action name to `BUFF_ACTIONS` array in `sta/web/templates/combat.html`
3. Done! (~30 seconds)

**For task roll actions** (require a 2d20 roll):
1. Add config to `sta/mechanics/action_config.py`
2. They automatically work with the dice panel - no UI changes needed!
3. Done! (~30 seconds)

### Key Files
- `sta/mechanics/action_config.py` - Action configurations (10+ actions already defined)
- `sta/mechanics/action_handlers.py` - Generic execution handlers
- `sta/models/combat.py` - ActiveEffect model for tracking buffs
- `sta/web/routes/api.py` - Generic `/api/encounter/<id>/execute-action` endpoint
- `ADDING_ACTIONS.md` - Complete developer guide with examples

### Already Configured Actions (RFT)
These actions are already configured and ready to use:
- **Tactical**: Calibrate Weapons, Targeting Solution, Modulate Shields
- **Science**: Calibrate Sensors, Scan For Weakness, Sensor Sweep
- **Engineering**: Damage Control, Regain Power, Regenerate Shields
- **Conn**: Attack Pattern, Evasive Action, Maneuver
- **Command** (Beta): Rally

See `ADDING_ACTIONS.md` for detailed examples and patterns.

## Testing

**Run tests before committing - ALWAYS!**

### Testing Practice (CRITICAL)

1. **Before any commit**: Run `pytest` and ensure all tests pass
2. **Add tests for new features**: Every new API endpoint, UI component, or business logic must have corresponding tests
3. **Test coverage**: Aim for meaningful coverage of critical paths, not just line counts
4. **Commit only after tests pass**: Never commit broken or untested code

### Running Tests

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests (REQUIRED before committing)
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_scene.py

# Run specific test class
pytest tests/test_scene.py::TestNarrativeSceneView

# Run with coverage report
pytest --cov=sta
```

### Test Structure
- `tests/conftest.py` - Shared fixtures (test database, sample data, helpers)
- `tests/test_scene.py` - Scene management, narrative views, NPC/picture APIs
- `tests/test_turn_order.py` - Turn claiming, passing, alternation, round advancement
- `tests/test_actions_*.py` - Station-specific action tests
- `tests/test_action_logging.py` - Combat log functionality
- `tests/test_visibility.py` - Fog/terrain visibility rules

### Writing New Tests
When adding new features, add corresponding tests that verify:
1. API endpoints return correct status codes and data
2. Business logic produces expected results
3. Edge cases and error conditions are handled
4. UI templates render correctly for different scenarios

## Development Notes

When implementing features:
1. Refer to `starshiprules.md` for combat mechanics
2. Ask the user if you need clarification on rules edge cases
3. Prioritize the player turn experience - this is the core loop
4. The view screen should be visually appealing and readable from a distance
5. Keep the GM controls powerful but simple
6. **Run tests before pushing**: `pytest`
7. **After completing a feature**, add the `ready-for-testing` label to the GitHub issue: `gh issue edit <number> --add-label "ready-for-testing"`

## Future Considerations
- Character sheet integration (full character management, not just combat stats)
- Campaign management
- Combat log/history
- Sound effects for dramatic moments
- Printable summaries
