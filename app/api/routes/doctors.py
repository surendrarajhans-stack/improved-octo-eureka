from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import paginate, parse_request_data, redirect_with_message, render
from app.core.permissions import UserRole
from app.core.security import get_password_hash
from app.database import get_db
from app.models.appointment import Appointment
from app.models.clinical import Prescription
from app.models.doctor import Doctor, DoctorSchedule
from app.models.hospital import Department
from app.models.user import User

router = APIRouter()


@router.get("")
def doctor_list(request: Request, page: int = 1, per_page: int = 20, department_id: int | None = None, specialization: str | None = None, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    query = db.query(Doctor).filter(Doctor.is_deleted.is_(False))
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    doctors, total = paginate(query.order_by(Doctor.id.desc()), page, per_page)
    departments = db.query(Department).all()
    return render(request, "doctors/list.html", db, current_user, doctors=doctors, departments=departments, total=total, page=page, per_page=per_page)


@router.get("/create")
def doctor_create_form(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    users = db.query(User).filter(User.role == UserRole.DOCTOR).all()
    return render(request, "doctors/list.html", db, current_user, create_mode=True, departments=departments, users=users, doctors=[])


@router.post("")
async def create_doctor(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    user_id = data.get("user_id")
    if not user_id:
        username = data.get("username") or f"doctor{int(datetime.utcnow().timestamp())}"
        user = User(
            hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1),
            username=username,
            email=data.get("email") or f"{username}@hospital.local",
            password_hash=get_password_hash(data.get("password") or "doctor123"),
            full_name=data.get("full_name") or username.title(),
            phone=data.get("phone"),
            role=UserRole.DOCTOR,
        )
        db.add(user)
        db.flush()
        user_id = user.id
    doctor = Doctor(
        user_id=int(user_id),
        hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1),
        employee_code=data["employee_code"],
        specialization=data["specialization"],
        qualification=data.get("qualification"),
        registration_no=data.get("registration_no"),
        experience_years=int(data.get("experience_years") or 0),
        consultation_fee=float(data.get("consultation_fee") or 0),
        department_id=int(data["department_id"]) if data.get("department_id") else None,
        is_available=str(data.get("is_available", "true")).lower() in {"true", "1", "yes", "on"},
        bio=data.get("bio"),
        languages_spoken=data.get("languages_spoken"),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return redirect_with_message(f"/doctors/{doctor.id}", "Doctor created")


@router.get("/{doctor_id}")
def doctor_detail(doctor_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    schedules = db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == doctor_id).order_by(DoctorSchedule.day_of_week).all()
    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).order_by(Appointment.appointment_date.desc()).limit(10).all()
    return render(request, "doctors/detail.html", db, current_user, doctor=doctor, schedules=schedules, appointments=appointments)


@router.get("/{doctor_id}/appointments")
def doctor_appointments(doctor_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).order_by(Appointment.appointment_date.desc()).all()
    return [{"id": a.id, "date": str(a.appointment_date), "status": a.status, "patient_id": a.patient_id} for a in appointments]


@router.put("/{doctor_id}")
async def update_doctor(doctor_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    data = await parse_request_data(request)
    for field in ["specialization", "qualification", "registration_no", "bio", "languages_spoken"]:
        if field in data:
            setattr(doctor, field, data[field])
    if data.get("consultation_fee"):
        doctor.consultation_fee = float(data["consultation_fee"])
    if data.get("department_id"):
        doctor.department_id = int(data["department_id"])
    if "is_available" in data:
        doctor.is_available = str(data["is_available"]).lower() in {"true", "1", "yes", "on"}
    db.commit()
    return JSONResponse({"message": "Doctor updated"})


@router.get("/{doctor_id}/availability")
def doctor_availability(doctor_id: int, date: str | None = None, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    schedules = db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == doctor_id, DoctorSchedule.is_active.is_(True)).all()
    return {"doctor_id": doctor_id, "available": doctor.is_available if doctor else False, "schedules": [{"day_of_week": s.day_of_week, "start_time": str(s.start_time), "end_time": str(s.end_time)} for s in schedules], "date": date}


@router.post("/{doctor_id}/schedule")
async def update_schedule(doctor_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    schedule = DoctorSchedule(
        doctor_id=doctor_id,
        day_of_week=int(data["day_of_week"]),
        start_time=datetime.strptime(data["start_time"], "%H:%M").time(),
        end_time=datetime.strptime(data["end_time"], "%H:%M").time(),
        slot_duration_minutes=int(data.get("slot_duration_minutes") or 15),
        max_appointments=int(data.get("max_appointments") or 20),
    )
    db.add(schedule)
    db.commit()
    return JSONResponse({"message": "Schedule saved", "id": schedule.id})


@router.get("/{doctor_id}/prescriptions")
def doctor_prescriptions(doctor_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    prescriptions = db.query(Prescription).filter(Prescription.doctor_id == doctor_id).all()
    return [{"id": p.id, "patient_id": p.patient_id, "date": str(p.prescribed_date), "status": p.status} for p in prescriptions]
