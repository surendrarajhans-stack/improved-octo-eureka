from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.hr import Attendance, Employee, Leave, Payroll

router = APIRouter(prefix="/hr")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    employees = db.query(Employee).order_by(Employee.id.desc()).limit(10).all()
    return render(request, "hr/employees.html", db, current_user, employees=employees)


@router.get("/employees")
def employees(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    employees = db.query(Employee).order_by(Employee.id.desc()).all()
    return render(request, "hr/employees.html", db, current_user, employees=employees)


@router.post("/employees")
async def add_employee(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    employee = Employee(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), user_id=int(data["user_id"]) if data.get("user_id") else None, employee_code=data["employee_code"], first_name=data["first_name"], last_name=data.get("last_name", ""), phone=data.get("phone"), email=data.get("email"), department_id=int(data["department_id"]) if data.get("department_id") else None, designation=data.get("designation"), employment_type=data.get("employment_type"), join_date=date.fromisoformat(data["join_date"]) if data.get("join_date") else None, salary=float(data.get("salary") or 0))
    db.add(employee)
    db.commit()
    return JSONResponse({"message": "Employee added", "id": employee.id})


@router.get("/employees/{employee_id}")
def employee_detail(employee_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(404, "Employee not found")
    return render(request, "hr/employees.html", db, current_user, detail_mode=True, employee=employee, employees=[employee])


@router.get("/attendance")
def attendance(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    records = db.query(Attendance).order_by(Attendance.date.desc()).all()
    return render(request, "hr/attendance.html", db, current_user, records=records)


@router.post("/attendance")
async def mark_attendance(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    record = Attendance(employee_id=int(data["employee_id"]), date=date.fromisoformat(data["date"]), check_in=datetime.strptime(data["check_in"], "%H:%M").time() if data.get("check_in") else None, check_out=datetime.strptime(data["check_out"], "%H:%M").time() if data.get("check_out") else None, total_hours=float(data.get("total_hours") or 0), status=data.get("status", "PRESENT"), notes=data.get("notes"))
    db.add(record)
    db.commit()
    return JSONResponse({"message": "Attendance marked", "id": record.id})


@router.get("/leave")
def leave_requests(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    leave_records = db.query(Leave).order_by(Leave.applied_on.desc()).all()
    return render(request, "hr/employees.html", db, current_user, leave_mode=True, leave_records=leave_records)


@router.post("/leave")
async def apply_leave(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    leave = Leave(employee_id=int(data["employee_id"]), leave_type=data["leave_type"], start_date=date.fromisoformat(data["start_date"]), end_date=date.fromisoformat(data["end_date"]), days=float(data.get("days") or 1), reason=data.get("reason"), status="PENDING")
    db.add(leave)
    db.commit()
    return JSONResponse({"message": "Leave applied", "id": leave.id})


@router.put("/leave/{leave_id}/approve")
async def approve_leave(leave_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    data = await parse_request_data(request)
    leave.status = data.get("status", "APPROVED")
    leave.approved_by = current_user.id
    leave.approved_on = datetime.utcnow()
    db.commit()
    return JSONResponse({"message": "Leave updated"})


@router.get("/payroll")
def payroll(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    records = db.query(Payroll).order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    return render(request, "hr/employees.html", db, current_user, payroll_mode=True, payroll=records)


@router.post("/payroll/generate")
async def generate_payroll(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    month = int(data["month"])
    year = int(data["year"])
    created = 0
    for employee in db.query(Employee).all():
        if db.query(Payroll).filter(Payroll.employee_id == employee.id, Payroll.month == month, Payroll.year == year).first():
            continue
        gross = employee.salary
        payroll = Payroll(employee_id=employee.id, month=month, year=year, basic_salary=employee.salary, allowances=employee.salary * 0.1, deductions=employee.salary * 0.05, gross_salary=gross, tax_deducted=employee.salary * 0.02, pf_deducted=employee.salary * 0.03, net_salary=employee.salary * 1.0, status="PROCESSED", processed_on=datetime.utcnow())
        db.add(payroll)
        created += 1
    db.commit()
    return JSONResponse({"message": "Payroll generated", "created": created})
