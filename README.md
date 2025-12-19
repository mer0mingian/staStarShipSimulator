# STA Starship Simulator

A web-based starship operations and combat simulator for **Star Trek Adventures 2nd Edition** tabletop RPG.

> **Beta Notice**: This project is in active development. Core starship combat features are functional, but some actions and features are still being implemented. Bug reports and feedback welcome!

## What Is This?

This app digitizes the starship combat experience for STA 2e tabletop sessions. Instead of tracking ship stats, breaches, shields, and momentum on paper, each player can use their own device (phone, tablet, laptop) while a shared "viewscreen" displays the tactical situation for everyone.

**Prerequisites**: This app assumes familiarity with the Star Trek Adventures 2nd Edition ruleset. It handles the bookkeeping and dice math, but you should understand concepts like Momentum, Threat, ship systems, breaches, and the 2d20 task resolution system.

**Best For**: In-person play sessions where the crew is on a starship, especially during starship combat encounters.

---

## Screenshots

**Role Selection** - Choose to join as a Player or Game Master
![Role Selection Screen](Screenshot%20-%20Star%20Trek%20Adventures%20Role%20Selection%20Screen.png)

**Viewscreen** - Tactical display showing the hex map, ship status, and resources
![Viewscreen Tactical Display](Screenshot%20-%20Battle%20at%20the%20Neutral%20Zone%20Tactical%20Display%20Round%201.png)

**GM View** - Manage all ships, Momentum/Threat pools, and take actions for enemy vessels
![GM Control Screen](Screenshot%20-%20Battle%20at%20the%20Neutral%20Zone%20Round%201.png)

**Player View** - See your turn summary and wait during enemy turns
![Player View During Enemy Turn](Screenshot%20-%20Battle%20at%20the%20Neutral%20Zone%20Enemy%20Turn%20Round%201.png)

---

## Features

### What's Ready

**Campaign & Multiplayer Support**
- Create campaigns with GM password protection
- Multiple players join from their own devices
- Players claim characters and choose bridge positions (Captain, Helm, Tactical, etc.)
- Turn claiming system for organized multiplayer combat

**Starship Combat**
- Hex-based tactical map with terrain (nebulae, asteroid fields, dust clouds)
- Full damage system: shields, breaches, system destruction
- Reserve power management
- Momentum pool (shared, max 6) and Threat pool
- Turn-based combat with player/enemy alternation
- Fog of war - ships hidden in dense terrain until detected
- Combat logging for all actions

**Bridge Station Actions**
- **Tactical**: Fire Weapons, Calibrate Weapons, Targeting Solution, Modulate Shields, Lock On, Defensive Fire
- **Science**: Calibrate Sensors, Scan for Weakness, Sensor Sweep
- **Engineering**: Damage Control, Regain Power, Regenerate Shields, Reroute Power
- **Conn/Helm**: Impulse, Thrusters, Attack Pattern, Evasive Action, Maneuver, Ram
- **Command**: Rally
- **Standard**: Pass, Change Position, Raise/Lower Shields, Arm/Disarm Weapons

**Three View Modes**
1. **Player View**: Individual controls for your station's actions
2. **GM View**: Full encounter control, enemy ship management, overrides
3. **Viewscreen**: Read-only tactical display for TV/projector

**Hailing System**
- Ships can hail each other
- Audio notifications when hailed

### What's Coming (Not Yet Implemented)

- Operations Station actions (Transporters, etc.)
- Medical Station actions
- Command Station: Direct action
- Cloaking mechanics
- Warp travel
- Ship talents
- Full character sheet integration (focuses, values, talents)
- Keep the Initiative momentum spend
- Sound effects for combat events

---

## Installation

### Option 1: Mac App

