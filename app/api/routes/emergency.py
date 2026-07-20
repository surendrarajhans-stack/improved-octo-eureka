from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.clinical import EmergencyCase

router = APIRouter(prefix="/emergency")


@router.get("")
def emergency_dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    cases = db.query(EmergencyCase).order_by(EmergencyCase.esi_level, EmergencyCase.arrival_time.desc()).all()
    return render(request, "emergency/dashboard.html", db, current_user, cases=cases)


@router.get("/cases")
def list_cases(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    cases = db.query(EmergencyCase).order_by(EmergencyCase.esi_level).all()
    return [{"id": c.id, "esi_level": c.esi_level, "chief_complaint": c.chief_complaint, "disposition": c.disposition} for c in cases]


@router.post("/register")
async def register_case(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    case = EmergencyCase(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), patient_id=int(data["patient_id"]) if data.get("patient_id") else None, esi_level=int(data.get("esi_level") or 3), arrival_mode=data.get("arrival_mode", "WALK_IN"), chief_complaint=data["chief_complaint"], is_mlc=str(data.get("is_mlc", "false")).lower() in {"true", "1", "yes", "on"}, mlc_number=data.get("mlc_number"), triage_notes=data.get("triage_notes"), attending_doctor_id=int(data["attending_doctor_id"]) if data.get("attending_doctor_id") else None, disposition=data.get("disposition", "ADMITTED"), notes=data.get("notes"))
    db.add(case)
    db.commit()
    return JSONResponse({"message": "Emergency case registered", "id": case.id})


@router.get("/{case_id}")
def case_detail(case_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    case = db.query(EmergencyCase).filter(EmergencyCase.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found")
    return render(request, "emergency/dashboard.html", db, current_user, detail_mode=True, case=case, cases=[case])


@router.put("/{case_id}/status")
async def update_disposition(case_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    case = db.query(EmergencyCase).filter(EmergencyCase.id == case_id).first()
    data = await parse_request_data(request)
    case.disposition = data.get("disposition", case.disposition)
    case.disposition_time = datetime.utcnow()
    db.commit()
    return JSONResponse({"message": "Disposition updated"})


@router.get("/triage")
def triage_board(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    cases = db.query(EmergencyCase).order_by(EmergencyCase.esi_level).all()
    return render(request, "emergency/dashboard.html", db, current_user, triage_mode=True, cases=cases)
