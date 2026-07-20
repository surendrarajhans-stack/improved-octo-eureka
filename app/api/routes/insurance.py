from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.insurance import InsuranceClaim, InsurancePolicy

router = APIRouter(prefix="/insurance")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    policies = db.query(InsurancePolicy).order_by(InsurancePolicy.id.desc()).limit(10).all()
    claims = db.query(InsuranceClaim).order_by(InsuranceClaim.id.desc()).limit(10).all()
    return render(request, "reports/dashboard.html", db, current_user, policies=policies, claims=claims, insurance_mode=True)


@router.get("/policies")
def policies(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    policies = db.query(InsurancePolicy).order_by(InsurancePolicy.id.desc()).all()
    return render(request, "reports/dashboard.html", db, current_user, policies=policies, insurance_mode=True)


@router.post("/policies")
async def add_policy(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    policy = InsurancePolicy(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), patient_id=int(data["patient_id"]) if data.get("patient_id") else None, policy_number=data["policy_number"], policy_type=data.get("policy_type"), insurer_name=data["insurer_name"], tpa_name=data.get("tpa_name"), coverage_amount=float(data.get("coverage_amount") or 0), copay_percent=float(data.get("copay_percent") or 0), start_date=date.fromisoformat(data["start_date"]) if data.get("start_date") else None, end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None, notes=data.get("notes"))
    db.add(policy)
    db.commit()
    return JSONResponse({"message": "Policy added", "id": policy.id})


@router.get("/claims")
def claims(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    claims = db.query(InsuranceClaim).order_by(InsuranceClaim.id.desc()).all()
    return render(request, "reports/dashboard.html", db, current_user, claims=claims, insurance_mode=True)


@router.post("/claims")
async def submit_claim(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    claim = InsuranceClaim(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), invoice_id=int(data["invoice_id"]), policy_id=int(data["policy_id"]), patient_id=int(data["patient_id"]), claim_number=data["claim_number"], diagnosis=data.get("diagnosis"), claimed_amount=float(data.get("claimed_amount") or 0), approved_amount=float(data.get("approved_amount") or 0), rejected_amount=float(data.get("rejected_amount") or 0), status=data.get("status", "SUBMITTED"), submission_date=date.today(), notes=data.get("notes"))
    db.add(claim)
    db.commit()
    return JSONResponse({"message": "Claim submitted", "id": claim.id})


@router.put("/claims/{claim_id}/status")
async def update_claim_status(claim_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    data = await parse_request_data(request)
    claim.status = data.get("status", claim.status)
    claim.approved_amount = float(data.get("approved_amount") or claim.approved_amount or 0)
    claim.rejected_amount = float(data.get("rejected_amount") or claim.rejected_amount or 0)
    claim.rejection_reason = data.get("rejection_reason")
    db.commit()
    return JSONResponse({"message": "Claim updated"})
