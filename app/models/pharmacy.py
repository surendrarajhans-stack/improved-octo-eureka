from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class Medicine(TimestampMixin, Base):
    __tablename__ = "medicines"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    form = Column(String(50), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    reorder_level = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    storage_conditions = Column(Text, nullable=True)
    is_controlled_substance = Column(Boolean, default=False)


class MedicineBatch(TimestampMixin, Base):
    __tablename__ = "medicine_batches"

    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    batch_number = Column(String(100), nullable=False)
    expiry_date = Column(Date, nullable=True)
    manufacture_date = Column(Date, nullable=True)
    purchase_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    quantity_purchased = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    grn_id = Column(Integer, ForeignKey("grns.id"), nullable=True)


class PharmacyDispensing(TimestampMixin, Base):
    __tablename__ = "pharmacy_dispensings"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    dispensed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    dispensed_at = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    payment_mode = Column(String(50), default="CASH")
    payment_status = Column(String(20), default="PENDING")
    notes = Column(Text, nullable=True)


class PharmacyDispensingItem(TimestampMixin, Base):
    __tablename__ = "pharmacy_dispensing_items"

    dispensing_id = Column(Integer, ForeignKey("pharmacy_dispensings.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id"), nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    instructions = Column(Text, nullable=True)


class DrugInteraction(TimestampMixin, Base):
    __tablename__ = "drug_interactions"

    medicine1_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    medicine2_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    clinical_effect = Column(Text, nullable=True)
