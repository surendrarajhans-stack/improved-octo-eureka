from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.opd import OPDVisit, Prescription, VitalSigns
from app.schemas.opd import (
    OPDVisitCreate,
    OPDVisitResponse,
    OPDVisitUpdate,
    PrescriptionCreate,
    PrescriptionResponse,
    VitalSignsCreate,
    VitalSignsResponse,
)

router = APIRouter(prefix="/opd", tags=["OPD"])


@router.get("/visits", response_model=list[OPDVisitResponse])
async def list_visits(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(OPDVisit).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/visits", response_model=OPDVisitResponse, status_code=status.HTTP_201_CREATED)
async def create_visit(
    data: OPDVisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    visit = OPDVisit(**data.model_dump())
    db.add(visit)
    await db.flush()
    await db.refresh(visit)
    return visit


@router.get("/visits/{visit_id}", response_model=OPDVisitResponse)
async def get_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(OPDVisit).where(OPDVisit.id == visit_id))
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="OPD Visit not found")
    return visit


@router.put("/visits/{visit_id}", response_model=OPDVisitResponse)
async def update_visit(
    visit_id: int,
    data: OPDVisitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(OPDVisit).where(OPDVisit.id == visit_id))
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="OPD Visit not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(visit, key, value)
    await db.flush()
    await db.refresh(visit)
    return visit


@router.post(
    "/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED
)
async def create_prescription(
    data: PrescriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    prescription = Prescription(**data.model_dump())
    db.add(prescription)
    await db.flush()
    await db.refresh(prescription)
    return prescription


@router.get("/prescriptions/{visit_id}", response_model=list[PrescriptionResponse])
async def get_prescriptions_for_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Prescription).where(Prescription.visit_id == visit_id)
    )
    return result.scalars().all()


@router.post(
    "/vitals", response_model=VitalSignsResponse, status_code=status.HTTP_201_CREATED
)
async def create_vitals(
    data: VitalSignsCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    vitals = VitalSigns(**data.model_dump())
    db.add(vitals)
    await db.flush()
    await db.refresh(vitals)
    return vitals


@router.get("/vitals/{visit_id}", response_model=list[VitalSignsResponse])
async def get_vitals_for_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(VitalSigns).where(VitalSigns.visit_id == visit_id)
    )
    return result.scalars().all()
