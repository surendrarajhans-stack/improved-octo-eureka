from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class RadiologyOrder(TimestampMixin, Base):
    __tablename__ = "radiology_orders"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    study_type = Column(String(20), nullable=False)
    body_part = Column(String(100), nullable=True)
    clinical_history = Column(Text, nullable=True)
    priority = Column(String(20), default="ROUTINE")
    status = Column(String(20), default="ORDERED")
    scheduled_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    billing_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)


class RadiologyReport(TimestampMixin, Base):
    __tablename__ = "radiology_reports"

    order_id = Column(Integer, ForeignKey("radiology_orders.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    radiologist_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    report_date = Column(DateTime, default=datetime.utcnow)
    findings = Column(Text, nullable=True)
    impression = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    image_paths_json = Column(Text, nullable=True)
    pdf_path = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
