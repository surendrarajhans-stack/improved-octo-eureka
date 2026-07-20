from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class OPDVisitBase(BaseModel):
    appointment_id: int | None = None
    patient_id: int
    doctor_id: int
    chief_complaint: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    prescription_notes: str | None = None
    follow_up_date: date | None = None
    visit_fee: float = 0.0
    is_paid: bool = False


class OPDVisitCreate(OPDVisitBase):
    pass


class OPDVisitUpdate(BaseModel):
    chief_complaint: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    prescription_notes: str | None = None
    follow_up_date: date | None = None
    visit_fee: float | None = None
    is_paid: bool | None = None


class OPDVisitResponse(OPDVisitBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    visit_date: datetime


class PrescriptionBase(BaseModel):
    visit_id: int
    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: str | None = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionUpdate(BaseModel):
    medicine_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    instructions: str | None = None


class PrescriptionResponse(PrescriptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class VitalSignsBase(BaseModel):
    visit_id: int
    blood_pressure: str | None = None
    pulse: int | None = None
    temperature: float | None = None
    weight: float | None = None
    height: float | None = None
    oxygen_saturation: float | None = None


class VitalSignsCreate(VitalSignsBase):
    pass


class VitalSignsUpdate(BaseModel):
    blood_pressure: str | None = None
    pulse: int | None = None
    temperature: float | None = None
    weight: float | None = None
    height: float | None = None
    oxygen_saturation: float | None = None


class VitalSignsResponse(VitalSignsBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recorded_at: datetime
