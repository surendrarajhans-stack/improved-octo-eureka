from datetime import date

from pydantic import BaseModel


class InsurancePolicyCreate(BaseModel):
    hospital_id: int
    patient_id: int | None = None
    policy_number: str
    policy_type: str | None = None
    insurer_name: str
    tpa_name: str | None = None
    coverage_amount: float = 0.0
    copay_percent: float = 0.0
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class InsuranceClaimCreate(BaseModel):
    hospital_id: int
    invoice_id: int
    policy_id: int
    patient_id: int
    claim_number: str
    diagnosis: str | None = None
    claimed_amount: float
    notes: str | None = None


class InsuranceClaimStatusUpdate(BaseModel):
    status: str
    approved_amount: float | None = None
    rejected_amount: float | None = None
    rejection_reason: str | None = None
