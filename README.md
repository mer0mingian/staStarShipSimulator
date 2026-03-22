# STA Starship Simulator

A web-based **Virtual Tabletop (VTT)** for **Star Trek Adventures 2nd Edition** tabletop RPG.

> **Quick Start**: See [docs/README.md](docs/README.md) for full documentation, or jump to [How to Play](#how-to-play) below.

---

## What Is This?

This app digitizes the starship combat experience for STA 2e tabletop sessions. Each player uses their own device while a shared "viewscreen" displays the tactical situation.

**Prerequisites**: Familiarity with Star Trek Adventures 2nd Edition (Momentum, Threat, 2d20 system).

---

## Features

- **Campaign Management** — Create/join campaigns, GM password protection, Universe Library
- **Character Management** — Species, roles, attributes, disciplines, stress, talents
- **Ship Management** — Systems, departments, weapons, shields, breaches, crew quality
- **Scene Management** — 4-state lifecycle (draft/ready/active/completed), split-party support
- **Multiplayer** — Multiple players on their own devices, turn claiming
- **Starship Combat** — Hex-based tactical map, Momentum/Threat pools
- **Bridge Actions** — Tactical, Science, Engineering, Conn, Command stations

---

## Milestones (VTT Transition)

| Milestone | Status | Description |
|-----------|--------|-------------|
| **M1** | ✅ Complete | Database Schema Migration |
| **M2** | ✅ Complete | Campaign Management |
| **M3** | ✅ Complete | Scene Management |
| **M4** | ✅ Complete | Character/Ship CRUD |
| **M5** | ✅ Complete | Combat Integration + Scene Lifecycle |
| **M6** | ✅ Complete | UI/UX Overhaul |
| **M7** | ✅ Complete | Import/Export + Final Integration |
| **M8** | ✅ Complete | Test Cleanup (376 passed, 0 skipped) |
| **M8.2** | ✅ Complete | Rules Understanding & Documentation |
| **M9** | ✅ Complete | Web UI & Theme Support |
| **M10** | 📋 Planned | Page Structure Rework (encounter unification) |

See [`docs/delivery_plan.md`](docs/delivery_plan.md) for full roadmap.

---

## Installation

### Docker (Recommended)
```bash
git clone https://github.com/mer0mingian/staStarShipSimulator.git
cd staStarShipSimulator
docker compose up -d
```
Available at **http://localhost:5001**

### Local Python
```bash
git clone https://github.com/mer0mingian/staStarShipSimulator.git
cd staStarShipSimulator
uv venv && uv sync
uv run uvicorn sta.web.app:app --host 0.0.0.0 --port 5001 --reload
```

---

## How to Play

### GM Setup
1. **Create a Campaign** — Set name and GM password (default: `ENGAGE1`)
2. **Add Characters** — Create or import player characters
3. **Add Ships** — Configure ship systems, weapons, scale
4. **Create Scenes** — Draft → Ready → Active → Completed lifecycle
5. **Share the Join Link** — Players join via campaign URL

### Player Experience
1. Navigate to campaign URL
2. Enter name and claim a character
3. Select bridge position (Captain, Helm, Tactical, etc.)
4. On your turn: claim it, select action, roll dice, apply results

### Combat Flow
- **Turn Structure** — Players act, then enemies act
- **Momentum** — Extra successes (max 6 in pool)
- **Threat** — GM resource for complications and enemy advantages
- **Viewscreen** — Shared display on TV/projector

---

## Documentation

| Topic | File |
|-------|------|
| Project roadmap | [`docs/delivery_plan.md`](docs/delivery_plan.md) |
| **Game mechanics** | [`docs/references/game_machanics.md`](docs/references/game_machanics.md) |
| **Data models** | [`docs/references/objects.md`](docs/references/objects.md) |
| **Talent system design** | [`docs/references/talent_system_design.md`](docs/references/talent_system_design.md) |
| Technical architecture | [`docs/references/technical.md`](docs/references/technical.md) |
| STA 2e rules reference | [`docs/rules_reference.md`](docs/rules_reference.md) |
| Development decisions | [`docs/archive/learnings_and_decisions.md`](docs/archive/learnings_and_decisions.md) |

Full documentation index: [`docs/README.md`](docs/README.md)

---

## Development

### Setup
```bash
uv venv && uv sync
```

### Testing
```bash
uv run pytest tests/ -v          # Run all tests
uv run pytest tests/m8_2/ -v     # Run M8.2 tests
uv run pytest --cov=sta tests/    # With coverage
```

### Architecture
- **FastAPI** backend with SQLAlchemy async ORM
- **Jinja2** templates with Bootstrap CSS
- **Agents**: See [`AGENTS.md`](AGENTS.md) for development workflow

### Key Files
- `sta/models/` — Pydantic data models
- `sta/database/schema.py` — SQLAlchemy ORM
- `sta/mechanics/` — Game mechanics (dice, combat, actions)
- `sta/web/routes/` — API endpoints

---

## Contributing

1. Read [`AGENTS.md`](AGENTS.md) for development workflow
2. Check [`docs/delivery_plan.md`](docs/delivery_plan.md) for roadmap
3. Run tests before submitting PRs: `uv run pytest tests/`
4. Update documentation if adding features

---

## License

Fan-made tool for Star Trek Adventures 2nd Edition (Modiphius Entertainment). Star Trek is a trademark of Paramount Global. For personal, non-commercial tabletop gaming use only.
