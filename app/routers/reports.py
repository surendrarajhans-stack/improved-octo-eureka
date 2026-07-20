from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.services.billing_service import get_revenue_report
from app.services.reports_service import (
    get_department_performance,
    get_inventory_status,
    get_patient_statistics,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/revenue")
async def revenue_report(
    start_date: str = None,
    end_date: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if start_date:
        sd = datetime.fromisoformat(start_date)
    else:
        sd = datetime(datetime.now().year, 1, 1)

    if end_date:
        ed = datetime.fromisoformat(end_date)
    else:
        ed = datetime.now()

    return await get_revenue_report(db, sd, ed)


@router.get("/patient-statistics")
async def patient_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_patient_statistics(db)


@router.get("/department-performance")
async def department_performance(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_department_performance(db)


@router.get("/inventory-status")
async def inventory_status(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_inventory_status(db)
