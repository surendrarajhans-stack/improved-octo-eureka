from datetime import datetime

from pydantic import BaseModel


class RadiologyOrderCreate(BaseModel):
    hospital_id: int
    patient_id: int
    doctor_id: int | None = None
    study_type: str
    body_part: str | None = None
    clinical_history: str | None = None
    priority: str = "ROUTINE"
    scheduled_date: datetime | None = None
    notes: str | None = None


class RadiologyReportCreate(BaseModel):
    patient_id: int
    radiologist_id: int | None = None
    findings: str | None = None
    impression: str | None = None
    recommendations: str | None = None
    is_verified: bool = False
