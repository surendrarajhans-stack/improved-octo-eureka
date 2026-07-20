from datetime import date, time

from pydantic import BaseModel


class PrescriptionItemInput(BaseModel):
    medicine_name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    quantity: int = 1
    instructions: str | None = None


class OPDConsultationCreate(BaseModel):
    appointment_id: int
    patient_id: int
    doctor_id: int
    visit_date: date
    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: str | None = None
    examination_findings: str | None = None
    diagnosis_primary: str | None = None
    diagnosis_secondary: str | None = None
    icd_code: str | None = None
    treatment_plan: str | None = None
    advice: str | None = None
    follow_up_date: date | None = None
    referral_to: str | None = None
    prescription_items: list[PrescriptionItemInput] = []


class IPDAdmissionCreate(BaseModel):
    hospital_id: int
    patient_id: int
    doctor_id: int
    department_id: int | None = None
    ward_id: int | None = None
    bed_id: int | None = None
    admission_date: date
    admission_time: time
    admission_type: str = "ELECTIVE"
    primary_diagnosis: str | None = None
    attendant_name: str | None = None
    attendant_phone: str | None = None
    attendant_relation: str | None = None


class NursingNoteCreate(BaseModel):
    note_text: str
    note_type: str = "NURSING"


class DailyProgressCreate(BaseModel):
    progress_date: date
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
