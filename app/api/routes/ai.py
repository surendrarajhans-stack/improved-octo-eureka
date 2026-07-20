from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai")


@router.get("")
def ai_home(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    service = AIService(db)
    insights = service.get_dashboard_insights(current_user.hospital_id or 1)
    return render(request, "ai/assistant.html", db, current_user, insights=insights)


@router.get("/assistant")
def assistant(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    return ai_home(request, current_user, db)


@router.post("/assistant/chat")
async def assistant_chat(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    response = AIService(db).chat_response(data.get("message", ""), data.get("context"))
    return JSONResponse({"message": response})


@router.get("/insights/revenue")
def revenue_insights(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    return AIService(db).predict_revenue(current_user.hospital_id or 1)


@router.get("/insights/patient-load")
def patient_load(target_date: str | None = None, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    dt = date.fromisoformat(target_date) if target_date else date.today() + timedelta(days=1)
    return AIService(db).predict_patient_load(current_user.hospital_id or 1, dt)


@router.get("/insights/bed-occupancy")
def bed_occupancy(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    return AIService(db).predict_bed_occupancy(current_user.hospital_id or 1)


@router.get("/insights/medicine-demand")
def medicine_demand(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    return AIService(db).predict_medicine_demand(current_user.hospital_id or 1)


@router.get("/insights/appointments")
def appointment_optimization(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    load = AIService(db).predict_patient_load(current_user.hospital_id or 1, date.today() + timedelta(days=1))
    suggestions = [
        {"priority": "High", "suggestion": "Open additional OPD slots if forecast exceeds 25 patients.", "forecast": load["predicted_count"]},
        {"priority": "Medium", "suggestion": "Call high-priority patients 15 minutes earlier to reduce congestion."},
    ]
    return suggestions


@router.post("/drug-interaction")
async def drug_interaction(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    medicine_ids = data.get("medicine_ids", [])
    if isinstance(medicine_ids, str):
        import json
        medicine_ids = json.loads(medicine_ids) if medicine_ids.startswith("[") else [int(v) for v in medicine_ids.split(",") if v]
    return AIService(db).check_drug_interaction([int(mid) for mid in medicine_ids])


@router.post("/icd-coding")
async def icd_coding(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    return AIService(db).suggest_icd_codes(data.get("diagnosis_text", ""))


@router.get("/dashboard")
def ai_dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    service = AIService(db)
    insights = service.get_dashboard_insights(current_user.hospital_id or 1)
    revenue = service.predict_revenue(current_user.hospital_id or 1)
    return render(request, "ai/assistant.html", db, current_user, insights=insights, forecast=revenue)
