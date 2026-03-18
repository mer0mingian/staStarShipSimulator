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

## Campaign Resource Pools (Ch 4, 9)

### Momentum Pool
- **Scope**: Campaign-wide pool, max 6
- **Gain Sources**: Successful tasks (1-3 per Ch 4), Extended Task breakthroughs, GM awards
- **Spend Uses**: Re-rolls, effect boosts, Keep Initiative (2), trigger complications, extra actions
- **Reset**: Typically resets between sessions or scenes

### Threat Pool
- **Scope**: Campaign-wide pool, max 24 (typical)
- **Gain Sources**: Failed tasks, complications, GM awards, NPC actions, player Momentum-to-Threat trades
- **Spend Uses**: GM introduces hazards, complications, reinforcements, NPC advantages, adversarial momentum
- **Note**: Unlike Momentum, Threat does NOT reset between sessions

### Implementation
- `ThreatManager` class: `sta/mechanics/threat_manager.py`
- `MomentumManager` class: `sta/mechanics/momentum_manager.py`
- Stored in `CampaignRecord` as `threat` and `momentum` columns

### NPC Stress/Threat Distinction (Ch 11)

- **NPCs do NOT have Stress tracks** - they cannot take Stress damage or Avoid Injury via Stress
- **NPCs use Threat instead of Determination** - values that would grant Determination add 3 to Personal Threat instead
- **Supporting Characters**: No values → no Stress. One value → max Stress = Fitness ÷ 2 (round up). Two or more values → max Stress = Fitness (like main PCs)
- **Notable NPCs**: Avoid Injury by spending Threat equal to severity (once per scene). Personal Threat pool: typically 3.
- **Major NPCs**: Avoid Injury by spending Threat equal to severity (unlimited per scene). Personal Threat pool: 6 + 1 per Value.
- **Minor NPCs**: Instantly defeated on any Injury. Cannot Avoid Injury. No Personal Threat.
- **NPC Ship actions**: Based on Crew Quality rating (e.g., 10 for Talented), not department attributes — unless a specific NPC is assigned to the station.
- **Personal Threat**: Separate from GM campaign Threat. Refreshes at start of each scene. NPCs may spend from either pool in any combination.

See `docs/sta2e_rules/sta2ecore_ch11.md` (lines 137-151, 73-88) for full NPC injury and Personal Threat rules.

## Ship Stress, Shields, and Breaches (Ch 5, 8)

### Shields Track
- **Formula**: Max Shields = Structure + Scale + Security (Ch05 line 629; Ch08 line 1029)
- Shields function as a depletion track — reduce by damage amount
- **Shield Breakthrough points** (Ch08 lines 1111-1172):
  - 50% threshold: Ship becomes *Shaken* (choose minor damage result)
  - 25% threshold: Ship becomes *Shaken* again; if already Shaken, suffers a Breach instead
  - 0% (shields down): Ship suffers a Breach immediately
- Shields reset to maximum at the start of each new scene (Ch08 line 1111)

### Resistance
- **Formula**: Resistance = ceil(Scale ÷ 2) + Structure bonus (Ch05 lines 565-570)
  - Structure 6 or lower: +0
  - Structure 7-8: +1
  - Structure 9-10: +2
  - Structure 11-12: +3
  - Structure 13+: +4
- Resistance reduces incoming damage by 1 per point (minimum damage 1)

### Breaches
- A ship is **destroyed** when it has accumulated more breaches than its Scale (total), **OR** more breaches to a single system than half its Scale (round down) — whichever limit is reached first (Ch08 lines 1160-1172)
- **Shaken** is a Ship Trait triggered by minor damage (Ch08 line 1114); the captain picks one: Brace for Impact, Losing Power, or Casualties/Minor Damage

### Task vs. Action Distinction
- **Tasks** (Ch07): Any dice-roll where the outcome is uncertain. Includes Challenge component tasks, combat attacks, skill checks, and Extended Task rolls.
- **Actions** (Ch08.4): Bridge-position-specific operations during Starship Combat only. Actions are executed by characters at ship stations (Command, Helm, Tactical, Operations, Science, Communications).

## Initiative and Momentum Spends (Ch 7, 8)

### Keep the Initiative (Ch 07, 08)
- **Cost**: 2 Momentum (Immediate) — same cost in Personal, Social, and Starship conflict
- **Effect**: Pass the next turn to an ally on your own side instead of the opposition
- **Restriction**: After someone Keeps the Initiative, no one on that side may do so again until the opposition has taken at least one turn
- **NPC version**: Spend 2 Threat to Keep the Initiative (pass turn to an allied NPC)

### Threat Spend for Reinforcements (Ch 09)
- **Starship reinforcements**: Spend Threat equal to the new ship's Scale
- **Minor NPC reinforcements**: 1 Threat each
- **Notable NPC reinforcements**: 2 Threat each

See Ch07 (lines 266-267, 389), Ch08.4 (line 506), Ch09 (lines 709-715).

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
