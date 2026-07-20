from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.master import Patient
from app.schemas.master import PatientCreate, PatientResponse, PatientUpdate

router = APIRouter(prefix="/patients", tags=["Patients"])


async def _generate_patient_id(db: AsyncSession) -> str:
    year = datetime.now().year
    result = await db.execute(
        select(func.count(Patient.id)).where(
            Patient.patient_id.like(f"P-{year}-%")
        )
    )
    count = result.scalar() or 0
    return f"P-{year}-{count + 1:04d}"


@router.get("/", response_model=list[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient_id = await _generate_patient_id(db)
    patient = Patient(**data.model_dump(), patient_id=patient_id)
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    await db.flush()
    await db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await db.delete(patient)
    await db.flush()
