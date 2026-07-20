from enum import Enum

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.database import Base
from app.models.base import TimestampMixin


class HospitalType(str, Enum):
    CLINIC = "CLINIC"
    HOSPITAL = "HOSPITAL"
    MEDICAL_COLLEGE = "MEDICAL_COLLEGE"


class WardType(str, Enum):
    GENERAL = "GENERAL"
    ICU = "ICU"
    NICU = "NICU"
    PICU = "PICU"
    PRIVATE = "PRIVATE"
    SEMI_PRIVATE = "SEMI_PRIVATE"


class BedStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
    RESERVED = "RESERVED"


class Hospital(TimestampMixin, Base):
    __tablename__ = "hospitals"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    logo = Column(String(255), nullable=True)
    registration_no = Column(String(100), nullable=True)
    accreditation = Column(String(100), nullable=True)
    bed_capacity = Column(Integer, default=0)
    type = Column(SAEnum(HospitalType), default=HospitalType.HOSPITAL)
    is_active = Column(Boolean, default=True)
    settings_json = Column(JSON, nullable=True)


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    head_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    floor = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class Ward(TimestampMixin, Base):
    __tablename__ = "wards"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    name = Column(String(255), nullable=False)
    ward_type = Column(SAEnum(WardType), default=WardType.GENERAL)
    total_beds = Column(Integer, default=0)
    floor = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)


class Bed(TimestampMixin, Base):
    __tablename__ = "beds"

    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    bed_number = Column(String(50), nullable=False)
    bed_type = Column(String(100), nullable=True)
    status = Column(SAEnum(BedStatus), default=BedStatus.AVAILABLE)
    current_patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
