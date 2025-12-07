# How to Start the Dev Server

## Option 1: Using dev.sh (Recommended)

If you have a virtual environment set up:

```bash
./dev.sh
```

This script:
- Activates the `venv` virtual environment
- Sets `FLASK_DEBUG=1` for hot reload
- Runs on `http://localhost:5001`

### First-time setup for dev.sh

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Option 2: Manual (without venv)

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Run the dev server
FLASK_APP=sta.web.app:create_app FLASK_DEBUG=1 flask run --port 5001
```

## Option 3: Using Docker

For development with hot reload:

```bash
docker compose --profile dev up sta-simulator-dev
```

For production mode:

```bash
docker compose up -d
```

## Access the App

Once running, open: **http://localhost:5001**
