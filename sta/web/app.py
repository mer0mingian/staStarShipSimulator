"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
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

    # Configuration - using app.state instead of Flask's app.config
    app.state.SECRET_KEY = SECRET_KEY

    # Upload folder setup (If necessary for routes handling file uploads)
    upload_folder = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.state.UPLOAD_FOLDER = upload_folder
    app.state.MAX_CONTENT_LENGTH = 16 * 1024 * 1024

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


# app = create_app() # This line might be needed elsewhere, keeping factory structure.
