from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.laboratory import LabOrder, LabOrderItem, LabReport, LabTest
from app.services.report_service import ReportService

router = APIRouter(prefix="/laboratory")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    orders = db.query(LabOrder).order_by(LabOrder.order_date.desc()).limit(20).all()
    return render(request, "laboratory/orders.html", db, current_user, orders=orders)


@router.get("/orders")
def orders(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    orders = db.query(LabOrder).order_by(LabOrder.order_date.desc()).all()
    tests = db.query(LabTest).filter(LabTest.is_active.is_(True)).all()
    return render(request, "laboratory/orders.html", db, current_user, orders=orders, tests=tests)


@router.post("/orders")
async def create_order(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    test_ids = data.get("test_ids", [])
    if isinstance(test_ids, str):
        import json
        test_ids = json.loads(test_ids) if test_ids.startswith("[") else [int(v) for v in test_ids.split(",") if v]
    order = LabOrder(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), patient_id=int(data["patient_id"]), doctor_id=int(data["doctor_id"]) if data.get("doctor_id") else None, sample_type=data.get("sample_type"), priority=data.get("priority", "ROUTINE"), notes=data.get("notes"))
    db.add(order)
    db.flush()
    for test_id in test_ids:
        db.add(LabOrderItem(order_id=order.id, test_id=int(test_id)))
    db.commit()
    return JSONResponse({"message": "Lab order created", "id": order.id})


@router.get("/orders/{order_id}")
def order_detail(order_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    items = db.query(LabOrderItem).filter(LabOrderItem.order_id == order_id).all()
    if not order:
        raise HTTPException(404, "Order not found")
    return render(request, "laboratory/orders.html", db, current_user, detail_mode=True, order=order, items=items, orders=[order])


@router.put("/orders/{order_id}/collect")
def collect_sample(order_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    order.status = "SAMPLE_COLLECTED"
    order.sample_collection_date = datetime.utcnow()
    db.commit()
    return JSONResponse({"message": "Sample collected"})


@router.post("/orders/{order_id}/results")
async def enter_results(order_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    item = db.query(LabOrderItem).filter(LabOrderItem.id == int(data["item_id"]), LabOrderItem.order_id == order_id).first()
    item.result_value = data.get("result_value")
    item.result_text = data.get("result_text")
    item.is_abnormal = str(data.get("is_abnormal", "false")).lower() in {"true", "1", "yes", "on"}
    item.status = "COMPLETED"
    item.verified_by = current_user.id
    item.verified_at = datetime.utcnow()
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    order.status = "COMPLETED"
    report = db.query(LabReport).filter(LabReport.order_id == order_id).first()
    if not report:
        report = LabReport(order_id=order_id, patient_id=order.patient_id, interpretation=data.get("interpretation"))
        db.add(report)
    db.commit()
    return JSONResponse({"message": "Results saved", "report_id": report.id})


@router.get("/reports")
def reports(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    reports = db.query(LabReport).order_by(LabReport.report_date.desc()).all()
    return render(request, "laboratory/reports.html", db, current_user, reports=reports)


@router.get("/reports/{report_id}")
def view_report(report_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    pdf = ReportService(db).generate_lab_report_pdf(report_id)
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=lab-report-{report_id}.pdf"})


@router.get("/tests")
def tests_catalog(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    tests = db.query(LabTest).filter(LabTest.is_active.is_(True)).all()
    return [{"id": t.id, "name": t.test_name, "code": t.test_code, "price": t.price} for t in tests]
