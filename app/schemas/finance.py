from pydantic import BaseModel, ConfigDict

from app.models.finance import AccountType, BudgetPeriod


class AccountBase(BaseModel):
    account_code: str
    name: str
    account_type: AccountType
    parent_id: int | None = None
    description: str | None = None
    balance: float = 0.0
    is_active: bool = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: AccountType | None = None
    parent_id: int | None = None
    description: str | None = None
    balance: float | None = None
    is_active: bool | None = None


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TransactionEntryBase(BaseModel):
    account_id: int
    debit_amount: float = 0.0
    credit_amount: float = 0.0


class TransactionEntryCreate(TransactionEntryBase):
    pass


class TransactionEntryResponse(TransactionEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_id: int


class TransactionBase(BaseModel):
    description: str
    total_amount: float
    reference_type: str | None = None
    reference_id: str | None = None
    notes: str | None = None


class TransactionCreate(TransactionBase):
    entries: list[TransactionEntryCreate] = []


class TransactionUpdate(BaseModel):
    description: str | None = None
    total_amount: float | None = None
    notes: str | None = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_number: str
    created_by: int | None = None


class BudgetBase(BaseModel):
    account_id: int
    fiscal_year: int
    period: BudgetPeriod
    budgeted_amount: float
    actual_amount: float = 0.0
    variance: float = 0.0


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    budgeted_amount: float | None = None
    actual_amount: float | None = None
    variance: float | None = None


class BudgetResponse(BudgetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
