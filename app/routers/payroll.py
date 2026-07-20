from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.payroll import Deduction, Payroll, SalaryComponent
from app.schemas.payroll import (
    DeductionCreate,
    DeductionResponse,
    DeductionUpdate,
    PayrollCreate,
    PayrollResponse,
    PayrollUpdate,
    SalaryComponentCreate,
    SalaryComponentResponse,
    SalaryComponentUpdate,
)

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.get("/", response_model=list[PayrollResponse])
async def list_payrolls(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Payroll).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=PayrollResponse, status_code=status.HTTP_201_CREATED)
async def create_payroll(
    data: PayrollCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payroll = Payroll(**data.model_dump())
    db.add(payroll)
    await db.flush()
    await db.refresh(payroll)
    return payroll


@router.get("/{payroll_id}", response_model=PayrollResponse)
async def get_payroll(
    payroll_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Payroll).where(Payroll.id == payroll_id))
    payroll = result.scalar_one_or_none()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return payroll


@router.put("/{payroll_id}", response_model=PayrollResponse)
async def update_payroll(
    payroll_id: int,
    data: PayrollUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Payroll).where(Payroll.id == payroll_id))
    payroll = result.scalar_one_or_none()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(payroll, key, value)
    await db.flush()
    await db.refresh(payroll)
    return payroll


@router.get("/salary-components/all", response_model=list[SalaryComponentResponse])
async def list_salary_components(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(SalaryComponent).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/salary-components",
    response_model=SalaryComponentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_salary_component(
    data: SalaryComponentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    component = SalaryComponent(**data.model_dump())
    db.add(component)
    await db.flush()
    await db.refresh(component)
    return component


@router.put("/salary-components/{component_id}", response_model=SalaryComponentResponse)
async def update_salary_component(
    component_id: int,
    data: SalaryComponentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(SalaryComponent).where(SalaryComponent.id == component_id)
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Salary component not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(component, key, value)
    await db.flush()
    await db.refresh(component)
    return component


@router.get("/deductions/all", response_model=list[DeductionResponse])
async def list_deductions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Deduction).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/deductions", response_model=DeductionResponse, status_code=status.HTTP_201_CREATED
)
async def create_deduction(
    data: DeductionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deduction = Deduction(**data.model_dump())
    db.add(deduction)
    await db.flush()
    await db.refresh(deduction)
    return deduction


@router.put("/deductions/{deduction_id}", response_model=DeductionResponse)
async def update_deduction(
    deduction_id: int,
    data: DeductionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Deduction).where(Deduction.id == deduction_id))
    deduction = result.scalar_one_or_none()
    if not deduction:
        raise HTTPException(status_code=404, detail="Deduction not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(deduction, key, value)
    await db.flush()
    await db.refresh(deduction)
    return deduction
