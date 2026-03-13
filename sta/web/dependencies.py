"""Common dependencies for FastAPI routes."""

import os
from fastapi import Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sta.database import get_db, CampaignRecord
from sqlalchemy import select

# Setup templates
root_path = os.path.dirname(__file__)
templates_dir = os.path.join(root_path, "templates")
templates = Jinja2Templates(directory=templates_dir)


async def get_gm_auth(request: Request, db: AsyncSession = Depends(get_db)):
    """Check if the user is authenticated as a GM for a campaign."""
    # This is a simplified version of the logic used in various routes
    # Most routes check against a specific campaign's gm_token
    return request.session.get("gm_token")


async def validate_gm_for_campaign(
    campaign_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Validate that the current user has GM access to the specified campaign."""
    gm_token = request.session.get("gm_token")
    if not gm_token:
        raise HTTPException(status_code=401, detail="GM authentication required")

    result = await db.execute(select(CampaignRecord).filter_by(id=campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign or campaign.gm_token != gm_token:
        raise HTTPException(
            status_code=401, detail="Invalid GM token for this campaign"
        )

    return campaign
