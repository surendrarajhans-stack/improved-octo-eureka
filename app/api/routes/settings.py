from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.core.permissions import UserRole
from app.core.security import get_password_hash
from app.database import get_db
from app.models.billing import BillingRate
from app.models.hospital import Department, Hospital
from app.models.user import AuditLog, User

router = APIRouter(prefix="/settings")


@router.get("")
def settings_index(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    hospital = db.query(Hospital).first()
    departments = db.query(Department).all()
    users = db.query(User).all()
    return render(request, "settings/index.html", db, current_user, hospital=hospital, departments=departments, users=users)


@router.get("/hospital")
def hospital_info(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    hospital = db.query(Hospital).first()
    return render(request, "settings/index.html", db, current_user, hospital=hospital, hospital_mode=True)


@router.post("/hospital")
async def update_hospital(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    hospital = db.query(Hospital).first()
    if not hospital:
        hospital = Hospital(code=data.get("code", "CGH"), name=data["name"])
        db.add(hospital)
    for field in ["name", "code", "address", "city", "state", "country", "phone", "email", "website", "registration_no", "accreditation"]:
        if field in data:
            setattr(hospital, field, data[field])
    db.commit()
    return JSONResponse({"message": "Hospital info updated"})


@router.get("/departments")
def departments_view(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return render(request, "settings/index.html", db, current_user, departments=departments, department_mode=True)


@router.post("/departments")
async def add_department(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    department = Department(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), name=data["name"], code=data["code"], head_doctor_id=int(data["head_doctor_id"]) if data.get("head_doctor_id") else None, floor=data.get("floor"), phone=data.get("phone"), description=data.get("description"))
    db.add(department)
    db.commit()
    return JSONResponse({"message": "Department added", "id": department.id})


@router.put("/departments/{department_id}")
async def update_department(department_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(404, "Department not found")
    data = await parse_request_data(request)
    for field in ["name", "code", "floor", "phone", "description"]:
        if field in data:
            setattr(department, field, data[field])
    db.commit()
    return JSONResponse({"message": "Department updated"})


@router.get("/billing-rates")
def billing_rates(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    rates = db.query(BillingRate).all()
    return render(request, "settings/index.html", db, current_user, rates=rates, rates_mode=True)


@router.post("/billing-rates")
async def add_rate(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    rate = BillingRate(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), service_type=data["service_type"], service_name=data["service_name"], price=float(data.get("price") or 0), tax_percent=float(data.get("tax_percent") or 0), description=data.get("description"), is_active=1)
    db.add(rate)
    db.commit()
    return JSONResponse({"message": "Rate added", "id": rate.id})


@router.get("/users")
def users_view(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return render(request, "settings/index.html", db, current_user, users=users, users_mode=True)


@router.post("/users")
async def create_user(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    user = User(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), username=data["username"], email=data["email"], password_hash=get_password_hash(data.get("password") or "password123"), full_name=data["full_name"], phone=data.get("phone"), role=UserRole(data.get("role", "GUEST")), is_active=True)
    db.add(user)
    db.commit()
    return JSONResponse({"message": "User created", "id": user.id})


@router.put("/users/{user_id}")
async def update_user(user_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    data = await parse_request_data(request)
    for field in ["username", "email", "full_name", "phone"]:
        if field in data:
            setattr(user, field, data[field])
    if data.get("role"):
        user.role = UserRole(data["role"])
    db.commit()
    return JSONResponse({"message": "User updated"})


@router.get("/audit-logs")
def audit_logs(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render(request, "settings/index.html", db, current_user, logs=logs, logs_mode=True)
