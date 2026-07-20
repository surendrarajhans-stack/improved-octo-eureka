from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="Tablet", nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reorder_level: Mapped[int] = mapped_column(default=10, nullable=False)
    current_stock: Mapped[int] = mapped_column(default=0, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    stock_movements = relationship("MedicineStock", back_populates="medicine", lazy="noload")


class PharmacyOrder(Base):
    __tablename__ = "pharmacy_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    visit_id: Mapped[int | None] = mapped_column(ForeignKey("opd_visits.id"), nullable=True)
    order_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    dispensed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id], lazy="noload")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="noload")
    items = relationship("PharmacyOrderItem", back_populates="order", lazy="noload")
    dispenser = relationship("User", foreign_keys=[dispensed_by], lazy="noload")


class PharmacyOrderItem(Base):
    __tablename__ = "pharmacy_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("pharmacy_orders.id"), nullable=False)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    order = relationship("PharmacyOrder", back_populates="items", lazy="noload")
    medicine = relationship("Medicine", foreign_keys=[medicine_id], lazy="noload")


class MedicineStock(Base):
    __tablename__ = "medicine_stocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"), nullable=False)
    quantity_added: Mapped[int] = mapped_column(default=0, nullable=False)
    quantity_used: Mapped[int] = mapped_column(default=0, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    medicine = relationship("Medicine", back_populates="stock_movements", lazy="noload")
