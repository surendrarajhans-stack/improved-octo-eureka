from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.services.dashboard_service import get_dashboard_stats, get_recent_activity

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_dashboard_stats(db)


@router.get("/recent-activity")
async def recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_recent_activity(db, limit)
