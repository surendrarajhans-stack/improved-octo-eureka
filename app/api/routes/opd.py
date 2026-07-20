from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.appointment import Appointment, AppointmentQueue
from app.models.clinical import OPDConsultation, Prescription, PrescriptionItem
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.services.report_service import ReportService

router = APIRouter(prefix="/opd")


@router.get("")
def opd_dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    today = date.today()
    queue = db.query(Appointment).filter(Appointment.appointment_date == today).order_by(Appointment.token_number).all()
    waiting = sum(1 for item in queue if item.status in {"SCHEDULED", "CONFIRMED", "WAITING"})
    in_progress = sum(1 for item in queue if item.status == "IN_PROGRESS")
    completed = sum(1 for item in queue if item.status == "COMPLETED")
    avg_wait = db.query(func.avg(AppointmentQueue.waiting_time_minutes)).scalar() or 0
    doctors = db.query(Doctor).all()
    return render(request, "opd/queue.html", db, current_user, queue=queue, waiting=waiting, in_progress=in_progress, completed=completed, avg_wait=round(avg_wait, 2), doctors=doctors)


@router.get("/queue")
def live_queue(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    today = date.today()
    queue = db.query(Appointment).filter(Appointment.appointment_date == today).order_by(Appointment.token_number).all()
    return [{"id": a.id, "token_number": a.token_number, "patient_id": a.patient_id, "doctor_id": a.doctor_id, "status": a.status} for a in queue]


@router.post("/queue/{appointment_id}/call")
def call_next(appointment_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    queue = db.query(AppointmentQueue).filter(AppointmentQueue.appointment_id == appointment_id).first()
    if not appointment or not queue:
        raise HTTPException(404, "Queue item not found")
    appointment.status = "IN_PROGRESS"
    queue.called_at = datetime.utcnow()
    queue.started_at = datetime.utcnow()
    db.commit()
    return JSONResponse({"message": "Patient called", "appointment_id": appointment_id})


@router.get("/consultation/{appointment_id}")
def consultation_form(appointment_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first() if appointment else None
    if not appointment or not patient:
        raise HTTPException(404, "Appointment not found")
    return render(request, "opd/consultation.html", db, current_user, appointment=appointment, patient=patient)


@router.post("/consultation")
async def save_consultation(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    consultation = OPDConsultation(
        appointment_id=int(data["appointment_id"]),
        patient_id=int(data["patient_id"]),
        doctor_id=int(data["doctor_id"]),
        visit_date=datetime.strptime(data.get("visit_date") or str(date.today()), "%Y-%m-%d").date(),
        chief_complaint=data.get("chief_complaint"),
        history_of_present_illness=data.get("history_of_present_illness"),
        past_medical_history=data.get("past_medical_history"),
        examination_findings=data.get("examination_findings"),
        diagnosis_primary=data.get("diagnosis_primary"),
        diagnosis_secondary=data.get("diagnosis_secondary"),
        icd_code=data.get("icd_code"),
        treatment_plan=data.get("treatment_plan"),
        advice=data.get("advice"),
        follow_up_date=datetime.strptime(data["follow_up_date"], "%Y-%m-%d").date() if data.get("follow_up_date") else None,
        referral_to=data.get("referral_to"),
    )
    db.add(consultation)
    db.flush()
    prescription = Prescription(patient_id=consultation.patient_id, doctor_id=consultation.doctor_id, consultation_id=consultation.id, prescribed_date=consultation.visit_date, valid_until=consultation.follow_up_date, diagnosis=consultation.diagnosis_primary, notes=consultation.advice)
    db.add(prescription)
    db.flush()
    items_payload = data.get("prescription_items")
    if isinstance(items_payload, str) and items_payload:
        import json
        parsed = json.loads(items_payload)
    else:
        parsed = []
        if data.get("medicine_name"):
            parsed.append({"medicine_name": data["medicine_name"], "dosage": data.get("dosage"), "frequency": data.get("frequency"), "duration": data.get("duration"), "quantity": int(data.get("quantity") or 1), "instructions": data.get("instructions")})
    for item in parsed:
        db.add(PrescriptionItem(prescription_id=prescription.id, **item))
    consultation.prescription_id = prescription.id
    appointment = db.query(Appointment).filter(Appointment.id == consultation.appointment_id).first()
    appointment.status = "COMPLETED"
    db.commit()
    return JSONResponse({"message": "Consultation saved", "consultation_id": consultation.id, "prescription_id": prescription.id})


@router.get("/prescription/{prescription_id}")
def prescription_view(prescription_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    report_service = ReportService(db)
    pdf = report_service.generate_prescription_pdf(prescription_id)
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=prescription-{prescription_id}.pdf"})
