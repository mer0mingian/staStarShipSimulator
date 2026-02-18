# STA Starship Simulator - Project Summary

## Overview
STA Starship Simulator is a web-based starship operations and combat simulator for the Star Trek Adventures 2nd Edition (STA 2e) tabletop RPG. It is designed to replace paper-based tracking of ship stats, shields, and momentum, allowing players to use their own devices (phones, tablets, laptops) while a shared "viewscreen" displays the tactical situation.

## Core Functionality
- **Multiplayer/Campaigns:** Supports GM-hosted campaigns with password protection. Players can join, claim characters, and select bridge positions.
- **Combat Simulation:** 
    - Hex-based tactical map with terrain (nebulae, asteroids).
    - Full damage system (shields, breaches, system destruction).
    - Turn-based combat alternating between players and enemies.
    - 2d20 dice system automation (successes, complications, momentum, threat).
- **Bridge Roles:** Implements specific actions for Captain, Helm, Tactical, Engineering, Science, etc.
- **View Modes:**
    - **Player View:** Station-specific controls.
    - **GM View:** Full control over encounters and NPCs.
    - **Viewscreen:** Read-only tactical display for the group.

## Technical Architecture
- **Language:** Python (likely Flask based on `app.py` references).
- **Frontend:** Web-based (templates/HTML/JS).
- **Database:** SQLite (`sta.db`).
- **Deployment:** Docker support, local Python execution, and packaged apps for Mac/Windows.
- **Dependency Management:** `requirements.txt` (Standard pip).

## Development Status
- **Beta:** Active development.
- **Key Files:**
    - `launcher.py`: Entry point.
    - `sta/`: Source code directory.
    - `CLAUDE.md`: Developer guide and rule references.
    - `ADDING_ACTIONS.md`: Guide for extending the action system.

## AI Assistant Constraints
- **Minimal Changes:** Maintain compatibility with the original branch.
- **Dependencies:** Avoid new dependencies unless strictly necessary.
- **Environment:** Use `uv` for virtual environment management (`.venv`).
