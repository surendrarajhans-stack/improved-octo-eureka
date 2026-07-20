from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    visit_type = Column(String(20), nullable=False)
    visit_id = Column(Integer, nullable=True)
    subtotal = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    advance_paid = Column(Float, default=0.0)
    net_payable = Column(Float, default=0.0)
    status = Column(String(20), default="DRAFT")


class InvoiceItem(TimestampMixin, Base):
    __tablename__ = "invoice_items"

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    service_type = Column(String(100), nullable=False)
    service_id = Column(Integer, nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax_percent = Column(Float, default=0.0)
    total = Column(Float, default=0.0)


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_mode = Column(String(50), nullable=False)
    transaction_id = Column(String(100), nullable=True)
    payment_date = Column(DateTime, default=datetime.utcnow)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="SUCCESS")


class Refund(TimestampMixin, Base):
    __tablename__ = "refunds"

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    refund_date = Column(DateTime, default=datetime.utcnow)
    refunded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="PROCESSED")


class BillingRate(TimestampMixin, Base):
    __tablename__ = "billing_rates"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    service_type = Column(String(100), nullable=False)
    service_name = Column(String(255), nullable=False)
    price = Column(Float, default=0.0)
    tax_percent = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
