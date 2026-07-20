from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.hr import Attendance, Employee, LeaveRequest
from app.schemas.hr import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestUpdate,
)

router = APIRouter(prefix="/hr", tags=["HR"])


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Employee).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED
)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = Employee(**data.model_dump())
    db.add(employee)
    await db.flush()
    await db.refresh(employee)
    return employee


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(emp, key, value)
    await db.flush()
    await db.refresh(emp)
    return emp


@router.get("/leave-requests", response_model=list[LeaveRequestResponse])
async def list_leave_requests(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LeaveRequest).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED
)
async def create_leave_request(
    data: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    leave = LeaveRequest(**data.model_dump())
    db.add(leave)
    await db.flush()
    await db.refresh(leave)
    return leave


@router.get("/leave-requests/{leave_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    leave_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LeaveRequest).where(LeaveRequest.id == leave_id))
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave


@router.put("/leave-requests/{leave_id}", response_model=LeaveRequestResponse)
async def update_leave_request(
    leave_id: int,
    data: LeaveRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LeaveRequest).where(LeaveRequest.id == leave_id))
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(leave, key, value)
    await db.flush()
    await db.refresh(leave)
    return leave


@router.get("/attendance", response_model=list[AttendanceResponse])
async def list_attendance(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Attendance).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED
)
async def record_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    attendance = Attendance(**data.model_dump())
    db.add(attendance)
    await db.flush()
    await db.refresh(attendance)
    return attendance


@router.put("/attendance/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: int,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
    attendance = result.scalar_one_or_none()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(attendance, key, value)
    await db.flush()
    await db.refresh(attendance)
    return attendance
