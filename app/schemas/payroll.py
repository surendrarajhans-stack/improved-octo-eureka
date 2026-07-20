from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.payroll import ComponentType, DeductionType, PayrollStatus


class PayrollBase(BaseModel):
    employee_id: int
    period_start: datetime
    period_end: datetime
    basic_salary: float
    allowances: float = 0.0
    deductions: float = 0.0
    gross_salary: float
    tax: float = 0.0
    net_salary: float
    status: PayrollStatus = PayrollStatus.DRAFT


class PayrollCreate(PayrollBase):
    pass


class PayrollUpdate(BaseModel):
    basic_salary: float | None = None
    allowances: float | None = None
    deductions: float | None = None
    gross_salary: float | None = None
    tax: float | None = None
    net_salary: float | None = None
    status: PayrollStatus | None = None
    processed_at: datetime | None = None
    paid_at: datetime | None = None


class PayrollResponse(PayrollBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    processed_at: datetime | None = None
    paid_at: datetime | None = None


class SalaryComponentBase(BaseModel):
    employee_id: int
    component_type: ComponentType
    amount: float
    is_taxable: bool = True
    effective_from: datetime


class SalaryComponentCreate(SalaryComponentBase):
    pass


class SalaryComponentUpdate(BaseModel):
    amount: float | None = None
    is_taxable: bool | None = None
    effective_from: datetime | None = None


class SalaryComponentResponse(SalaryComponentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DeductionBase(BaseModel):
    payroll_id: int
    description: str
    amount: float
    deduction_type: DeductionType


class DeductionCreate(DeductionBase):
    pass


class DeductionUpdate(BaseModel):
    description: str | None = None
    amount: float | None = None
    deduction_type: DeductionType | None = None


class DeductionResponse(DeductionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
