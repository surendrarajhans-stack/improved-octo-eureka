from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.clinical import DailyProgress, IPDAdmission, NursingNote
from app.models.hospital import Bed, Ward
from app.models.patient import PatientVitals

router = APIRouter(prefix="/ipd")


@router.get("")
def ipd_dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    admissions = db.query(IPDAdmission).order_by(IPDAdmission.admission_date.desc()).all()
    wards = db.query(Ward).all()
    return render(request, "ipd/admissions.html", db, current_user, admissions=admissions, wards=wards)


@router.get("/admissions")
def admissions_list(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    admissions = db.query(IPDAdmission).order_by(IPDAdmission.admission_date.desc()).all()
    return render(request, "ipd/admissions.html", db, current_user, admissions=admissions)


@router.post("/admit")
async def admit_patient(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    admission = IPDAdmission(
        hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1),
        patient_id=int(data["patient_id"]),
        doctor_id=int(data["doctor_id"]),
        department_id=int(data["department_id"]) if data.get("department_id") else None,
        ward_id=int(data["ward_id"]) if data.get("ward_id") else None,
        bed_id=int(data["bed_id"]) if data.get("bed_id") else None,
        admission_date=datetime.strptime(data.get("admission_date") or str(date.today()), "%Y-%m-%d").date(),
        admission_time=datetime.strptime(data.get("admission_time") or "10:00", "%H:%M").time(),
        admission_type=data.get("admission_type", "ELECTIVE"),
        primary_diagnosis=data.get("primary_diagnosis"),
        attendant_name=data.get("attendant_name"),
        attendant_phone=data.get("attendant_phone"),
        attendant_relation=data.get("attendant_relation"),
    )
    db.add(admission)
    if admission.bed_id:
        bed = db.query(Bed).filter(Bed.id == admission.bed_id).first()
        bed.status = "OCCUPIED"
        bed.current_patient_id = admission.patient_id
    db.commit()
    return JSONResponse({"message": "Patient admitted", "id": admission.id})


@router.get("/admission/{admission_id}")
def admission_detail(admission_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    admission = db.query(IPDAdmission).filter(IPDAdmission.id == admission_id).first()
    notes = db.query(NursingNote).filter(NursingNote.admission_id == admission_id).all()
    progress = db.query(DailyProgress).filter(DailyProgress.admission_id == admission_id).all()
    vitals = db.query(PatientVitals).filter(PatientVitals.patient_id == admission.patient_id).all() if admission else []
    if not admission:
        raise HTTPException(404, "Admission not found")
    return render(request, "ipd/admissions.html", db, current_user, detail_mode=True, admission=admission, notes=notes, progress=progress, vitals=vitals, admissions=[admission])


@router.post("/admission/{admission_id}/vitals")
async def add_vitals(admission_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    admission = db.query(IPDAdmission).filter(IPDAdmission.id == admission_id).first()
    data = await parse_request_data(request)
    vitals = PatientVitals(patient_id=admission.patient_id, visit_id=admission_id, recorded_by=current_user.id, temperature=float(data.get("temperature") or 0) or None, blood_pressure_sys=int(data.get("blood_pressure_sys") or 0) or None, blood_pressure_dia=int(data.get("blood_pressure_dia") or 0) or None, pulse_rate=int(data.get("pulse_rate") or 0) or None, respiratory_rate=int(data.get("respiratory_rate") or 0) or None, oxygen_saturation=float(data.get("oxygen_saturation") or 0) or None, weight=float(data.get("weight") or 0) or None, height=float(data.get("height") or 0) or None)
    if vitals.weight and vitals.height:
        vitals.bmi = round(vitals.weight / ((vitals.height / 100) ** 2), 2)
    db.add(vitals)
    db.commit()
    return JSONResponse({"message": "Vitals added", "id": vitals.id})


@router.post("/admission/{admission_id}/notes")
async def add_note(admission_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    note = NursingNote(admission_id=admission_id, nurse_id=current_user.id, note_text=data["note_text"], note_type=data.get("note_type", "NURSING"))
    db.add(note)
    db.commit()
    return JSONResponse({"message": "Note added", "id": note.id})


@router.post("/admission/{admission_id}/progress")
async def add_progress(admission_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    progress = DailyProgress(admission_id=admission_id, doctor_id=current_user.id, progress_date=datetime.strptime(data.get("progress_date") or str(date.today()), "%Y-%m-%d").date(), subjective=data.get("subjective"), objective=data.get("objective"), assessment=data.get("assessment"), plan=data.get("plan"))
    db.add(progress)
    db.commit()
    return JSONResponse({"message": "Progress added", "id": progress.id})


@router.post("/admission/{admission_id}/discharge")
async def discharge_patient(admission_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    admission = db.query(IPDAdmission).filter(IPDAdmission.id == admission_id).first()
    data = await parse_request_data(request)
    admission.status = "DISCHARGED"
    admission.discharge_date = datetime.strptime(data.get("discharge_date") or str(date.today()), "%Y-%m-%d").date()
    admission.discharge_time = datetime.strptime(data.get("discharge_time") or "12:00", "%H:%M").time()
    admission.discharge_summary = data.get("discharge_summary")
    if admission.bed_id:
        bed = db.query(Bed).filter(Bed.id == admission.bed_id).first()
        bed.status = "AVAILABLE"
        bed.current_patient_id = None
    db.commit()
    return JSONResponse({"message": "Patient discharged"})


@router.get("/wards")
def wards_view(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    wards = db.query(Ward).all()
    beds = db.query(Bed).all()
    return render(request, "ipd/wards.html", db, current_user, wards=wards, beds=beds)


@router.get("/bed-status")
def bed_status(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    beds = db.query(Bed).all()
    return [{"id": b.id, "ward_id": b.ward_id, "bed_number": b.bed_number, "status": b.status} for b in beds]
