from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.inventory import ItemCategory


class InventoryItemBase(BaseModel):
    item_code: str
    name: str
    category: ItemCategory
    unit: str
    current_stock: float = 0.0
    reorder_level: float = 10.0
    unit_cost: float = 0.0
    supplier_name: str | None = None
    location: str | None = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: str | None = None
    category: ItemCategory | None = None
    unit: str | None = None
    current_stock: float | None = None
    reorder_level: float | None = None
    unit_cost: float | None = None
    supplier_name: str | None = None
    location: str | None = None


class InventoryItemResponse(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PurchaseOrderBase(BaseModel):
    supplier_name: str
    expected_delivery: datetime | None = None
    total_amount: float = 0.0
    status: str = "PENDING"
    notes: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrderUpdate(BaseModel):
    expected_delivery: datetime | None = None
    total_amount: float | None = None
    status: str | None = None
    approved_by: int | None = None
    notes: str | None = None


class PurchaseOrderResponse(PurchaseOrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    po_number: str
    order_date: datetime
    approved_by: int | None = None


class PurchaseOrderItemBase(BaseModel):
    po_id: int
    item_id: int
    quantity: float
    unit_price: float
    amount: float
    received_quantity: float = 0.0


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItemUpdate(BaseModel):
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None
    received_quantity: float | None = None


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StockMovementBase(BaseModel):
    item_id: int
    movement_type: str
    quantity: float
    reference_id: str | None = None
    notes: str | None = None
    moved_by: int | None = None


class StockMovementCreate(StockMovementBase):
    pass


class StockMovementResponse(StockMovementBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    moved_at: datetime
