from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Invoice, InvoiceStatus, Payment
from app.models.opd import OPDVisit


async def generate_invoice_number(db: AsyncSession) -> str:
    year = datetime.now().year
    result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.invoice_number.like(f"INV-{year}-%")
        )
    )
    count = result.scalar() or 0
    return f"INV-{year}-{count + 1:04d}"


async def create_invoice_from_opd(db: AsyncSession, opd_visit_id: int) -> Invoice:
    result = await db.execute(select(OPDVisit).where(OPDVisit.id == opd_visit_id))
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="OPD visit not found")

    invoice_number = await generate_invoice_number(db)
    invoice = Invoice(
        invoice_number=invoice_number,
        patient_id=visit.patient_id,
        opd_visit_id=visit.id,
        total_amount=float(visit.visit_fee),
        paid_amount=0.0,
        discount=0.0,
        tax=0.0,
        status=InvoiceStatus.PENDING,
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def process_payment(
    db: AsyncSession, invoice_id: int, amount: float, payment_method: str, notes: str = ""
) -> Payment:
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot pay a cancelled invoice")

    payment = Payment(
        invoice_id=invoice_id,
        amount=amount,
        payment_method=payment_method,
        notes=notes,
    )
    db.add(payment)

    # Update invoice paid amount and status
    new_paid = float(invoice.paid_amount) + amount
    invoice.paid_amount = new_paid
    if new_paid >= float(invoice.total_amount):
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    await db.flush()
    await db.refresh(payment)
    return payment


async def get_revenue_report(
    db: AsyncSession, start_date: datetime, end_date: datetime
) -> dict:
    result = await db.execute(
        select(func.sum(Payment.amount), func.count(Payment.id)).where(
            Payment.payment_date.between(start_date, end_date)
        )
    )
    row = result.one()
    total_revenue = float(row[0] or 0)
    payment_count = int(row[1] or 0)

    # By method
    method_result = await db.execute(
        select(Payment.payment_method, func.sum(Payment.amount)).where(
            Payment.payment_date.between(start_date, end_date)
        ).group_by(Payment.payment_method)
    )
    by_method = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): float(row[1] or 0)
        for row in method_result.all()
    }

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_revenue": total_revenue,
        "payment_count": payment_count,
        "by_payment_method": by_method,
    }
