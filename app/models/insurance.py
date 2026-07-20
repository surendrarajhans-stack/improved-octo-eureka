from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class InsurancePolicy(TimestampMixin, Base):
    __tablename__ = "insurance_policies"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    policy_number = Column(String(100), nullable=False)
    policy_type = Column(String(100), nullable=True)
    insurer_name = Column(String(255), nullable=False)
    tpa_name = Column(String(255), nullable=True)
    coverage_amount = Column(Float, default=0.0)
    copay_percent = Column(Float, default=0.0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class InsuranceClaim(TimestampMixin, Base):
    __tablename__ = "insurance_claims"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    claim_number = Column(String(100), nullable=False)
    admission_date = Column(Date, nullable=True)
    discharge_date = Column(Date, nullable=True)
    diagnosis = Column(String(255), nullable=True)
    claimed_amount = Column(Float, default=0.0)
    approved_amount = Column(Float, default=0.0)
    rejected_amount = Column(Float, default=0.0)
    status = Column(String(20), default="SUBMITTED")
    submission_date = Column(Date, nullable=True)
    settlement_date = Column(Date, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class TPA(TimestampMixin, Base):
    __tablename__ = "tpas"

    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    empanelled_services_json = Column(Text, nullable=True)
