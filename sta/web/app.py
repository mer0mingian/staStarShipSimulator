"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sta.database.async_db import engine, initialize_db
# Note: We use os.getcwd() for root path reference, assuming this file is at the root of the web logic.
# The actual project root is several directories up.

SECRET_KEY = "sta-simulator-dev-key"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for FastAPI."""
    # 1. Initialization: Create tables using the async engine
    # NOTE: Migrations (from sta/database/db.py) must be run separately before web startup.
    await initialize_db()

    yield

    # 2. Shutdown: No explicit cleanup needed for in-memory SQLite engine dispose
    pass


def create_app():
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="STA Starship Simulator API", version="1.0.0", lifespan=lifespan
    )

    # Session middleware
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

    # Static files and uploads
    root_path = os.path.dirname(__file__)

    static_dir = os.path.join(root_path, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    upload_dir = os.path.join(root_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

    # Register APIRouters (replacing Flask Blueprints)
    # Must import routers from their corresponding new files (e.g., main.py -> main_router.py)
    from sta.web.routes.main_router import main_router
    from sta.web.routes.encounters_router import encounters_router
    from sta.web.routes.api_router import api_router
    from sta.web.routes.campaigns_router import campaigns_router
    from sta.web.routes.scenes_router import scenes_router
    from sta.web.routes.universe_router import universe_router
    from sta.web.routes.characters_router import characters_router
    from sta.web.routes.ships_router import ships_router

    # Register routers with prefixes mirroring original blueprint URLs
    app.include_router(main_router, prefix="")
    app.include_router(encounters_router, prefix="/encounters")
    app.include_router(api_router, prefix="/api")
    app.include_router(campaigns_router, prefix="/campaigns")
    app.include_router(scenes_router, prefix="/scenes")
    app.include_router(universe_router, prefix="")
    app.include_router(characters_router, prefix="")
    app.include_router(ships_router, prefix="")

    return app
