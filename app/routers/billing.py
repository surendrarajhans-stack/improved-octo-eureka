from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.billing import InsuranceClaim, Invoice, InvoiceItem, Payment
from app.schemas.billing import (
    InsuranceClaimCreate,
    InsuranceClaimResponse,
    InsuranceClaimUpdate,
    InvoiceCreate,
    InvoiceItemCreate,
    InvoiceItemResponse,
    InvoiceResponse,
    InvoiceUpdate,
    PaymentCreate,
    PaymentResponse,
)
from app.services.billing_service import (
    create_invoice_from_opd,
    generate_invoice_number,
    process_payment,
)

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Invoice).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    invoice_number = await generate_invoice_number(db)
    invoice = Invoice(**data.model_dump(), invoice_number=invoice_number)
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(invoice, key, value)
    await db.flush()
    await db.refresh(invoice)
    return invoice


@router.post("/invoices/{invoice_id}/generate-from-opd", response_model=InvoiceResponse)
async def generate_from_opd(
    invoice_id: int,
    opd_visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    invoice = await create_invoice_from_opd(db, opd_visit_id)
    return invoice


@router.post("/invoices/{invoice_id}/pay", response_model=PaymentResponse)
async def pay_invoice(
    invoice_id: int,
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payment = await process_payment(
        db, invoice_id, data.amount, data.payment_method, data.notes or ""
    )
    return payment


@router.post("/invoice-items", response_model=InvoiceItemResponse, status_code=201)
async def create_invoice_item(
    data: InvoiceItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = InvoiceItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Payment).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payment = Payment(**data.model_dump())
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


@router.get("/insurance-claims", response_model=list[InsuranceClaimResponse])
async def list_insurance_claims(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(InsuranceClaim).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/insurance-claims",
    response_model=InsuranceClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_insurance_claim(
    data: InsuranceClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    claim = InsuranceClaim(**data.model_dump())
    db.add(claim)
    await db.flush()
    await db.refresh(claim)
    return claim


@router.put("/insurance-claims/{claim_id}", response_model=InsuranceClaimResponse)
async def update_insurance_claim(
    claim_id: int,
    data: InsuranceClaimUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(InsuranceClaim).where(InsuranceClaim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Insurance claim not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(claim, key, value)
    await db.flush()
    await db.refresh(claim)
    return claim
