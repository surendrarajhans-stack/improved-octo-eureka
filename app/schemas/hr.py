from datetime import date, time

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    hospital_id: int
    employee_code: str
    first_name: str
    last_name: str
    phone: str | None = None
    email: str | None = None
    department_id: int | None = None
    designation: str | None = None
    employment_type: str | None = None
    join_date: date | None = None
    salary: float = 0.0


class AttendanceCreate(BaseModel):
    employee_id: int
    date: date
    check_in: time | None = None
    check_out: time | None = None
    total_hours: float = 0.0
    status: str
    notes: str | None = None


class LeaveCreate(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days: float = 1.0
    reason: str | None = None


class PayrollGenerate(BaseModel):
    month: int
    year: int
