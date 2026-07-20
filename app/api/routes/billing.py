from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.billing import BillingRate, Invoice, InvoiceItem, Payment, Refund
from app.models.patient import Patient
from app.services.billing_service import BillingService
from app.services.report_service import ReportService

router = APIRouter(prefix="/billing")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.invoice_date.desc()).limit(20).all()
    return render(request, "billing/invoices.html", db, current_user, invoices=invoices)


@router.get("/invoices")
def invoices(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
    return render(request, "billing/invoices.html", db, current_user, invoices=invoices)


@router.get("/create")
def create_form(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    rates = db.query(BillingRate).filter(BillingRate.is_active == 1).all()
    return render(request, "billing/create.html", db, current_user, patients=patients, rates=rates)


@router.post("/invoices")
async def create_invoice(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    import json
    items_payload = data.get("items")
    items = json.loads(items_payload) if isinstance(items_payload, str) else items_payload
    service = BillingService(db)
    hospital_id = int(data.get("hospital_id") or current_user.hospital_id or 1)
    invoice = Invoice(hospital_id=hospital_id, patient_id=int(data["patient_id"]), invoice_number=service.generate_invoice_number(hospital_id), visit_type=data.get("visit_type", "OPD"), visit_id=int(data["visit_id"]) if data.get("visit_id") else None, status="PENDING")
    db.add(invoice)
    db.flush()
    subtotal = 0.0
    for item in items:
        quantity = float(item.get("quantity") or 1)
        unit_price = float(item.get("unit_price") or 0)
        discount = float(item.get("discount") or 0)
        tax_percent = float(item.get("tax_percent") or 0)
        total = quantity * unit_price
        total_after_discount = total - discount
        total_with_tax = total_after_discount + (total_after_discount * tax_percent / 100)
        subtotal += total
        db.add(InvoiceItem(invoice_id=invoice.id, service_type=item.get("service_type", "GENERAL"), description=item["description"], quantity=quantity, unit_price=unit_price, discount=discount, tax_percent=tax_percent, total=round(total_with_tax, 2)))
    invoice.subtotal = round(subtotal, 2)
    invoice.discount_amount = float(data.get("discount_amount") or 0)
    invoice.tax_amount = float(data.get("tax_amount") or 0)
    invoice.total_amount = round(subtotal - invoice.discount_amount + invoice.tax_amount, 2)
    invoice.net_payable = invoice.total_amount
    db.commit()
    db.refresh(invoice)
    return JSONResponse({"message": "Invoice created", "id": invoice.id, "invoice_number": invoice.invoice_number})


@router.get("/invoices/{invoice_id}")
def invoice_detail(invoice_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
    payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return render(request, "billing/invoices.html", db, current_user, detail_mode=True, invoice=invoice, items=items, payments=payments, invoices=[invoice])


@router.post("/invoices/{invoice_id}/payment")
async def record_payment(invoice_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    payment = BillingService(db).process_payment(invoice_id, float(data["amount"]), data.get("payment_mode", "CASH"))
    payment.transaction_id = data.get("transaction_id")
    payment.notes = data.get("notes")
    db.commit()
    return JSONResponse({"message": "Payment recorded", "payment_id": payment.id})


@router.post("/invoices/{invoice_id}/refund")
async def process_refund(invoice_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    refund = Refund(invoice_id=invoice_id, payment_id=int(data["payment_id"]) if data.get("payment_id") else None, amount=float(data["amount"]), reason=data.get("reason"), refunded_by=current_user.id, status="PROCESSED")
    db.add(refund)
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    invoice.status = "REFUNDED"
    db.commit()
    return JSONResponse({"message": "Refund processed", "refund_id": refund.id})


@router.get("/invoices/{invoice_id}/print")
def printable_invoice(invoice_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    pdf = ReportService(db).generate_bill_pdf(invoice_id)
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=invoice-{invoice_id}.pdf"})


@router.get("/rates")
def billing_rates(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    rates = db.query(BillingRate).all()
    return render(request, "billing/invoices.html", db, current_user, rates=rates, rates_mode=True, invoices=[])
