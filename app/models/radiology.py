from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RadiologyTest(Base):
    __tablename__ = "radiology_tests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    modality: Mapped[str] = mapped_column(String(50), nullable=False)
    body_part: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    preparation_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)


class RadiologyOrder(Base):
    __tablename__ = "radiology_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    visit_id: Mapped[int | None] = mapped_column(ForeignKey("opd_visits.id"), nullable=True)
    order_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)

    patient = relationship("Patient", foreign_keys=[patient_id], lazy="noload")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="noload")
    items = relationship("RadiologyOrderItem", back_populates="order", lazy="noload")


class RadiologyOrderItem(Base):
    __tablename__ = "radiology_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("radiology_orders.id"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("radiology_tests.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order = relationship("RadiologyOrder", back_populates="items", lazy="noload")
    test = relationship("RadiologyTest", foreign_keys=[test_id], lazy="noload")
    result = relationship(
        "RadiologyResult", back_populates="order_item", lazy="noload", uselist=False
    )


class RadiologyResult(Base):
    __tablename__ = "radiology_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("radiology_order_items.id"), nullable=False
    )
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    impression: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reported_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    result_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order_item = relationship("RadiologyOrderItem", back_populates="result", lazy="noload")
