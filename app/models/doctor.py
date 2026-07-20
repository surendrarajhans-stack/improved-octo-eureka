from enum import Enum

from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text, Time

from app.database import Base
from app.models.base import TimestampMixin


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Doctor(TimestampMixin, Base):
    __tablename__ = "doctors"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    employee_code = Column(String(50), unique=True, nullable=False)
    specialization = Column(String(255), nullable=False)
    qualification = Column(String(255), nullable=True)
    registration_no = Column(String(100), nullable=True)
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(Float, default=0.0)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_available = Column(Boolean, default=True)
    bio = Column(Text, nullable=True)
    languages_spoken = Column(String(255), nullable=True)
    schedule_json = Column(Text, nullable=True)


class DoctorSchedule(TimestampMixin, Base):
    __tablename__ = "doctor_schedules"

    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=15)
    max_appointments = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)


class DoctorLeave(TimestampMixin, Base):
    __tablename__ = "doctor_leaves"

    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    leave_type = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default=LeaveStatus.PENDING.value)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
