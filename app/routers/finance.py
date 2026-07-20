from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.finance import Account, Budget, Transaction, TransactionEntry
from app.schemas.finance import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/finance", tags=["Finance"])


async def _generate_transaction_number(db: AsyncSession) -> str:
    year = datetime.now().year
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.transaction_number.like(f"TXN-{year}-%")
        )
    )
    count = result.scalar() or 0
    return f"TXN-{year}-{count + 1:05d}"


@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Account).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    account = Account(**data.model_dump())
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    await db.flush()
    await db.refresh(account)
    return account


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Transaction).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    txn_number = await _generate_transaction_number(db)
    entries = data.entries
    txn_data = data.model_dump(exclude={"entries"})
    transaction = Transaction(**txn_data, transaction_number=txn_number, created_by=current_user.id)
    db.add(transaction)
    await db.flush()

    for entry_data in entries:
        entry = TransactionEntry(**entry_data.model_dump(), transaction_id=transaction.id)
        db.add(entry)

    await db.flush()
    await db.refresh(transaction)
    return transaction


@router.get("/transactions/{txn_id}", response_model=TransactionResponse)
async def get_transaction(
    txn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Transaction).where(Transaction.id == txn_id))
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.put("/transactions/{txn_id}", response_model=TransactionResponse)
async def update_transaction(
    txn_id: int,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Transaction).where(Transaction.id == txn_id))
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, key, value)
    await db.flush()
    await db.refresh(txn)
    return txn


@router.get("/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Budget).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    budget = Budget(**data.model_dump())
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Budget).where(Budget.id == budget_id))
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)
    await db.flush()
    await db.refresh(budget)
    return budget
