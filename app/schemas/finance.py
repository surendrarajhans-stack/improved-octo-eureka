from datetime import date

from pydantic import BaseModel


class AccountCreate(BaseModel):
    hospital_id: int
    account_code: str
    account_name: str
    account_type: str
    parent_id: int | None = None
    opening_balance: float = 0.0


class JournalLineInput(BaseModel):
    account_id: int
    debit_amount: float = 0.0
    credit_amount: float = 0.0
    description: str | None = None


class JournalEntryCreate(BaseModel):
    hospital_id: int
    entry_number: str
    entry_date: date
    description: str | None = None
    reference: str | None = None
    lines: list[JournalLineInput]


class ExpenseCreate(BaseModel):
    hospital_id: int
    expense_date: date
    category: str
    department_id: int | None = None
    amount: float
    description: str | None = None
    payment_mode: str | None = None
