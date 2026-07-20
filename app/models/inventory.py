from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class InventoryCategory(TimestampMixin, Base):
    __tablename__ = "inventory_categories"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)


class InventoryItem(TimestampMixin, Base):
    __tablename__ = "inventory_items"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("inventory_categories.id"), nullable=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=True)
    reorder_level = Column(Integer, default=10)
    current_stock = Column(Float, default=0.0)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    gst_number = Column(String(100), nullable=True)
    payment_terms = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    po_number = Column(String(100), nullable=False)
    order_date = Column(Date, nullable=False)
    expected_delivery = Column(Date, nullable=True)
    total_amount = Column(Float, default=0.0)
    status = Column(String(20), default="DRAFT")
    notes = Column(Text, nullable=True)


class PurchaseOrderItem(TimestampMixin, Base):
    __tablename__ = "purchase_order_items"

    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity_ordered = Column(Float, default=0.0)
    quantity_received = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)


class GRN(TimestampMixin, Base):
    __tablename__ = "grns"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    grn_number = Column(String(100), nullable=False)
    received_date = Column(Date, nullable=False)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)


class GRNItem(TimestampMixin, Base):
    __tablename__ = "grn_items"

    grn_id = Column(Integer, ForeignKey("grns.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity_received = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(Date, nullable=True)
    total_price = Column(Float, default=0.0)


class StockTransfer(TimestampMixin, Base):
    __tablename__ = "stock_transfers"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    from_department = Column(String(255), nullable=True)
    to_department = Column(String(255), nullable=True)
    transfer_date = Column(DateTime, nullable=False)
    transferred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="PENDING")
    notes = Column(Text, nullable=True)


class StockTransferItem(TimestampMixin, Base):
    __tablename__ = "stock_transfer_items"

    transfer_id = Column(Integer, ForeignKey("stock_transfers.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
