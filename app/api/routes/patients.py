from datetime import datetime
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import (
    audit,
    generate_patient_uhid,
    generate_qr_code,
    paginate,
    parse_request_data,
    redirect_with_message,
    render,
)
from app.database import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient, PatientAllergy, PatientDocument, PatientMedicalHistory, PatientVitals

router = APIRouter()
UPLOAD_DIR = FilePath("static/uploads/patients")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _patient_query(db: Session, search: str | None = None, gender: str | None = None, blood_group: str | None = None):
    query = db.query(Patient).filter(Patient.is_deleted.is_(False))
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Patient.first_name.ilike(term), Patient.last_name.ilike(term), Patient.uhid.ilike(term), Patient.phone.ilike(term)))
    if gender:
        query = query.filter(Patient.gender == gender)
    if blood_group:
        query = query.filter(Patient.blood_group == blood_group)
    return query.order_by(Patient.id.desc())


@router.get("")
def patient_list(request: Request, page: int = 1, per_page: int = 20, search: str | None = None, gender: str | None = None, blood_group: str | None = None, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    query = _patient_query(db, search, gender, blood_group)
    patients, total = paginate(query, page, per_page)
    return render(request, "patients/list.html", db, current_user, patients=patients, total=total, page=page, per_page=per_page, search=search or "", gender=gender or "", blood_group=blood_group or "")


@router.get("/create")
def patient_create_form(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    preview = generate_patient_uhid(db)
    return render(request, "patients/create.html", db, current_user, uhid_preview=preview)


@router.post("")
async def create_patient(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    hospital_id = int(data.get("hospital_id") or current_user.hospital_id or 1)
    uhid = generate_patient_uhid(db)
    qr_code = generate_qr_code(uhid)
    patient = Patient(
        hospital_id=hospital_id,
        uhid=uhid,
        qr_code=qr_code,
        first_name=data["first_name"],
        last_name=data.get("last_name", ""),
        dob=datetime.strptime(data["dob"], "%Y-%m-%d").date() if data.get("dob") else None,
        gender=data.get("gender"),
        blood_group=data.get("blood_group"),
        phone=data.get("phone"),
        alt_phone=data.get("alt_phone"),
        email=data.get("email"),
        address=data.get("address"),
        city=data.get("city"),
        state=data.get("state"),
        country=data.get("country"),
        pincode=data.get("pincode"),
        emergency_contact_name=data.get("emergency_contact_name"),
        emergency_contact_phone=data.get("emergency_contact_phone"),
        emergency_contact_relation=data.get("emergency_contact_relation"),
        aadhar_no=data.get("aadhar_no"),
        pan_no=data.get("pan_no"),
        marital_status=data.get("marital_status"),
        occupation=data.get("occupation"),
        religion=data.get("religion"),
        nationality=data.get("nationality"),
        notes=data.get("notes"),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    if data.get("medical_history"):
        db.add(PatientMedicalHistory(patient_id=patient.id, condition=data["medical_history"], notes="Seeded from registration"))
    if data.get("allergies"):
        db.add(PatientAllergy(patient_id=patient.id, allergen=data["allergies"], reaction="Reported"))
    db.commit()
    audit(db, current_user.id, "CREATE", "PATIENT", patient.id, new_values={"uhid": patient.uhid}, ip_address=request.client.host if request.client else None)
    if request.headers.get("accept") == "application/json" or "application/json" in request.headers.get("content-type", ""):
        return JSONResponse({"id": patient.id, "uhid": patient.uhid, "message": "Patient created"})
    return redirect_with_message(f"/patients/{patient.id}", "Patient created successfully")


@router.get("/search")
def search_patients(q: str = Query(""), db: Session = Depends(get_db), current_user=Depends(require_auth)):
    patients = _patient_query(db, q).limit(10).all()
    return [{"id": p.id, "uhid": p.uhid, "name": f"{p.first_name} {p.last_name}", "phone": p.phone} for p in patients]


@router.get("/{patient_id}")
def patient_detail(patient_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_deleted.is_(False)).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    visits = db.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(Appointment.appointment_date.desc()).all()
    vitals = db.query(PatientVitals).filter(PatientVitals.patient_id == patient_id).order_by(PatientVitals.recorded_at).all()
    documents = db.query(PatientDocument).filter(PatientDocument.patient_id == patient_id).all()
    allergies = db.query(PatientAllergy).filter(PatientAllergy.patient_id == patient_id).all()
    history = db.query(PatientMedicalHistory).filter(PatientMedicalHistory.patient_id == patient_id).all()
    return render(request, "patients/detail.html", db, current_user, patient=patient, visits=visits, vitals=vitals, documents=documents, allergies=allergies, history=history)


@router.get("/{patient_id}/edit")
def edit_patient_form(patient_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    return render(request, "patients/create.html", db, current_user, patient=patient, uhid_preview=patient.uhid, edit_mode=True)


@router.put("/{patient_id}")
async def update_patient(patient_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_deleted.is_(False)).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    data = await parse_request_data(request)
    for field in ["first_name", "last_name", "gender", "blood_group", "phone", "alt_phone", "email", "address", "city", "state", "country", "pincode", "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation", "notes"]:
        if field in data:
            setattr(patient, field, data[field])
    if data.get("dob"):
        patient.dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
    db.commit()
    audit(db, current_user.id, "UPDATE", "PATIENT", patient.id, new_values=data)
    return JSONResponse({"message": "Patient updated", "id": patient.id})


@router.delete("/{patient_id}")
def delete_patient(patient_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    patient.is_deleted = True
    patient.is_active = False
    db.commit()
    audit(db, current_user.id, "DELETE", "PATIENT", patient.id)
    return JSONResponse({"message": "Patient deleted"})


@router.get("/{patient_id}/history")
def patient_history(patient_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    visits = db.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(Appointment.appointment_date.desc()).all()
    return [{"id": visit.id, "date": str(visit.appointment_date), "doctor_id": visit.doctor_id, "status": visit.status} for visit in visits]


@router.post("/{patient_id}/documents")
async def upload_document(patient_id: int, request: Request, document: UploadFile | None = File(default=None), current_user=Depends(require_auth), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    data = await parse_request_data(request)
    file_path = data.get("file_path")
    if document is not None:
        content = await document.read()
        destination = UPLOAD_DIR / f"{patient_id}_{document.filename}"
        destination.write_bytes(content)
        file_path = str(destination)
    if not file_path:
        raise HTTPException(400, "No file provided")
    record = PatientDocument(patient_id=patient_id, document_type=data.get("document_type", "GENERAL"), file_path=file_path, description=data.get("description"))
    db.add(record)
    db.commit()
    return JSONResponse({"message": "Document uploaded", "id": record.id})
