from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: int
    appointment_date: date
    appointment_time: time
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    reason: str | None = None
    notes: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    appointment_date: date | None = None
    appointment_time: time | None = None
    status: AppointmentStatus | None = None
    reason: str | None = None
    notes: str | None = None


class AppointmentResponse(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: int | None = None
    created_at: datetime