**[Download for Mac](https://github.com/tommertron/staStarShipSimulator/releases/download/install/STA-Starship-Simulator-0.1.0-mac.dmg)** (28 MB)

1. Open the downloaded DMG file
2. Drag "STA Starship Simulator" to your Applications folder
3. Launch from Applications (you may need to right-click → Open the first time)
4. Your browser will open automatically to the app

The app runs a local server - share the Network URL shown in the console window with players on your local network.

### Option 2: Windows App

**[Download for Windows](https://github.com/tommertron/staStarShipSimulator/releases/download/install/STA-Starship-Simulator-0.1.0-windows.zip)** (24 MB)

1. Extract the downloaded zip file
2. Run `STA Starship Simulator.exe`
3. Your browser will open automatically to the app

**Note:** Windows may show a SmartScreen warning since the app isn't signed. Click "More info" → "Run anyway".

The app runs a local server - share the Network URL shown in the console window with players on your local network.

### Option 3: Docker

**Prerequisites**: Docker and Docker Compose installed

```bash
# Clone the repository
git clone https://github.com/tommertron/staStarShipSimulator.git
cd staStarShipSimulator

# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

The application will be available at **http://localhost:5001**

### Option 4: Local Python

**Prerequisites**: Python 3.10+

```bash
# Clone the repository
git clone https://github.com/tommertron/staStarShipSimulator.git
cd staStarShipSimulator

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
FLASK_APP=sta.web.app:create_app flask run --port 5001
```

The application will be available at **http://localhost:5001**

---

## How to Play

### Initial Setup (GM)

1. **Create a Campaign**
   - Go to the home page and click "Create New Campaign"
   - Enter a campaign name and GM password (default: `ENGAGE1`)
   - You'll be taken to the campaign management screen

2. **Add Players**
   - In campaign management, add player characters
   - You can generate random characters or create custom ones
   - Each character needs: name, attributes (Control, Daring, Fitness, Insight, Presence, Reason), and disciplines (Command, Conn, Engineering, Medicine, Science, Security)

3. **Add Ships**
   - Add your player ship to the campaign's ship pool
   - Configure ship systems, departments, weapons, and scale
   - Set one ship as the "active" player ship

4. **Create an Encounter**
   - From the campaign, create a new encounter
   - Add enemy ships
   - Configure the tactical map (add terrain if desired)
   - Set initial positions

5. **Share the Join Link**
   - Players can join by navigating to your campaign
   - Or share the direct join URL

### Joining as a Player

1. Navigate to the campaign URL (get this from your GM)
2. Enter your name
3. Claim an available character
4. Select your bridge position (Captain, Helm, Tactical, etc.)
5. You'll see actions available to your station

### During Combat

**Turn Structure**
- Combat alternates between player side and enemy side
- When it's the players' turn, any player can "claim" the turn
- The player who claims the turn takes their major and minor actions
- After all players have acted, enemies take their turns

**Taking Actions**
1. Claim the turn when it's the players' side
2. Select a minor action (optional) and/or major action
3. For task rolls: set your target number (Attribute + Discipline + modifiers)
4. Roll dice using the dice panel
5. Apply results (the app calculates successes, complications, etc.)
6. Your turn ends automatically after using your actions

**The Dice Panel**
- Set your target number for the roll
- Choose how many d20s to roll (base 2, buy more with Momentum/Threat)
- Click "Roll" to roll
- Results show: successes, complications, and total
- Challenge dice (for damage) are handled separately

**Momentum & Threat**
- Extra successes become Momentum (stored in shared pool, max 6)
- Players can spend Threat to gain benefits (adds to GM's Threat pool)
- GM spends Threat to power enemy actions and complications

### Setting Up the Viewscreen

1. Open the encounter
2. Click "Viewscreen" mode
3. Display this on a TV or projector for everyone to see
4. Shows: tactical map, ship status, shields, breaches, Momentum/Threat pools

---

## Tips for Best Experience

- **Use a tablet or larger phone** - The interface works on mobile but is designed for larger screens
- **Dedicate one screen to the viewscreen** - A TV or laptop showing the viewscreen helps everyone stay oriented
- **The GM should have their own device** - Separate from the viewscreen
- **Familiarize players with their station** - Each bridge position has different available actions
- **Keep the STA 2e rulebook handy** - For edge cases and rules clarifications

---

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=sta

# Run specific test file
pytest tests/test_turn_order.py
```

### Development Mode with Hot Reload

```bash
# Using Docker
docker compose --profile dev up sta-simulator-dev

# Or locally
FLASK_DEBUG=1 FLASK_APP=sta.web.app:create_app flask run --port 5001
```

### Resetting the Database

```bash
# Docker
docker compose down -v  # removes volumes
docker compose up -d

# Local - just delete the database file
rm -f sta.db
```

---

## Contributing

Bug reports and feature requests are welcome! Please open an issue on GitHub.

If you'd like to contribute code:
1. Check existing issues for what needs work
2. Read `CLAUDE.md` for project architecture details
3. Read `ADDING_ACTIONS.md` if you're adding new bridge station actions
4. Run tests before submitting PRs: `pytest`

---

## License

This project is a fan-made tool for use with Star Trek Adventures 2nd Edition by Modiphius Entertainment. Star Trek and all related marks are trademarks of Paramount Global.

This software is provided as-is for personal, non-commercial use in tabletop gaming sessions.
