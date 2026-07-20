from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.hr import AttendanceStatus, EmploymentType, LeaveStatus, LeaveType


class EmployeeBase(BaseModel):
    user_id: int
    staff_id: int | None = None
    department_id: int
    position: str
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    hire_date: date
    termination_date: date | None = None
    manager_id: int | None = None
    skills: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    department_id: int | None = None
    position: str | None = None
    employment_type: EmploymentType | None = None
    termination_date: date | None = None
    manager_id: int | None = None
    skills: str | None = None


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LeaveRequestBase(BaseModel):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    days_count: float
    reason: str | None = None


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    status: LeaveStatus | None = None
    approved_by: int | None = None
    reviewed_at: datetime | None = None


class LeaveRequestResponse(LeaveRequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: LeaveStatus
    approved_by: int | None = None
    applied_at: datetime
    reviewed_at: datetime | None = None


class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    hours_worked: float | None = None
    status: AttendanceStatus = AttendanceStatus.PRESENT


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    check_in: datetime | None = None
    check_out: datetime | None = None
    hours_worked: float | None = None
    status: AttendanceStatus | None = None


class AttendanceResponse(AttendanceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
