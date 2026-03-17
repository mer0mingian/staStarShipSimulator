# Technical Reference

## Current Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **API**: REST endpoints via Flask routes

### Frontend
- **Templates**: Jinja2 (Flask templates)
- **Styling**: Bootstrap CSS
- **JavaScript**: Vanilla JS for interactivity

### Development
- **Testing**: pytest
- **Package Management**: uv
- **Virtual Environment**: `.venv/`

## Project Structure

```
sta/
├── database/           # SQLAlchemy models and schema
│   ├── schema.py      # Main database schema
│   └── vtt_schema.py  # VTT-specific models
├── mechanics/          # Game logic
│   └── action_config.py  # Declarative action system
├── models/            # Data models
│   ├── vtt/          # Pydantic VTT models (new)
│   └── legacy/       # Legacy dataclass models
├── web/              # Web application
│   ├── routes/       # Flask route handlers
│   ├── templates/    # Jinja2 templates
│   └── static/      # CSS, JS, images
└── ...
```

## Key Files

- `sta/web/app.py` - Flask application factory
- `sta/database/schema.py` - Database models
- `ADDING_ACTIONS.md` - Guide for adding new actions

## Running the Application

```bash
# Development
FLASK_APP=sta.web.app:create_app flask run --port 5001

# With debug
FLASK_DEBUG=1 FLASK_APP=sta.web.app:create_app flask run --port 5001
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=sta tests/
```

## Database

- SQLite: `sta_simulator.db`
- Reset: `rm -f sta.db` then restart app

## API Patterns

All API endpoints follow REST conventions and return JSON.
See route files in `sta/web/routes/` for endpoint definitions.
