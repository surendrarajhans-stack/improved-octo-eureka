from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import paginate, parse_request_data, redirect_with_message, render
from app.database import get_db
from app.models.appointment import Appointment, AppointmentQueue
from app.models.doctor import Doctor
from app.models.hospital import Department
from app.models.patient import Patient

router = APIRouter()


def _appointment_query(db: Session, search: str | None = None, status: str | None = None, doctor_id: int | None = None):
    query = db.query(Appointment).filter(Appointment.is_deleted.is_(False))
    if search:
        query = query.join(Patient, Patient.id == Appointment.patient_id).filter(Patient.first_name.ilike(f"%{search}%"))
    if status:
        query = query.filter(Appointment.status == status)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    return query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())


@router.get("")
def appointment_list(request: Request, page: int = 1, per_page: int = 20, search: str | None = None, status: str | None = None, doctor_id: int | None = None, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    items, total = paginate(_appointment_query(db, search, status, doctor_id), page, per_page)
    doctors = db.query(Doctor).all()
    return render(request, "appointments/list.html", db, current_user, appointments=items, total=total, page=page, per_page=per_page, doctors=doctors)


@router.get("/create")
def appointment_create_form(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patients = db.query(Patient).filter(Patient.is_deleted.is_(False)).all()
    doctors = db.query(Doctor).all()
    departments = db.query(Department).all()
    return render(request, "appointments/list.html", db, current_user, create_mode=True, patients=patients, doctors=doctors, departments=departments, appointments=[])


@router.get("/queue")
def appointment_queue(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    today = date.today()
    queue = db.query(Appointment).filter(Appointment.appointment_date == today).order_by(Appointment.doctor_id, Appointment.token_number).all()
    return render(request, "opd/queue.html", db, current_user, queue=queue)


@router.get("/calendar")
def appointment_calendar(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    appointments = db.query(Appointment).order_by(Appointment.appointment_date.desc()).limit(100).all()
    return render(request, "appointments/calendar.html", db, current_user, appointments=appointments)


@router.post("")
async def create_appointment(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    appointment_date = datetime.strptime(data["appointment_date"], "%Y-%m-%d").date()
    appointment_time = datetime.strptime(data["appointment_time"], "%H:%M").time()
    token_number = (db.query(func.max(Appointment.token_number)).filter(Appointment.appointment_date == appointment_date).scalar() or 0) + 1
    slot_number = (db.query(func.max(Appointment.slot_number)).filter(Appointment.doctor_id == int(data["doctor_id"]), Appointment.appointment_date == appointment_date).scalar() or 0) + 1
    doctor = db.query(Doctor).filter(Doctor.id == int(data["doctor_id"])).first()
    appointment = Appointment(
        hospital_id=int(data.get("hospital_id") or current_user.hospital_id or doctor.hospital_id or 1),
        patient_id=int(data["patient_id"]),
        doctor_id=int(data["doctor_id"]),
        department_id=int(data["department_id"]) if data.get("department_id") else doctor.department_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        slot_number=slot_number,
        token_number=token_number,
        appointment_type=data.get("appointment_type", "OPD"),
        status=data.get("status", "SCHEDULED"),
        chief_complaint=data.get("chief_complaint"),
        priority=data.get("priority", "NORMAL"),
        consultation_fee=float(data.get("consultation_fee") or doctor.consultation_fee or 0),
        notes=data.get("notes"),
        booked_by=current_user.id,
    )
    db.add(appointment)
    db.flush()
    db.add(AppointmentQueue(appointment_id=appointment.id, queue_position=token_number))
    db.commit()
    db.refresh(appointment)
    if "application/json" in request.headers.get("content-type", ""):
        return JSONResponse({"message": "Appointment created", "id": appointment.id, "token_number": appointment.token_number})
    return redirect_with_message(f"/appointments/{appointment.id}", "Appointment created")


@router.get("/{appointment_id}")
def appointment_detail(appointment_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    return render(request, "appointments/list.html", db, current_user, detail_mode=True, appointment=appointment, appointments=[appointment])


@router.put("/{appointment_id}/status")
async def update_appointment_status(appointment_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    data = await parse_request_data(request)
    appointment.status = data["status"]
    appointment.cancelled_reason = data.get("cancelled_reason")
    db.commit()
    return JSONResponse({"message": "Status updated", "status": appointment.status})
