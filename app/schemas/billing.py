from pydantic import BaseModel


class InvoiceItemInput(BaseModel):
    service_type: str
    description: str
    quantity: float = 1.0
    unit_price: float
    discount: float = 0.0
    tax_percent: float = 0.0


class InvoiceCreate(BaseModel):
    hospital_id: int
    patient_id: int
    visit_type: str
    visit_id: int | None = None
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    items: list[InvoiceItemInput]


class PaymentCreate(BaseModel):
    amount: float
    payment_mode: str
    transaction_id: str | None = None
    notes: str | None = None


class RefundCreate(BaseModel):
    amount: float
    reason: str | None = None
