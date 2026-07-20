from datetime import date
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.billing import Invoice, InvoiceItem, Payment
from app.models.clinical import EmergencyCase, IPDAdmission, Prescription, PrescriptionItem
from app.models.hospital import Hospital
from app.models.laboratory import LabOrderItem, LabReport


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def daily_summary(self, hospital_id: int, date: date) -> dict:
        patients_seen = self.db.query(func.count(Appointment.id)).filter(Appointment.hospital_id == hospital_id, Appointment.appointment_date == date).scalar() or 0
        revenue = self.db.query(func.coalesce(func.sum(Payment.amount), 0.0)).join(Invoice, Invoice.id == Payment.invoice_id).filter(Invoice.hospital_id == hospital_id, func.date(Payment.payment_date) == date).scalar() or 0.0
        admissions = self.db.query(func.count(IPDAdmission.id)).filter(IPDAdmission.hospital_id == hospital_id, IPDAdmission.admission_date == date).scalar() or 0
        discharges = self.db.query(func.count(IPDAdmission.id)).filter(IPDAdmission.hospital_id == hospital_id, IPDAdmission.discharge_date == date).scalar() or 0
        emergency_cases = self.db.query(func.count(EmergencyCase.id)).filter(EmergencyCase.hospital_id == hospital_id, func.date(EmergencyCase.arrival_time) == date).scalar() or 0
        return {"date": str(date), "patients_seen": patients_seen, "revenue": revenue, "admissions": admissions, "discharges": discharges, "emergency_cases": emergency_cases}

    def export_to_excel(self, data: list[dict], columns: list[str], sheet_name: str) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = sheet_name
        sheet.append(columns)
        for row in data:
            sheet.append([row.get(column) for column in columns])
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()

    def export_to_pdf(self, title: str, data: list[dict], columns: list[str]) -> bytes:
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        table_data = [columns] + [[str(row.get(column, "")) for column in columns] for row in data]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        doc.build([Paragraph(title, styles["Title"]), Spacer(1, 12), table])
        return output.getvalue()

    def generate_prescription_pdf(self, prescription_id: int) -> bytes:
        prescription = self.db.query(Prescription).filter(Prescription.id == prescription_id).first()
        items = self.db.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == prescription_id).all()
        hospital = self.db.query(Hospital).first()
        data = [{"Medicine": item.medicine_name, "Dosage": item.dosage, "Frequency": item.frequency, "Duration": item.duration} for item in items]
        return self.export_to_pdf(f"{hospital.name if hospital else 'Hospital'} Prescription #{prescription.id}", data, ["Medicine", "Dosage", "Frequency", "Duration"])

    def generate_discharge_summary_pdf(self, admission_id: int) -> bytes:
        admission = self.db.query(IPDAdmission).filter(IPDAdmission.id == admission_id).first()
        data = [{"Field": "Primary Diagnosis", "Value": admission.primary_diagnosis}, {"Field": "Summary", "Value": admission.discharge_summary or "-"}]
        return self.export_to_pdf(f"Discharge Summary #{admission.id}", data, ["Field", "Value"])

    def generate_lab_report_pdf(self, report_id: int) -> bytes:
        report = self.db.query(LabReport).filter(LabReport.id == report_id).first()
        items = self.db.query(LabOrderItem).filter(LabOrderItem.order_id == report.order_id).all()
        data = [{"Test": item.id, "Result": item.result_value or item.result_text or "Pending", "Flag": "Abnormal" if item.is_abnormal else "Normal"} for item in items]
        return self.export_to_pdf(f"Lab Report #{report.id}", data, ["Test", "Result", "Flag"])

    def generate_bill_pdf(self, invoice_id: int) -> bytes:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        items = self.db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
        data = [{"Description": item.description, "Qty": item.quantity, "Amount": item.total} for item in items]
        return self.export_to_pdf(f"Invoice {invoice.invoice_number}", data, ["Description", "Qty", "Amount"])
