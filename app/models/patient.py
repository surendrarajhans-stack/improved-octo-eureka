from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class AllergySeverity(str, Enum):
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    uhid = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    alt_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    photo = Column(Text, nullable=True)
    qr_code = Column(Text, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(100), nullable=True)
    insurance_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=True)
    aadhar_no = Column(String(20), nullable=True)
    pan_no = Column(String(20), nullable=True)
    marital_status = Column(String(50), nullable=True)
    occupation = Column(String(100), nullable=True)
    religion = Column(String(100), nullable=True)
    nationality = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class PatientMedicalHistory(TimestampMixin, Base):
    __tablename__ = "patient_medical_histories"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    condition = Column(String(255), nullable=False)
    diagnosed_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class PatientAllergy(TimestampMixin, Base):
    __tablename__ = "patient_allergies"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    allergen = Column(String(255), nullable=False)
    reaction = Column(String(255), nullable=True)
    severity = Column(String(20), default=AllergySeverity.MILD.value)
    discovered_date = Column(Date, nullable=True)


class PatientDocument(TimestampMixin, Base):
    __tablename__ = "patient_documents"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    document_type = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class PatientVitals(TimestampMixin, Base):
    __tablename__ = "patient_vitals"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    visit_id = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    blood_pressure_sys = Column(Integer, nullable=True)
    blood_pressure_dia = Column(Integer, nullable=True)
    pulse_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class DigitalConsent(TimestampMixin, Base):
    __tablename__ = "digital_consents"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    consent_type = Column(String(100), nullable=False)
    is_signed = Column(Boolean, default=False)
    signed_at = Column(DateTime, nullable=True)
    signature_path = Column(String(255), nullable=True)
    witnessed_by = Column(String(255), nullable=True)
