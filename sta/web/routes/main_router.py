from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sta.database.async_db import get_db

# Assuming EncounterRecord is defined and mapped in schema
from sta.database.schema import EncounterRecord

main_router = APIRouter()


@main_router.get("/")
async def index(db: AsyncSession = Depends(get_db)):
    """Home page - list active encounters via API."""
    try:
        # Migrate synchronous session.query to async SQLAlchemy 2.0 style
        stmt = select(EncounterRecord).filter(EncounterRecord.is_active == True)
        result = await db.execute(stmt)

        # Return list of dicts or primary key/name for simple status check instead of rendering HTML
        encounters = [{"id": e.id, "name": e.name} for e in result.scalars().all()]

        return {
            "message": "Welcome to the FastAPI STA Simulator API!",
            "active_encounters_count": len(encounters),
        }
    except Exception as e:
        # In FastAPI, raise HTTPException for API errors
        raise HTTPException(
            status_code=500, detail=f"Database error during index lookup: {e}"
        )
