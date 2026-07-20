from datetime import date, datetime

from pydantic import BaseModel


class InventoryItemCreate(BaseModel):
    hospital_id: int
    category_id: int | None = None
    name: str
    code: str
    unit: str | None = None
    reorder_level: int = 10
    current_stock: float = 0.0
    location: str | None = None
    description: str | None = None


class PurchaseOrderCreate(BaseModel):
    hospital_id: int
    supplier_id: int
    po_number: str
    order_date: date
    expected_delivery: date | None = None
    total_amount: float = 0.0
    notes: str | None = None


class GRNCreate(BaseModel):
    hospital_id: int
    po_id: int | None = None
    supplier_id: int | None = None
    grn_number: str
    received_date: date
    total_amount: float = 0.0
    notes: str | None = None


class StockTransferCreate(BaseModel):
    hospital_id: int
    from_department: str | None = None
    to_department: str | None = None
    transfer_date: datetime
    status: str = "PENDING"
    notes: str | None = None
