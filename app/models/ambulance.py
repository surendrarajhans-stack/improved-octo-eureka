from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    registration_no = Column(String(50), nullable=False)
    vehicle_type = Column(String(50), nullable=False)
    model = Column(String(100), nullable=True)
    capacity = Column(Integer, default=1)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    gps_device_id = Column(String(100), nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    fitness_expiry = Column(Date, nullable=True)
    status = Column(String(30), default="AVAILABLE")
    last_location = Column(String(255), nullable=True)


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    license_number = Column(String(100), nullable=False)
    license_expiry = Column(Date, nullable=True)
    is_available = Column(Integer, default=1)
    address = Column(Text, nullable=True)


class AmbulanceTrip(TimestampMixin, Base):
    __tablename__ = "ambulance_trips"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    pickup_address = Column(Text, nullable=True)
    destination = Column(Text, nullable=True)
    trip_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    distance_km = Column(Float, default=0.0)
    fare = Column(Float, default=0.0)
    status = Column(String(30), default="REQUESTED")
    notes = Column(Text, nullable=True)


class VehicleMaintenance(TimestampMixin, Base):
    __tablename__ = "vehicle_maintenance"

    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    maintenance_date = Column(Date, nullable=False)
    maintenance_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cost = Column(Float, default=0.0)
    done_by = Column(String(255), nullable=True)
    next_due_date = Column(Date, nullable=True)
