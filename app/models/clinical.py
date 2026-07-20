from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Time

from app.database import Base
from app.models.base import TimestampMixin


class PrescriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISPENSED = "DISPENSED"
    EXPIRED = "EXPIRED"


class AdmissionType(str, Enum):
    ELECTIVE = "ELECTIVE"
    EMERGENCY = "EMERGENCY"
    TRANSFER = "TRANSFER"


class AdmissionStatus(str, Enum):
    ADMITTED = "ADMITTED"
    DISCHARGED = "DISCHARGED"
    TRANSFERRED = "TRANSFERRED"
    ABSCONDED = "ABSCONDED"
    LAMA = "LAMA"
    EXPIRED = "EXPIRED"


class NoteType(str, Enum):
    NURSING = "NURSING"
    DOCTOR = "DOCTOR"
    OBSERVATION = "OBSERVATION"


class ArrivalMode(str, Enum):
    WALK_IN = "WALK_IN"
    AMBULANCE = "AMBULANCE"
    REFERRED = "REFERRED"


class Disposition(str, Enum):
    ADMITTED = "ADMITTED"
    DISCHARGED = "DISCHARGED"
    TRANSFERRED = "TRANSFERRED"
    EXPIRED = "EXPIRED"
    ABSCONDED = "ABSCONDED"


class OPDConsultation(TimestampMixin, Base):
    __tablename__ = "opd_consultations"

    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    visit_date = Column(Date, nullable=False)
    chief_complaint = Column(Text, nullable=True)
    history_of_present_illness = Column(Text, nullable=True)
    past_medical_history = Column(Text, nullable=True)
    examination_findings = Column(Text, nullable=True)
    diagnosis_primary = Column(String(255), nullable=True)
    diagnosis_secondary = Column(String(255), nullable=True)
    icd_code = Column(String(50), nullable=True)
    treatment_plan = Column(Text, nullable=True)
    advice = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    referral_to = Column(String(255), nullable=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    billing_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    status = Column(String(50), default="COMPLETED")


class Prescription(TimestampMixin, Base):
    __tablename__ = "prescriptions"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    consultation_id = Column(Integer, ForeignKey("opd_consultations.id"), nullable=True)
    prescribed_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    diagnosis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default=PrescriptionStatus.ACTIVE.value)


class PrescriptionItem(TimestampMixin, Base):
    __tablename__ = "prescription_items"

    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medicine_name = Column(String(255), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    duration = Column(String(100), nullable=True)
    quantity = Column(Integer, default=1)
    instructions = Column(Text, nullable=True)
    is_substitutable = Column(Boolean, default=True)


class IPDAdmission(TimestampMixin, Base):
    __tablename__ = "ipd_admissions"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)
    admission_date = Column(Date, nullable=False)
    admission_time = Column(Time, nullable=False)
    discharge_date = Column(Date, nullable=True)
    discharge_time = Column(Time, nullable=True)
    admission_type = Column(String(20), default=AdmissionType.ELECTIVE.value)
    primary_diagnosis = Column(String(255), nullable=True)
    secondary_diagnosis = Column(String(255), nullable=True)
    surgery_planned = Column(String(255), nullable=True)
    mlc_case = Column(Boolean, default=False)
    mlc_number = Column(String(100), nullable=True)
    attendant_name = Column(String(255), nullable=True)
    attendant_phone = Column(String(20), nullable=True)
    attendant_relation = Column(String(100), nullable=True)
    discharge_summary = Column(Text, nullable=True)
    status = Column(String(20), default=AdmissionStatus.ADMITTED.value)


class NursingNote(TimestampMixin, Base):
    __tablename__ = "nursing_notes"

    admission_id = Column(Integer, ForeignKey("ipd_admissions.id"), nullable=False)
    nurse_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note_text = Column(Text, nullable=False)
    note_type = Column(String(20), default=NoteType.NURSING.value)
    noted_at = Column(DateTime, default=datetime.utcnow)


class DailyProgress(TimestampMixin, Base):
    __tablename__ = "daily_progress"

    admission_id = Column(Integer, ForeignKey("ipd_admissions.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    progress_date = Column(Date, nullable=False)
    subjective = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    noted_at = Column(DateTime, default=datetime.utcnow)


class EmergencyCase(TimestampMixin, Base):
    __tablename__ = "emergency_cases"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    esi_level = Column(Integer, nullable=False)
    arrival_time = Column(DateTime, default=datetime.utcnow)
    arrival_mode = Column(String(20), default=ArrivalMode.WALK_IN.value)
    chief_complaint = Column(Text, nullable=False)
    is_mlc = Column(Boolean, default=False)
    mlc_number = Column(String(100), nullable=True)
    triage_notes = Column(Text, nullable=True)
    attending_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    disposition = Column(String(20), default=Disposition.ADMITTED.value)
    disposition_time = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
