from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.billing import InvoiceStatus, PaymentMethod


class InvoiceBase(BaseModel):
    patient_id: int
    admission_id: int | None = None
    opd_visit_id: int | None = None
    total_amount: float = 0.0
    paid_amount: float = 0.0
    discount: float = 0.0
    tax: float = 0.0
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: datetime | None = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    total_amount: float | None = None
    paid_amount: float | None = None
    discount: float | None = None
    tax: float | None = None
    status: InvoiceStatus | None = None
    due_date: datetime | None = None


class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_number: str
    created_at: datetime


class InvoiceItemBase(BaseModel):
    invoice_id: int
    description: str
    quantity: float = 1.0
    unit_price: float
    amount: float
    category: str | None = None


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemUpdate(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None
    category: str | None = None


class InvoiceItemResponse(InvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PaymentBase(BaseModel):
    invoice_id: int
    amount: float
    payment_method: PaymentMethod = PaymentMethod.CASH
    transaction_id: str | None = None
    notes: str | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payment_date: datetime


class InsuranceClaimBase(BaseModel):
    patient_id: int
    invoice_id: int
    insurance_provider: str
    claim_number: str | None = None
    claimed_amount: float
    approved_amount: float | None = None
    status: str = "SUBMITTED"


class InsuranceClaimCreate(InsuranceClaimBase):
    pass


class InsuranceClaimUpdate(BaseModel):
    claim_number: str | None = None
    approved_amount: float | None = None
    status: str | None = None
    approved_at: datetime | None = None


class InsuranceClaimResponse(InsuranceClaimBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    submitted_at: datetime
    approved_at: datetime | None = None
