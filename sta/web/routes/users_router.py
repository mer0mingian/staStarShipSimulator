"""User preferences routes for theme settings (FastAPI)."""

from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Cookie,
    Body,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sta.database.async_db import get_db
from sta.database.schema import CampaignPlayerRecord

users_router = APIRouter(prefix="/api/users", tags=["users"])

VALID_THEMES = {"light", "dark"}


async def _get_current_player(
    sta_session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> CampaignPlayerRecord:
    """Get current player from session token."""
    if not sta_session_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    stmt = select(CampaignPlayerRecord).filter(
        CampaignPlayerRecord.session_token == sta_session_token,
    )
    result = await db.execute(stmt)
    player = result.scalars().first()

    if not player:
        raise HTTPException(status_code=401, detail="Invalid session token")

    return player


@users_router.get("/me/theme")
async def get_theme_preference(
    player: CampaignPlayerRecord = Depends(_get_current_player),
):
    """Get the current user's theme preference."""
    return {
        "theme_preference": player.theme_preference,
    }


@users_router.put("/me/theme")
async def set_theme_preference(
    data: dict = Body(...),
    player: CampaignPlayerRecord = Depends(_get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Set the current user's theme preference."""
    theme = data.get("theme_preference")

    if theme is None:
        raise HTTPException(status_code=400, detail="theme_preference is required")

    if theme not in VALID_THEMES:
        valid_themes = ", ".join(sorted(VALID_THEMES))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme_preference. Must be one of: {valid_themes}",
        )

    player.theme_preference = theme
    await db.commit()

    return {
        "success": True,
        "theme_preference": player.theme_preference,
    }


@users_router.delete("/me/theme")
async def clear_theme_preference(
    player: CampaignPlayerRecord = Depends(_get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Clear the current user's theme preference (reset to default)."""
    player.theme_preference = None
    await db.commit()

    return {
        "success": True,
        "theme_preference": None,
    }
