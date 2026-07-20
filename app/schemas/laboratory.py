from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LabTestBase(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    normal_range: str | None = None
    unit: str | None = None
    price: float
    turnaround_hours: int = 24


class LabTestCreate(LabTestBase):
    pass


class LabTestUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    normal_range: str | None = None
    unit: str | None = None
    price: float | None = None
    turnaround_hours: int | None = None


class LabTestResponse(LabTestBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LabOrderBase(BaseModel):
    patient_id: int
    doctor_id: int
    visit_id: int | None = None
    priority: str = "NORMAL"
    status: str = "PENDING"
    total_amount: float = 0.0


class LabOrderCreate(LabOrderBase):
    pass


class LabOrderUpdate(BaseModel):
    priority: str | None = None
    status: str | None = None
    total_amount: float | None = None


class LabOrderResponse(LabOrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_date: datetime


class LabOrderItemBase(BaseModel):
    order_id: int
    test_id: int
    status: str = "PENDING"


class LabOrderItemCreate(LabOrderItemBase):
    pass


class LabOrderItemUpdate(BaseModel):
    status: str | None = None
    collected_at: datetime | None = None
    processed_at: datetime | None = None


class LabOrderItemResponse(LabOrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    collected_at: datetime | None = None
    processed_at: datetime | None = None


class LabResultBase(BaseModel):
    order_item_id: int
    result_value: str | None = None
    unit: str | None = None
    normal_range: str | None = None
    is_abnormal: bool = False
    notes: str | None = None
    verified_by: int | None = None


class LabResultCreate(LabResultBase):
    pass


class LabResultUpdate(BaseModel):
    result_value: str | None = None
    unit: str | None = None
    normal_range: str | None = None
    is_abnormal: bool | None = None
    notes: str | None = None
    verified_by: int | None = None


class LabResultResponse(LabResultBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    result_date: datetime
