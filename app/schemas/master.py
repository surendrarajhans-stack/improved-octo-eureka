from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str
    description: str | None = None
    head_doctor_id: int | None = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    head_doctor_id: int | None = None
    is_active: bool | None = None


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Doctor schemas
class DoctorBase(BaseModel):
    user_id: int
    department_id: int
    specialization: str
    qualification: str
    license_number: str
    consultation_fee: float = 0.0
    is_available: bool = True


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    department_id: int | None = None
    specialization: str | None = None
    qualification: str | None = None
    consultation_fee: float | None = None
    is_available: bool | None = None


class DoctorResponse(DoctorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Patient schemas
class PatientBase(BaseModel):
    full_name: str
    dob: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str
    email: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    insurance_provider: str | None = None
    insurance_number: str | None = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: str | None = None
    dob: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    insurance_provider: str | None = None
    insurance_number: str | None = None


class PatientResponse(PatientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: str
    created_at: datetime


# Staff schemas
class StaffBase(BaseModel):
    user_id: int
    department_id: int
    designation: str
    employee_id: str
    joining_date: date
    salary: float = 0.0


class StaffCreate(StaffBase):
    pass


class StaffUpdate(BaseModel):
    department_id: int | None = None
    designation: str | None = None
    salary: float | None = None


class StaffResponse(StaffBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
