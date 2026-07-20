from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.ipd import Admission, Bed, BedStatus, DailyRound, Ward
from app.schemas.ipd import (
    AdmissionCreate,
    AdmissionResponse,
    AdmissionUpdate,
    BedCreate,
    BedResponse,
    BedUpdate,
    DailyRoundCreate,
    DailyRoundResponse,
    WardCreate,
    WardResponse,
    WardUpdate,
)

router = APIRouter(prefix="/ipd", tags=["IPD"])


# Wards
@router.get("/wards", response_model=list[WardResponse])
async def list_wards(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Ward).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/wards", response_model=WardResponse, status_code=status.HTTP_201_CREATED)
async def create_ward(
    data: WardCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ward = Ward(**data.model_dump())
    db.add(ward)
    await db.flush()
    await db.refresh(ward)
    return ward


@router.get("/wards/{ward_id}", response_model=WardResponse)
async def get_ward(
    ward_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Ward).where(Ward.id == ward_id))
    ward = result.scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    return ward


@router.put("/wards/{ward_id}", response_model=WardResponse)
async def update_ward(
    ward_id: int,
    data: WardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Ward).where(Ward.id == ward_id))
    ward = result.scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ward, key, value)
    await db.flush()
    await db.refresh(ward)
    return ward


# Beds
@router.get("/beds", response_model=list[BedResponse])
async def list_beds(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Bed).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/beds", response_model=BedResponse, status_code=status.HTTP_201_CREATED)
async def create_bed(
    data: BedCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    bed = Bed(**data.model_dump())
    db.add(bed)
    await db.flush()
    await db.refresh(bed)
    return bed


@router.get("/beds/{bed_id}", response_model=BedResponse)
async def get_bed(
    bed_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Bed).where(Bed.id == bed_id))
    bed = result.scalar_one_or_none()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return bed


@router.put("/beds/{bed_id}", response_model=BedResponse)
async def update_bed(
    bed_id: int,
    data: BedUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Bed).where(Bed.id == bed_id))
    bed = result.scalar_one_or_none()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(bed, key, value)
    await db.flush()
    await db.refresh(bed)
    return bed


@router.post("/beds/{bed_id}/admit-patient", response_model=AdmissionResponse)
async def admit_patient(
    bed_id: int,
    data: AdmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Bed).where(Bed.id == bed_id))
    bed = result.scalar_one_or_none()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if bed.status != BedStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Bed is not available")

    admission_data = data.model_dump()
    admission_data["bed_id"] = bed_id
    admission = Admission(**admission_data)
    db.add(admission)
    bed.status = BedStatus.OCCUPIED
    await db.flush()
    await db.refresh(admission)
    return admission


# Admissions
@router.get("/admissions", response_model=list[AdmissionResponse])
async def list_admissions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Admission).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/admissions", response_model=AdmissionResponse, status_code=status.HTTP_201_CREATED
)
async def create_admission(
    data: AdmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    admission = Admission(**data.model_dump())
    db.add(admission)

    # Mark bed as occupied
    result = await db.execute(select(Bed).where(Bed.id == data.bed_id))
    bed = result.scalar_one_or_none()
    if bed:
        bed.status = BedStatus.OCCUPIED

    await db.flush()
    await db.refresh(admission)
    return admission


@router.get("/admissions/{admission_id}", response_model=AdmissionResponse)
async def get_admission(
    admission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Admission).where(Admission.id == admission_id))
    admission = result.scalar_one_or_none()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    return admission


@router.put("/admissions/{admission_id}", response_model=AdmissionResponse)
async def update_admission(
    admission_id: int,
    data: AdmissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Admission).where(Admission.id == admission_id))
    admission = result.scalar_one_or_none()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(admission, key, value)
    await db.flush()
    await db.refresh(admission)
    return admission


@router.post("/admissions/{admission_id}/discharge", response_model=AdmissionResponse)
async def discharge_patient(
    admission_id: int,
    discharge_notes: str = "",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Admission).where(Admission.id == admission_id))
    admission = result.scalar_one_or_none()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    if admission.is_discharged:
        raise HTTPException(status_code=400, detail="Patient already discharged")

    admission.is_discharged = True
    admission.actual_discharge = datetime.now(timezone.utc)
    admission.discharge_notes = discharge_notes

    # Free the bed
    bed_result = await db.execute(select(Bed).where(Bed.id == admission.bed_id))
    bed = bed_result.scalar_one_or_none()
    if bed:
        bed.status = BedStatus.AVAILABLE

    await db.flush()
    await db.refresh(admission)
    return admission


# Daily rounds
@router.post(
    "/daily-rounds", response_model=DailyRoundResponse, status_code=status.HTTP_201_CREATED
)
async def create_daily_round(
    data: DailyRoundCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    round_entry = DailyRound(**data.model_dump())
    db.add(round_entry)
    await db.flush()
    await db.refresh(round_entry)
    return round_entry


@router.get("/daily-rounds/{admission_id}", response_model=list[DailyRoundResponse])
async def get_daily_rounds(
    admission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(DailyRound).where(DailyRound.admission_id == admission_id)
    )
    return result.scalars().all()
