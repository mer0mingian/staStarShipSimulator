# STA Starship Simulator

A web-based starship operations and combat simulator for **Star Trek Adventures 2nd Edition** tabletop RPG.

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed

### Run the Application

```bash
# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

The application will be available at **http://localhost:5001**

### Development Mode

For development with hot reload:

```bash
docker compose --profile dev up sta-simulator-dev
```

### Data Persistence

The SQLite database is stored in a Docker volume (`sta-simulator-data`) and persists across container restarts.

To reset the database:
```bash
docker compose down -v  # removes volumes
docker compose up -d
```

## Local Development (without Docker)

### Requirements
- Python 3.10+

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
FLASK_APP=sta.web.app:create_app flask run --port 5001
```

The application will be available at **http://localhost:5001**

## Usage

1. Open the application in your browser
2. Create a new encounter or select an existing one
3. Choose your role:
   - **Player**: Control your character and ship
   - **Game Master**: Oversee the encounter and control enemy vessels
4. Multiple users can join the same encounter with different roles
