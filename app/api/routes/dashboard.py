from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import render
from app.database import get_db
from app.models.appointment import Appointment
from app.models.billing import Payment
from app.models.clinical import EmergencyCase, IPDAdmission
from app.models.doctor import Doctor
from app.models.hospital import Bed, Department, Ward
from app.models.inventory import InventoryItem
from app.models.laboratory import LabOrder

router = APIRouter()


@router.get("/")
def index():
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    today = date.today()
    today_patients = db.query(func.count(Appointment.id)).filter(Appointment.appointment_date == today).scalar() or 0
    today_revenue = db.query(func.coalesce(func.sum(Payment.amount), 0.0)).filter(func.date(Payment.payment_date) == today).scalar() or 0.0
    total_appointments = today_patients
    current_admissions = db.query(func.count(IPDAdmission.id)).filter(IPDAdmission.status == "ADMITTED").scalar() or 0
    available_beds = db.query(func.count(Bed.id)).filter(Bed.status == "AVAILABLE").scalar() or 0
    emergency_cases = db.query(func.count(EmergencyCase.id)).filter(func.date(EmergencyCase.arrival_time) == today).scalar() or 0
    low_stock_items = db.query(InventoryItem).filter(InventoryItem.current_stock <= InventoryItem.reorder_level).limit(10).all()
    pending_lab_reports = db.query(func.count(LabOrder.id)).filter(LabOrder.status.in_(["ORDERED", "PROCESSING", "SAMPLE_COLLECTED"])).scalar() or 0
    doctor_availability = db.query(Doctor).order_by(Doctor.is_available.desc(), Doctor.id).limit(8).all()

    revenue_labels, revenue_data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        revenue_labels.append(day.strftime("%d %b"))
        revenue_data.append(float(db.query(func.coalesce(func.sum(Payment.amount), 0.0)).filter(func.date(Payment.payment_date) == day).scalar() or 0.0))

    patient_labels, patient_data = [], []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        patient_labels.append(day.strftime("%d %b"))
        patient_data.append(db.query(func.count(Appointment.id)).filter(Appointment.appointment_date == day).scalar() or 0)

    department_wise_patients = []
    for dept_name, count in db.query(Department.name, func.count(Appointment.id)).join(Appointment, Appointment.department_id == Department.id, isouter=True).group_by(Department.id).all():
        department_wise_patients.append({"label": dept_name, "value": count})

    ward_stats = []
    for ward in db.query(Ward).all():
        total = db.query(func.count(Bed.id)).filter(Bed.ward_id == ward.id).scalar() or 0
        occupied = db.query(func.count(Bed.id)).filter(Bed.ward_id == ward.id, Bed.status == "OCCUPIED").scalar() or 0
        ward_stats.append({"name": ward.name, "occupied": occupied, "total": total, "rate": round((occupied / total) * 100, 2) if total else 0})
    bed_occupancy_rate = round((sum(item['occupied'] for item in ward_stats) / sum(item['total'] for item in ward_stats)) * 100, 2) if sum(item['total'] for item in ward_stats) else 0

    return render(request, "dashboard.html", db, current_user,
        today_patients=today_patients, today_revenue=today_revenue, total_appointments=total_appointments,
        current_admissions=current_admissions, available_beds=available_beds, emergency_cases=emergency_cases,
        low_stock_items=low_stock_items, pending_lab_reports=pending_lab_reports, doctor_availability=doctor_availability,
        revenue_chart={"labels": revenue_labels, "data": revenue_data}, patient_chart={"labels": patient_labels, "data": patient_data},
        department_wise_patients=department_wise_patients, ward_stats=ward_stats, bed_occupancy_rate=bed_occupancy_rate)
