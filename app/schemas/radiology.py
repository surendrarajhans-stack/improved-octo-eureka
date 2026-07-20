from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RadiologyTestBase(BaseModel):
    name: str
    description: str | None = None
    modality: str
    body_part: str | None = None
    price: float
    preparation_instructions: str | None = None


class RadiologyTestCreate(RadiologyTestBase):
    pass


class RadiologyTestUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    modality: str | None = None
    body_part: str | None = None
    price: float | None = None
    preparation_instructions: str | None = None


class RadiologyTestResponse(RadiologyTestBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RadiologyOrderBase(BaseModel):
    patient_id: int
    doctor_id: int
    visit_id: int | None = None
    clinical_notes: str | None = None
    priority: str = "NORMAL"
    status: str = "PENDING"
    total_amount: float = 0.0


class RadiologyOrderCreate(RadiologyOrderBase):
    pass


class RadiologyOrderUpdate(BaseModel):
    clinical_notes: str | None = None
    priority: str | None = None
    status: str | None = None
    total_amount: float | None = None


class RadiologyOrderResponse(RadiologyOrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_date: datetime


class RadiologyOrderItemBase(BaseModel):
    order_id: int
    test_id: int
    status: str = "PENDING"


class RadiologyOrderItemCreate(RadiologyOrderItemBase):
    pass


class RadiologyOrderItemUpdate(BaseModel):
    status: str | None = None
    scheduled_at: datetime | None = None
    performed_at: datetime | None = None


class RadiologyOrderItemResponse(RadiologyOrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    scheduled_at: datetime | None = None
    performed_at: datetime | None = None


class RadiologyResultBase(BaseModel):
    order_item_id: int
    findings: str | None = None
    impression: str | None = None
    recommendations: str | None = None
    performed_by: int | None = None
    reported_by: int | None = None
    image_url: str | None = None


class RadiologyResultCreate(RadiologyResultBase):
    pass


class RadiologyResultUpdate(BaseModel):
    findings: str | None = None
    impression: str | None = None
    recommendations: str | None = None
    performed_by: int | None = None
    reported_by: int | None = None
    image_url: str | None = None


class RadiologyResultResponse(RadiologyResultBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    result_date: datetime
