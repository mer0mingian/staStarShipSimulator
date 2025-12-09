# Player View Redesign Plan

## Goal
Redesign combat_player.html to match GM view's tabbed layout structure.

## Structure Changes

### From (current):
- Extends base.html with LCARS sidebar
- Single scrolling page with all content

### To (new):
- Standalone HTML like combat_gm.html
- `.player-wrapper` > `.player-left-nav` + `.player-main`
- Tabbed navigation

## Tabs Layout

### 1. Main Tab (default)
- Turn banner (whose turn, round number)
- Resources row (Momentum, Threat)
- Turn counters (player turns used/total, enemy turns used/total)
- Tactical map (full width)
- Combat log (if needed)

### 2. Actions Tab
- Minor Actions list
- Major Actions list
- All action panels:
  - Fire panel
  - Defensive Fire panel
  - Damage Control panel
  - Ram panel
  - Reroute Power panel
  - Thrusters panel
  - Generic dice panel
- Fire results, dice results, etc.
- Selection summary
- Incoming attack panel (for defensive rolls)

### 3. Character Tab
- Character name and info
- Attributes (Control, Daring, Fitness, Insight, Presence, Reason)
- Disciplines (Command, Conn, Engineering, Medicine, Science, Security)
- Position on ship
- Any talents/abilities

### 4. Ship Tab
- Ship name and class
- Systems (Comms, Computers, Engines, Sensors, Structure, Weapons) with breach indicators
- Departments (Command, Conn, Engineering, Medicine, Science, Security)
- Weapons list (with armed status)
- Shields display
- **Reserve Power status** (moved from main view)
- Scale, Resistance info

## CSS Structure (copy from GM view pattern)

```css
.player-wrapper { display: flex; height: 100vh; }
.player-left-nav { width: 180px; flex-direction: column; }
.player-nav-tab { /* tab button styles */ }
.player-nav-tab.active { /* active state */ }
.player-main { flex: 1; overflow-y: auto; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }
```

## Color Theme
- Use green/blue colors for player (vs purple for GM)
- tab-main: butterscotch
- tab-actions: tomato/orange
- tab-character: bluey
- tab-ship: african-violet

## JavaScript to Preserve
All existing functions from combat_player.html:
- `showTab()` - new function for tab switching
- `selectAction()`, `cancelAction()`
- `executeFireAction()`, `displayFireResults()`
- `executeDefensiveFire()`
- `executeDamageControlRoll()`, `populateDamageControlOptions()`
- `executeReroutePower()`, `updateReservePowerDisplay()`
- `executeRamAction()`, `updateRamDamageDisplay()`
- `executeBuffAction()`, `executeMajorBuffAction()`
- `showThrustersPanel()`, `executeThrustersAction()`
- `startImpulseMovement()`, `executeImpulseMove()`
- `renderTacticalMap()`, `renderTacticalMapWithMoves()`
- `updateTurnDisplay()`, `updateTurnCounters()`
- `fetchTurnStatus()`, polling interval
- `showPendingAttackPanel()`, `rollDefensiveDice()`, `submitDefensiveRoll()`
- `claimTurn()`, `releaseTurn()` (multiplayer)
- Toast functions: `showToast()`, `showErrorToast()`, `showSuccessToast()`, `showInfoToast()`
- All the helper functions for range, hex distance, etc.

## Implementation Approach
Due to file size (~4000 lines), write in chunks:
1. First: CSS styles section
2. Second: HTML structure with tabs
3. Third: JavaScript (can be copied mostly verbatim)

Or: Create minimal working version first, then add features incrementally.
