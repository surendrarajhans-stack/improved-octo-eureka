from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.ipd import Admission, Bed
from app.services.ai_service import (
    forecast_bed_occupancy,
    predict_readmission_risk,
    suggest_diagnosis,
)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class ReadmissionRequest(BaseModel):
    patient_age: int
    diagnosis: str
    previous_admissions: int = 0


class DiagnosisRequest(BaseModel):
    symptoms: list[str]


@router.post("/predict-readmission")
async def predict_readmission(
    data: ReadmissionRequest,
    current_user=Depends(get_current_user),
):
    return predict_readmission_risk(data.patient_age, data.diagnosis, data.previous_admissions)


@router.post("/suggest-diagnosis")
async def get_diagnosis_suggestions(
    data: DiagnosisRequest,
    current_user=Depends(get_current_user),
):
    suggestions = suggest_diagnosis(data.symptoms)
    return {"symptoms": data.symptoms, "suggestions": suggestions}


@router.get("/bed-occupancy-forecast")
async def bed_occupancy_forecast(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Get historical daily admission counts (last 30 days)
    total_beds_result = await db.execute(select(func.count(Bed.id)))
    total_beds = total_beds_result.scalar() or 1

    admissions_result = await db.execute(
        select(
            func.date(Admission.admission_date).label("date"),
            func.count(Admission.id).label("count"),
        )
        .group_by(func.date(Admission.admission_date))
        .order_by(func.date(Admission.admission_date).desc())
        .limit(30)
    )
    rows = admissions_result.all()
    historical_occupancy = [
        round((row[1] / total_beds) * 100, 2) for row in reversed(rows)
    ]

    result = forecast_bed_occupancy(historical_occupancy, forecast_days=days)
    result["total_beds"] = total_beds
    return result
