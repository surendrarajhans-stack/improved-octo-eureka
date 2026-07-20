from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PatientBase(BaseModel):
    hospital_id: int
    first_name: str
    last_name: str
    dob: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None
    alt_phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    aadhar_no: str | None = None
    pan_no: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    religion: str | None = None
    nationality: str | None = None
    notes: str | None = None


class PatientCreate(PatientBase):
    allergies: str | None = None
    medical_history: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None
    alt_phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class PatientResponse(PatientBase):
    id: int
    uhid: str
    qr_code: str | None = None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PatientDocumentCreate(BaseModel):
    document_type: str
    file_path: str
    description: str | None = None


class PatientVitalsCreate(BaseModel):
    temperature: float | None = None
    blood_pressure_sys: int | None = None
    blood_pressure_dia: int | None = None
    pulse_rate: int | None = None
    respiratory_rate: int | None = None
    oxygen_saturation: float | None = None
    weight: float | None = None
    height: float | None = None
