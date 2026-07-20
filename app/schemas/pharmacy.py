from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MedicineBase(BaseModel):
    name: str
    generic_name: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    unit: str = "Tablet"
    unit_price: float
    reorder_level: int = 10
    current_stock: int = 0
    is_available: bool = True


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: str | None = None
    generic_name: str | None = None
    category: str | None = None
    unit_price: float | None = None
    reorder_level: int | None = None
    current_stock: int | None = None
    is_available: bool | None = None


class MedicineResponse(MedicineBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PharmacyOrderBase(BaseModel):
    patient_id: int
    doctor_id: int
    visit_id: int | None = None
    total_amount: float = 0.0
    status: str = "PENDING"


class PharmacyOrderCreate(PharmacyOrderBase):
    pass


class PharmacyOrderUpdate(BaseModel):
    total_amount: float | None = None
    status: str | None = None
    dispensed_by: int | None = None


class PharmacyOrderResponse(PharmacyOrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_date: datetime
    dispensed_by: int | None = None


class PharmacyOrderItemBase(BaseModel):
    order_id: int
    medicine_id: int
    quantity: int
    unit_price: float
    amount: float
    instructions: str | None = None


class PharmacyOrderItemCreate(PharmacyOrderItemBase):
    pass


class PharmacyOrderItemResponse(PharmacyOrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MedicineStockBase(BaseModel):
    medicine_id: int
    quantity_added: int = 0
    quantity_used: int = 0
    transaction_type: str
    reference_id: str | None = None


class MedicineStockCreate(MedicineStockBase):
    pass


class MedicineStockResponse(MedicineStockBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_date: datetime
