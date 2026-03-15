# STA Starship Simulator

A web-based **Virtual Tabletop (VTT)** for **Star Trek Adventures 2nd Edition** tabletop RPG. Currently transitioning from a combat-encounter tool to a full VTT experience.

> **Development Notice**: This project is in active development. The core starship combat system is functional. The VTT transition is in progress (see Milestones below).

## What Is This?

This app digitizes the starship combat experience for STA 2e tabletop sessions. Each player uses their own device (phone, tablet, laptop) while a shared "viewscreen" displays the tactical situation.

**Prerequisites**: Familiarity with Star Trek Adventures 2nd Edition ruleset (Momentum, Threat, 2d20 system).

---

## Milestones (VTT Transition)

| Milestone | Status | Description |
|-----------|--------|-------------|
| **M1** | ✅ Complete | Database Schema Migration |
| **M2** | ✅ Complete | Campaign Management |
| **M3** | ✅ Complete | Scene Management |
| **M4** | ✅ Complete | Character/Ship CRUD |
| **M5** | 🚧 In Progress | Combat Integration + Scene Lifecycle |
| **M6** | Pending | UI/UX Overhaul |

See `docs/delivery_plan.md` for full VTT transition plan.

---

## Current Features

- **Campaign Management**: Create/join campaigns, GM password protection, Universe Library
- **Character Management**: Full CRUD, species/role, attributes/disciplines, stress/determination, talents, default player ownership
- **Ship Management**: Full CRUD, systems/departments, weapons, shields, breaches, crew quality
- **Scene Management**: 4-state lifecycle (draft/ready/active/completed), multi-active scenes, split-party support
- **Multiplayer**: Multiple players on own devices, turn claiming
- **Starship Combat**: Hex-based tactical map, shields, breaches, Momentum/Threat
- **Bridge Actions**: Tactical, Science, Engineering, Conn, Command stations
- **View Modes**: Player, GM, and shared Viewscreen

---

## VTT Roadmap

Full VTT feature roadmap is tracked in `docs/delivery_plan.md`. Completed: M1-M4. Next: M5 (Combat Integration + Scene Lifecycle).

### Scene Lifecycle (M5 Feature)
- **draft** → **ready** → **active** → **completed**
- Multiple active scenes for split-party support
- Scene transition dialogue with connected/ready scenes

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

The project uses `uv` for fast dependency management.

```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt -r requirements-dev.txt

# Run tests using uv
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=sta tests/
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
