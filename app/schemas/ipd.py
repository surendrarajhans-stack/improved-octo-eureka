from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.ipd import BedStatus, WardType


class WardBase(BaseModel):
    name: str
    ward_type: WardType
    floor: int = 1
    capacity: int = 10
    description: str | None = None


class WardCreate(WardBase):
    pass


class WardUpdate(BaseModel):
    name: str | None = None
    ward_type: WardType | None = None
    floor: int | None = None
    capacity: int | None = None
    description: str | None = None


class WardResponse(WardBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class BedBase(BaseModel):
    bed_number: str
    ward_id: int
    status: BedStatus = BedStatus.AVAILABLE
    features: str | None = None


class BedCreate(BedBase):
    pass


class BedUpdate(BaseModel):
    bed_number: str | None = None
    ward_id: int | None = None
    status: BedStatus | None = None
    features: str | None = None


class BedResponse(BedBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AdmissionBase(BaseModel):
    patient_id: int
    doctor_id: int
    bed_id: int
    expected_discharge: date | None = None
    diagnosis: str | None = None
    treatment_summary: str | None = None


class AdmissionCreate(AdmissionBase):
    pass


class AdmissionUpdate(BaseModel):
    expected_discharge: date | None = None
    diagnosis: str | None = None
    treatment_summary: str | None = None
    discharge_notes: str | None = None
    is_discharged: bool | None = None


class AdmissionResponse(AdmissionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    admission_date: datetime
    actual_discharge: datetime | None = None
    discharge_notes: str | None = None
    is_discharged: bool


class DailyRoundBase(BaseModel):
    admission_id: int
    doctor_id: int
    notes: str | None = None
    vitals_notes: str | None = None


class DailyRoundCreate(DailyRoundBase):
    pass


class DailyRoundUpdate(BaseModel):
    notes: str | None = None
    vitals_notes: str | None = None


class DailyRoundResponse(DailyRoundBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    round_date: datetime
