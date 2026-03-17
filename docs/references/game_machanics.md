# Game Mechanics Reference

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

- **GitHub Issues** - **Check this first!** Tracks planned features and current development priorities.
  - Repository: `tommertron/staStarShipSimulator`
  - View online: https://github.com/tommertron/staStarShipSimulator/issues
  - List via CLI: `gh issue list --repo tommertron/staStarShipSimulator`
  - Organized by milestones (Alpha, Beta, v1.0) and labels (station types, core-mechanics, ai-mode, etc.)
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
