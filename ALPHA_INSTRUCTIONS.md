# STA Starship Simulator - Alpha Instructions

## Quick Start

### 1. Setup (one time)

```bash
# Navigate to the project directory
cd staStarShipSimulator

# Activate the virtual environment
source venv/bin/activate
```

You'll need to activate the venv each time you open a new terminal.

### 2. Run the Web App

```bash
python scripts/run_server.py
```

Open http://localhost:5001 in your browser.

### 3. Create an Encounter

1. Click **New Encounter** on the home page
2. Give your encounter a name
3. Choose your bridge position (Captain, Helm, Tactical, etc.)
4. Choose to generate a random character/ship or use existing ones
5. Click **Start Encounter**

A random enemy ship will be generated automatically.

### 4. Combat Interface

The combat screen shows:

- **Resources** - Momentum (shared pool, max 6) and Threat (GM pool)
- **Your Character** - Stats and focuses
- **Your Ship** - Shields, weapons, breaches
- **Enemy Ships** - Their current status
- **Actions** - Minor and Major actions available for your position
- **Dice Roller** - Roll 2d20 tasks

#### Rolling Dice

1. Set your **Attribute** and **Discipline** values
2. Set the **Difficulty** (shown next to each action)
3. Check **Focus Applies** if one of your focuses is relevant
4. Add **Bonus Dice** if spending Momentum (costs 1/2/3 for each extra die)
5. Click **Roll 2d20**

Results show:
- Green = success
- Blue = critical (counts as 2 successes)
- Gray = failure
- Red = complication (rolled 20)

#### Managing Resources

- Click **+/-** buttons to adjust Momentum and Threat
- Click **End Turn** to pass to the enemy

---

## CLI Scripts

### Generate a Random Character

```bash
python scripts/generate_character.py
```

### Generate a Random Ship

```bash
# Federation ship
python scripts/generate_ship.py

# Enemy ship
python scripts/generate_ship.py --enemy

# Specific faction
python scripts/generate_ship.py --enemy --faction Klingon
python scripts/generate_ship.py --enemy --faction Romulan

# Difficulty (affects stats/talents)
python scripts/generate_ship.py --enemy --difficulty easy
python scripts/generate_ship.py --enemy --difficulty hard
```

### Interactive Text Combat

```bash
python scripts/test_combat.py
```

This runs a simple text-based combat loop where you can:
- Choose your bridge position
- Select actions from a menu
- Roll dice and see results
- Watch enemy turns play out

Good for quick testing without the web UI.

---

## Game Mechanics Reference

### Task Rolls (2d20)

- Roll 2d20, trying to get **at or under** your Target Number
- **Target Number** = Attribute + Discipline
- Each die at or under = 1 success
- Roll of **1** = 2 successes (critical)
- If **Focus applies** and roll ≤ Discipline = 2 successes
- Roll of **20** = complication
- Need successes ≥ Difficulty to succeed
- Extra successes = Momentum generated

### Momentum Spends

| Cost | Effect |
|------|--------|
| 1/2/3 | Buy extra d20 (before rolling) |
| 2 | Create a trait |
| 2 | Take a second major action (+1 Difficulty) |
| 1 | Extra minor action |

### Attack Difficulties

| Attack Type | Difficulty |
|-------------|------------|
| Energy Weapons | 2 |
| Torpedoes | 3 |

### Damage

Weapons have a flat damage rating. Add the ship's **Weapons Damage Bonus**:

| Weapons Rating | Bonus |
|----------------|-------|
| 6 or lower | +0 |
| 7-8 | +1 |
| 9-10 | +2 |
| 11-12 | +3 |

Damage reduces shields first. When shields hit 0, further damage causes **breaches**.

---

## Position Actions (Quick Reference)

### Captain
- **Direct** (Major, 1 Momentum): Ally takes immediate action
- **Rally** (Major, Diff 0): Generate Momentum

### Helm
- **Impulse** (Minor): Move up to 2 zones
- **Evasive Action** (Major): Attacks vs you become opposed
- **Attack Pattern** (Major): Assist all attacks, but easier to hit

### Tactical
- **Calibrate Weapons** (Minor): Next attack +1 damage
- **Targeting Solution** (Minor): Re-roll or choose system hit
- **Fire** (Major, Diff 2/3): Attack with weapon
- **Modulate Shields** (Major): Resistance +2 until next turn

### Operations/Engineering
- **Damage Control** (Major, Diff 2+): Patch a breach
- **Regenerate Shields** (Major, Diff 2): Restore shields
- **Reroute Power** (Major): Boost a system

### Science
- **Calibrate Sensors** (Minor): Re-roll on next scan
- **Scan For Weakness** (Major, Diff 2): Next attack +2 damage or Piercing
- **Sensor Sweep** (Major, Diff 1): Get info about a zone

---

## Known Limitations (Alpha)

- Enemy ships take simplified automatic turns
- No zone/range tracking yet (assumes Close/Medium range)
- No multi-ship encounters on player side
- Breaches don't fully affect action difficulties yet
- No persistent campaign tracking

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'flask'"**
- Make sure you activated the venv: `source venv/bin/activate`

**Database issues**
- Delete `sta_simulator.db` to reset the database

**Port already in use**
- Kill the existing process or change the port in `run_server.py`
