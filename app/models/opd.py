from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OPDVisit(Base):
    __tablename__ = "opd_visits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id"), nullable=True
    )
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    visit_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescription_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    visit_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    patient = relationship("Patient", foreign_keys=[patient_id], lazy="noload")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="noload")
    appointment = relationship("Appointment", foreign_keys=[appointment_id], lazy="noload")
    prescriptions = relationship("Prescription", back_populates="visit", lazy="noload")
    vitals = relationship("VitalSigns", back_populates="visit", lazy="noload")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("opd_visits.id"), nullable=False)
    medicine_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    visit = relationship("OPDVisit", back_populates="prescriptions", lazy="noload")


class VitalSigns(Base):
    __tablename__ = "vital_signs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("opd_visits.id"), nullable=False)
    blood_pressure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pulse: Mapped[int | None] = mapped_column(nullable=True)
    temperature: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    weight: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    height: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    oxygen_saturation: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    visit = relationship("OPDVisit", back_populates="vitals", lazy="noload")
