from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class LabOrder(TimestampMixin, Base):
    __tablename__ = "lab_orders"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    visit_id = Column(Integer, nullable=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    sample_collection_date = Column(DateTime, nullable=True)
    sample_type = Column(String(100), nullable=True)
    priority = Column(String(20), default="ROUTINE")
    status = Column(String(20), default="ORDERED")
    notes = Column(Text, nullable=True)
    billing_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)


class LabTest(TimestampMixin, Base):
    __tablename__ = "lab_tests"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    test_name = Column(String(255), nullable=False)
    test_code = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)
    normal_range = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    price = Column(Integer, default=0)
    turnaround_hours = Column(Integer, default=24)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class LabOrderItem(TimestampMixin, Base):
    __tablename__ = "lab_order_items"

    order_id = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("lab_tests.id"), nullable=False)
    status = Column(String(20), default="PENDING")
    result_value = Column(String(255), nullable=True)
    result_text = Column(Text, nullable=True)
    is_abnormal = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class LabReport(TimestampMixin, Base):
    __tablename__ = "lab_reports"

    order_id = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    report_date = Column(DateTime, default=datetime.utcnow)
    interpretation = Column(Text, nullable=True)
    pathologist_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pdf_path = Column(String(255), nullable=True)
    is_emailed = Column(Boolean, default=False)
    is_printed = Column(Boolean, default=False)
