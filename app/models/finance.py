from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    account_code = Column(String(50), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    is_active = Column(Integer, default=1)
    opening_balance = Column(Float, default=0.0)


class JournalEntry(TimestampMixin, Base):
    __tablename__ = "journal_entries"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    entry_number = Column(String(100), nullable=False)
    entry_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(255), nullable=True)
    total_debit = Column(Float, default=0.0)
    total_credit = Column(Float, default=0.0)
    status = Column(String(20), default="DRAFT")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class JournalLine(TimestampMixin, Base):
    __tablename__ = "journal_lines"

    journal_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    description = Column(Text, nullable=True)


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    expense_date = Column(Date, nullable=False)
    category = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    amount = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    receipt_path = Column(String(255), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="PENDING")
    payment_mode = Column(String(50), nullable=True)
    payment_date = Column(Date, nullable=True)


class Budget(TimestampMixin, Base):
    __tablename__ = "budgets"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    fiscal_year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)
    budgeted_amount = Column(Float, default=0.0)
    actual_amount = Column(Float, default=0.0)
