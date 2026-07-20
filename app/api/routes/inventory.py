from datetime import date, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.inventory import GRN, InventoryItem, PurchaseOrder, StockTransfer

router = APIRouter(prefix="/inventory")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    items = db.query(InventoryItem).order_by(InventoryItem.name).limit(20).all()
    low_stock = [item for item in items if item.current_stock <= item.reorder_level]
    return render(request, "inventory/stock.html", db, current_user, items=items, low_stock=low_stock)


@router.get("/items")
def items(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    items = db.query(InventoryItem).order_by(InventoryItem.name).all()
    return render(request, "inventory/stock.html", db, current_user, items=items)


@router.post("/items")
async def add_item(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    item = InventoryItem(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), category_id=int(data["category_id"]) if data.get("category_id") else None, name=data["name"], code=data["code"], unit=data.get("unit"), reorder_level=int(data.get("reorder_level") or 10), current_stock=float(data.get("current_stock") or 0), location=data.get("location"), description=data.get("description"))
    db.add(item)
    db.commit()
    return JSONResponse({"message": "Item added", "id": item.id})


@router.get("/purchase-orders")
def po_list(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    purchase_orders = db.query(PurchaseOrder).order_by(PurchaseOrder.order_date.desc()).all()
    return render(request, "inventory/stock.html", db, current_user, purchase_orders=purchase_orders, po_mode=True)


@router.post("/purchase-orders")
async def create_po(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    po = PurchaseOrder(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), supplier_id=int(data["supplier_id"]), po_number=data["po_number"], order_date=date.fromisoformat(data["order_date"]), expected_delivery=date.fromisoformat(data["expected_delivery"]) if data.get("expected_delivery") else None, total_amount=float(data.get("total_amount") or 0), status=data.get("status", "DRAFT"), notes=data.get("notes"))
    db.add(po)
    db.commit()
    return JSONResponse({"message": "PO created", "id": po.id})


@router.post("/grn")
async def record_grn(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    grn = GRN(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), po_id=int(data["po_id"]) if data.get("po_id") else None, supplier_id=int(data["supplier_id"]) if data.get("supplier_id") else None, grn_number=data["grn_number"], received_date=date.fromisoformat(data["received_date"]), received_by=current_user.id, total_amount=float(data.get("total_amount") or 0), notes=data.get("notes"))
    db.add(grn)
    db.commit()
    return JSONResponse({"message": "GRN recorded", "id": grn.id})


@router.get("/stock-transfers")
def transfers(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    transfers = db.query(StockTransfer).order_by(StockTransfer.transfer_date.desc()).all()
    return render(request, "inventory/stock.html", db, current_user, transfers=transfers, transfer_mode=True)


@router.post("/stock-transfers")
async def create_transfer(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    transfer = StockTransfer(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), from_department=data.get("from_department"), to_department=data.get("to_department"), transfer_date=datetime.fromisoformat(data.get("transfer_date") or datetime.utcnow().isoformat()), transferred_by=current_user.id, status=data.get("status", "PENDING"), notes=data.get("notes"))
    db.add(transfer)
    db.commit()
    return JSONResponse({"message": "Transfer created", "id": transfer.id})


@router.get("/low-stock")
def low_stock(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    items = db.query(InventoryItem).filter(InventoryItem.current_stock <= InventoryItem.reorder_level).all()
    return render(request, "inventory/stock.html", db, current_user, low_stock=items, items=items)
