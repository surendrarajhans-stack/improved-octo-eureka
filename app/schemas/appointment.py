from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class AppointmentBase(BaseModel):
    hospital_id: int
    patient_id: int
    doctor_id: int
    department_id: int | None = None
    appointment_date: date
    appointment_time: time
    appointment_type: str = "OPD"
    chief_complaint: str | None = None
    priority: str = "NORMAL"
    consultation_fee: float = 0.0
    notes: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    appointment_date: date | None = None
    appointment_time: time | None = None
    status: str | None = None
    notes: str | None = None
    cancelled_reason: str | None = None


class AppointmentResponse(AppointmentBase):
    id: int
    slot_number: int
    token_number: int
    status: str
    payment_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AppointmentStatusUpdate(BaseModel):
    status: str
    cancelled_reason: str | None = None
