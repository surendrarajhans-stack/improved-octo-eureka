from datetime import datetime, time

from pydantic import BaseModel, ConfigDict


class DoctorBase(BaseModel):
    user_id: int
    hospital_id: int
    employee_code: str
    specialization: str
    qualification: str | None = None
    registration_no: str | None = None
    experience_years: int = 0
    consultation_fee: float = 0.0
    department_id: int | None = None
    bio: str | None = None
    languages_spoken: str | None = None


class DoctorCreate(DoctorBase):
    is_available: bool = True


class DoctorUpdate(BaseModel):
    specialization: str | None = None
    qualification: str | None = None
    consultation_fee: float | None = None
    department_id: int | None = None
    is_available: bool | None = None
    bio: str | None = None
    languages_spoken: str | None = None


class DoctorResponse(DoctorBase):
    id: int
    is_available: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DoctorScheduleCreate(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int = 15
    max_appointments: int = 20
