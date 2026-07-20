from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import render
from app.database import get_db
from app.models.appointment import Appointment
from app.models.billing import Invoice, Payment
from app.models.doctor import Doctor
from app.models.hr import Employee
from app.models.inventory import InventoryItem
from app.models.patient import Patient
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    return render(request, "reports/dashboard.html", db, current_user)


@router.get("/daily")
def daily_report(report_date: str | None = None, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    target = date.fromisoformat(report_date) if report_date else date.today()
    return ReportService(db).daily_summary(current_user.hospital_id or 1, target)


@router.get("/patients")
def patient_report(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patients = db.query(Patient).filter(Patient.is_deleted.is_(False)).all()
    return [{"id": p.id, "uhid": p.uhid, "name": f"{p.first_name} {p.last_name}", "phone": p.phone} for p in patients]


@router.get("/doctors")
def doctor_performance(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()
    report = []
    for doctor in doctors:
        count = db.query(Appointment).filter(Appointment.doctor_id == doctor.id).count()
        report.append({"doctor_id": doctor.id, "specialization": doctor.specialization, "appointments": count})
    return report


@router.get("/financial")
def financial_summary(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    revenue = sum(p.amount for p in db.query(Payment).all())
    outstanding = sum(inv.net_payable - inv.advance_paid for inv in db.query(Invoice).all())
    return {"revenue": revenue, "outstanding": outstanding}


@router.get("/inventory")
def inventory_report(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    return [{"item": item.name, "stock": item.current_stock, "reorder_level": item.reorder_level} for item in db.query(InventoryItem).all()]


@router.get("/hr")
def hr_report(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    return [{"employee": f"{e.first_name} {e.last_name}", "designation": e.designation, "salary": e.salary} for e in db.query(Employee).all()]


@router.get("/export")
def export_report(kind: str = Query("patients"), format: str = Query("excel"), current_user=Depends(require_auth), db: Session = Depends(get_db)):
    service = ReportService(db)
    data = []
    columns = []
    if kind == "patients":
        data = [{"UHID": p.uhid, "Name": f"{p.first_name} {p.last_name}", "Phone": p.phone} for p in db.query(Patient).all()]
        columns = ["UHID", "Name", "Phone"]
    elif kind == "financial":
        data = [{"Invoice": i.invoice_number, "Total": i.total_amount, "Status": i.status} for i in db.query(Invoice).all()]
        columns = ["Invoice", "Total", "Status"]
    else:
        data = [{"Doctor": d.id, "Specialization": d.specialization} for d in db.query(Doctor).all()]
        columns = ["Doctor", "Specialization"]
    if format == "pdf":
        content = service.export_to_pdf(f"{kind.title()} Report", data, columns)
        media = "application/pdf"
        filename = f"{kind}.pdf"
    else:
        content = service.export_to_excel(data, columns, kind.title())
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{kind}.xlsx"
    return Response(content, media_type=media, headers={"Content-Disposition": f"attachment; filename={filename}"})
