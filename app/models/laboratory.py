from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LabTest(Base):
    __tablename__ = "lab_tests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    normal_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    turnaround_hours: Mapped[int] = mapped_column(default=24, nullable=False)


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    visit_id: Mapped[int | None] = mapped_column(ForeignKey("opd_visits.id"), nullable=True)
    order_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)

    patient = relationship("Patient", foreign_keys=[patient_id], lazy="noload")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="noload")
    items = relationship("LabOrderItem", back_populates="order", lazy="noload")


class LabOrderItem(Base):
    __tablename__ = "lab_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("lab_orders.id"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("lab_tests.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order = relationship("LabOrder", back_populates="items", lazy="noload")
    test = relationship("LabTest", foreign_keys=[test_id], lazy="noload")
    result = relationship("LabResult", back_populates="order_item", lazy="noload", uselist=False)


class LabResult(Base):
    __tablename__ = "lab_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("lab_order_items.id"), nullable=False
    )
    result_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    normal_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    result_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    order_item = relationship("LabOrderItem", back_populates="result", lazy="noload")
    verifier = relationship("User", foreign_keys=[verified_by], lazy="noload")
