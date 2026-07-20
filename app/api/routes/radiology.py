from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.radiology import RadiologyOrder, RadiologyReport

router = APIRouter(prefix="/radiology")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    orders = db.query(RadiologyOrder).order_by(RadiologyOrder.created_at.desc()).all()
    return render(request, "laboratory/orders.html", db, current_user, orders=orders, radiology_mode=True)


@router.get("/orders")
def orders(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    orders = db.query(RadiologyOrder).order_by(RadiologyOrder.created_at.desc()).all()
    return render(request, "laboratory/orders.html", db, current_user, orders=orders, radiology_mode=True)


@router.post("/orders")
async def create_order(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    order = RadiologyOrder(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), patient_id=int(data["patient_id"]), doctor_id=int(data["doctor_id"]) if data.get("doctor_id") else None, study_type=data["study_type"], body_part=data.get("body_part"), clinical_history=data.get("clinical_history"), priority=data.get("priority", "ROUTINE"), status=data.get("status", "ORDERED"), scheduled_date=datetime.fromisoformat(data["scheduled_date"]) if data.get("scheduled_date") else None, notes=data.get("notes"))
    db.add(order)
    db.commit()
    return JSONResponse({"message": "Radiology order created", "id": order.id})


@router.get("/orders/{order_id}")
def detail(order_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    order = db.query(RadiologyOrder).filter(RadiologyOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    report = db.query(RadiologyReport).filter(RadiologyReport.order_id == order_id).first()
    return render(request, "laboratory/orders.html", db, current_user, detail_mode=True, order=order, report=report, radiology_mode=True)


@router.post("/reports/{order_id}")
async def submit_report(order_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    order = db.query(RadiologyOrder).filter(RadiologyOrder.id == order_id).first()
    report = db.query(RadiologyReport).filter(RadiologyReport.order_id == order_id).first()
    if not report:
        report = RadiologyReport(order_id=order_id, patient_id=order.patient_id)
        db.add(report)
    report.radiologist_id = current_user.id
    report.findings = data.get("findings")
    report.impression = data.get("impression")
    report.recommendations = data.get("recommendations")
    report.is_verified = str(data.get("is_verified", "false")).lower() in {"true", "1", "yes", "on"}
    order.status = "COMPLETED"
    db.commit()
    return JSONResponse({"message": "Report submitted", "id": report.id})


@router.get("/reports/{report_id}")
def view_report(report_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    report = db.query(RadiologyReport).filter(RadiologyReport.id == report_id).first()
    return {"id": report.id, "findings": report.findings, "impression": report.impression, "recommendations": report.recommendations}
