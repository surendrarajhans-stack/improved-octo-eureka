from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.pharmacy import Medicine, MedicineBatch, PharmacyDispensing, PharmacyDispensingItem

router = APIRouter(prefix="/pharmacy")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    medicines = db.query(Medicine).order_by(Medicine.name).limit(20).all()
    return render(request, "pharmacy/inventory.html", db, current_user, medicines=medicines)


@router.get("/medicines")
def medicine_inventory(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    medicines = db.query(Medicine).order_by(Medicine.name).all()
    batches = db.query(MedicineBatch).all()
    return render(request, "pharmacy/inventory.html", db, current_user, medicines=medicines, batches=batches)


@router.post("/medicines")
async def add_medicine(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    medicine = Medicine(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), name=data["name"], generic_name=data.get("generic_name"), category=data.get("category"), form=data.get("form"), manufacturer=data.get("manufacturer"), unit=data.get("unit"), reorder_level=int(data.get("reorder_level") or 10), description=data.get("description"))
    db.add(medicine)
    db.commit()
    return JSONResponse({"message": "Medicine added", "id": medicine.id})


@router.get("/dispense")
def dispensing_form(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    medicines = db.query(Medicine).filter(Medicine.is_active.is_(True)).all()
    return render(request, "pharmacy/dispensing.html", db, current_user, medicines=medicines)


@router.post("/dispense")
async def dispense_medicines(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    dispensing = PharmacyDispensing(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), patient_id=int(data["patient_id"]), prescription_id=int(data["prescription_id"]) if data.get("prescription_id") else None, dispensed_by=current_user.id, payment_mode=data.get("payment_mode", "CASH"), payment_status=data.get("payment_status", "PAID"), notes=data.get("notes"))
    db.add(dispensing)
    db.flush()
    import json
    items = json.loads(data.get("items") or "[]")
    total_amount = 0.0
    for item in items:
        unit_price = float(item.get("unit_price") or 0)
        quantity = int(item.get("quantity") or 1)
        total_price = unit_price * quantity
        db.add(PharmacyDispensingItem(dispensing_id=dispensing.id, medicine_id=int(item["medicine_id"]), batch_id=int(item["batch_id"]) if item.get("batch_id") else None, quantity=quantity, unit_price=unit_price, total_price=total_price, instructions=item.get("instructions")))
        total_amount += total_price
    dispensing.total_amount = total_amount
    dispensing.net_amount = total_amount - float(data.get("discount") or 0)
    dispensing.discount = float(data.get("discount") or 0)
    db.commit()
    return JSONResponse({"message": "Medicines dispensed", "id": dispensing.id, "net_amount": dispensing.net_amount})


@router.get("/dispensing/{dispensing_id}")
def dispensing_record(dispensing_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    record = db.query(PharmacyDispensing).filter(PharmacyDispensing.id == dispensing_id).first()
    items = db.query(PharmacyDispensingItem).filter(PharmacyDispensingItem.dispensing_id == dispensing_id).all()
    return {"id": record.id, "patient_id": record.patient_id, "items": [{"medicine_id": i.medicine_id, "quantity": i.quantity, "total_price": i.total_price} for i in items]}


@router.get("/expiry-alerts")
def expiry_alerts(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    threshold = date.today() + timedelta(days=30)
    batches = db.query(MedicineBatch).filter(MedicineBatch.expiry_date <= threshold).all()
    return [{"batch_number": b.batch_number, "medicine_id": b.medicine_id, "expiry_date": str(b.expiry_date)} for b in batches]


@router.get("/low-stock")
def low_stock(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    medicines = db.query(Medicine).filter(Medicine.is_active.is_(True)).all()
    low = []
    for medicine in medicines:
        available = sum(batch.quantity_available for batch in db.query(MedicineBatch).filter(MedicineBatch.medicine_id == medicine.id).all())
        if available <= medicine.reorder_level:
            low.append({"medicine": medicine, "available": available})
    return render(request, "pharmacy/inventory.html", db, current_user, low_stock=low, medicines=medicines)
