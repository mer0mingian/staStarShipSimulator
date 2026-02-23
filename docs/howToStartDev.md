# STA Starship Simulator - Developer Guide

## Development Environment Setup

### 1. Prerequisites
- **Python 3.13+** (Required)
- **uv** (Recommended package manager)
- **Docker** & **Docker Compose** (Optional, for containerized testing)

### 2. Local Setup (Recommended)
This project uses `uv` for fast dependency management.

```bash
# 1. Clone the repository
git clone https://github.com/tommertron/staStarShipSimulator.git
cd staStarShipSimulator

# 2. Create a virtual environment with Python 3.13
uv venv --python 3.13
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# 4. Run tests
uv run pytest

# 5. Run the application (Development mode)
# This uses Flask's built-in server with hot reloading
FLASK_APP=sta.web.app:create_app FLASK_DEBUG=1 flask run --port 5001
```

### 3. Docker Setup
You can also run the application and tests in Docker containers.

```bash
# Run tests in Docker
docker compose -f docker-compose.test.yml up --build

# Run application in Docker (Development mode)
docker compose --profile dev up --build
```

## Project Structure
- `sta/`: Source code directory
    - `web/`: Web application (routes, templates, static files)
    - `models/`: Database models (SQLAlchemy)
    - `mechanics/`: Game logic implementation
- `tests/`: Unit and integration tests
- `docs/`: Documentation

## Testing Guidelines
- Run `pytest` before committing any changes.
- Ensure all tests pass locally.
- Write new tests for any new features or bug fixes.
- Use `pytest --cov=sta` to check code coverage.

## Code Style & Conventions
- Follow PEP 8 guidelines.
- Use type hints where possible.
- Keep changes minimal and focused.
- **Do not introduce new dependencies** unless absolutely necessary.
- Refer to `AGENTS.md` for AI assistant rules and project constraints.
