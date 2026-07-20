from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.billing import Invoice, InvoiceItem, Payment
from app.models.doctor import Doctor
from app.models.insurance import InsurancePolicy


class BillingService:
    def __init__(self, db: Session):
        self.db = db

    def generate_invoice_number(self, hospital_id: int) -> str:
        count = self.db.query(Invoice).filter(Invoice.hospital_id == hospital_id).count()
        return f"INV-{date.today().year}-{count + 1:05d}"

    def create_opd_invoice(self, patient_id: int, doctor_id: int, items: list) -> Invoice:
        doctor = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        hospital_id = doctor.hospital_id if doctor else 1
        invoice = Invoice(
            hospital_id=hospital_id,
            patient_id=patient_id,
            invoice_number=self.generate_invoice_number(hospital_id),
            visit_type="OPD",
            status="PENDING",
        )
        self.db.add(invoice)
        self.db.flush()
        subtotal = 0.0
        for item in items:
            total = float(item.get("quantity", 1)) * float(item.get("unit_price", 0))
            subtotal += total
            self.db.add(InvoiceItem(invoice_id=invoice.id, total=total, **item))
        invoice.subtotal = subtotal
        invoice.total_amount = subtotal
        invoice.net_payable = subtotal
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def calculate_insurance_claim(self, invoice_id: int, policy_id: int) -> dict:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        policy = self.db.query(InsurancePolicy).filter(InsurancePolicy.id == policy_id).first()
        if not invoice or not policy:
            return {"eligible": False, "approved_amount": 0.0}
        copay = invoice.net_payable * (policy.copay_percent / 100)
        approved = min(policy.coverage_amount, max(invoice.net_payable - copay, 0.0))
        return {"eligible": True, "approved_amount": round(approved, 2), "copay": round(copay, 2)}

    def process_payment(self, invoice_id: int, amount: float, mode: str) -> Payment:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        payment = Payment(invoice_id=invoice_id, patient_id=invoice.patient_id, amount=amount, payment_mode=mode, status="SUCCESS")
        self.db.add(payment)
        invoice.advance_paid += amount
        invoice.status = "PAID" if invoice.advance_paid >= invoice.net_payable else "PARTIAL"
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def apply_discount(self, invoice_id: int, discount: float, reason: str):
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.discount_amount = discount
        invoice.net_payable = max(invoice.total_amount - discount, 0.0)
        self.db.commit()
        return {"invoice_id": invoice_id, "discount": discount, "reason": reason}

    def generate_receipt_pdf(self, payment_id: int) -> bytes:
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, 800, "Payment Receipt")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, 770, f"Receipt ID: {payment.id}")
        pdf.drawString(50, 750, f"Invoice ID: {payment.invoice_id}")
        pdf.drawString(50, 730, f"Amount: {payment.amount:.2f}")
        pdf.drawString(50, 710, f"Mode: {payment.payment_mode}")
        pdf.drawString(50, 690, f"Date: {payment.payment_date}")
        pdf.showPage()
        pdf.save()
        return buffer.getvalue()
