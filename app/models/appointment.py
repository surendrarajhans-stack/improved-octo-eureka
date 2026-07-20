from enum import Enum

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time

from app.database import Base
from app.models.base import TimestampMixin


class AppointmentType(str, Enum):
    OPD = "OPD"
    TELEMEDICINE = "TELEMEDICINE"
    EMERGENCY = "EMERGENCY"


class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class AppointmentPriority(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    slot_number = Column(Integer, default=1)
    token_number = Column(Integer, default=1)
    appointment_type = Column(String(20), default=AppointmentType.OPD.value)
    status = Column(String(20), default=AppointmentStatus.SCHEDULED.value)
    chief_complaint = Column(Text, nullable=True)
    priority = Column(String(20), default=AppointmentPriority.NORMAL.value)
    consultation_fee = Column(Float, default=0.0)
    payment_status = Column(String(20), default="PENDING")
    notes = Column(Text, nullable=True)
    booked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancelled_reason = Column(Text, nullable=True)


class AppointmentQueue(TimestampMixin, Base):
    __tablename__ = "appointment_queues"

    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    queue_position = Column(Integer, nullable=False)
    called_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    waiting_time_minutes = Column(Integer, nullable=True)
