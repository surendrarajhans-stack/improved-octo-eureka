import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WardType(str, enum.Enum):
    GENERAL = "GENERAL"
    SEMI_PRIVATE = "SEMI_PRIVATE"
    PRIVATE = "PRIVATE"
    ICU = "ICU"
    NICU = "NICU"
    EMERGENCY = "EMERGENCY"


class BedStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
    RESERVED = "RESERVED"


class Ward(Base):
    __tablename__ = "wards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ward_type: Mapped[WardType] = mapped_column(Enum(WardType), nullable=False)
    floor: Mapped[int] = mapped_column(nullable=False, default=1)
    capacity: Mapped[int] = mapped_column(nullable=False, default=10)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    beds = relationship("Bed", back_populates="ward", lazy="noload")


class Bed(Base):
    __tablename__ = "beds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bed_number: Mapped[str] = mapped_column(String(20), nullable=False)
    ward_id: Mapped[int] = mapped_column(ForeignKey("wards.id"), nullable=False)
    status: Mapped[BedStatus] = mapped_column(
        Enum(BedStatus), default=BedStatus.AVAILABLE, nullable=False
    )
    features: Mapped[str | None] = mapped_column(Text, nullable=True)

    ward = relationship("Ward", back_populates="beds", lazy="noload")


class Admission(Base):
    __tablename__ = "admissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), nullable=False)
    admission_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    expected_discharge: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_discharge: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    discharge_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_discharged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    patient = relationship("Patient", foreign_keys=[patient_id], lazy="noload")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="noload")
    bed = relationship("Bed", foreign_keys=[bed_id], lazy="noload")
    daily_rounds = relationship("DailyRound", back_populates="admission", lazy="noload")


class DailyRound(Base):
    __tablename__ = "daily_rounds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    admission_id: Mapped[int] = mapped_column(ForeignKey("admissions.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    vitals_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    round_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    admission = relationship("Admission", back_populates="daily_rounds", lazy="noload")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], lazy="noload")
