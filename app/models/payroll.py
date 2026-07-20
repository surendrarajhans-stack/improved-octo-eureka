import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PayrollStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSED = "PROCESSED"
    APPROVED = "APPROVED"
    PAID = "PAID"


class ComponentType(str, enum.Enum):
    BASIC = "BASIC"
    HRA = "HRA"
    DA = "DA"
    TA = "TA"
    MEDICAL = "MEDICAL"
    OTHER = "OTHER"


class DeductionType(str, enum.Enum):
    TAX = "TAX"
    PF = "PF"
    ESI = "ESI"
    LOAN = "LOAN"
    OTHER = "OTHER"


class Payroll(Base):
    __tablename__ = "payrolls"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    basic_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    allowances: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    gross_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    net_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PayrollStatus] = mapped_column(
        Enum(PayrollStatus), default=PayrollStatus.DRAFT, nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    employee = relationship("Employee", foreign_keys=[employee_id], lazy="noload")
    deduction_items = relationship("Deduction", back_populates="payroll", lazy="noload")


class SalaryComponent(Base):
    __tablename__ = "salary_components"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    component_type: Mapped[ComponentType] = mapped_column(Enum(ComponentType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_taxable: Mapped[bool] = mapped_column(default=True, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    employee = relationship("Employee", foreign_keys=[employee_id], lazy="noload")


class Deduction(Base):
    __tablename__ = "deductions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payroll_id: Mapped[int] = mapped_column(ForeignKey("payrolls.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    deduction_type: Mapped[DeductionType] = mapped_column(Enum(DeductionType), nullable=False)

    payroll = relationship("Payroll", back_populates="deduction_items", lazy="noload")
