from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.billing import Payment
from app.models.finance import Account, Expense, JournalEntry, JournalLine

router = APIRouter(prefix="/finance")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    total_income = db.query(func.coalesce(func.sum(Payment.amount), 0.0)).scalar() or 0.0
    total_expense = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).scalar() or 0.0
    accounts = db.query(Account).order_by(Account.account_code).limit(10).all()
    return render(request, "finance/dashboard.html", db, current_user, total_income=total_income, total_expense=total_expense, accounts=accounts)


@router.get("/accounts")
def accounts(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    records = db.query(Account).order_by(Account.account_code).all()
    return [{"id": a.id, "account_code": a.account_code, "account_name": a.account_name, "account_type": a.account_type} for a in records]


@router.get("/journal")
def journal(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    entries = db.query(JournalEntry).order_by(JournalEntry.entry_date.desc()).all()
    return render(request, "finance/dashboard.html", db, current_user, journal_entries=entries, journal_mode=True)


@router.post("/journal")
async def create_journal(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    import json
    lines = json.loads(data.get("lines") or "[]")
    entry = JournalEntry(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), entry_number=data["entry_number"], entry_date=date.fromisoformat(data["entry_date"]), description=data.get("description"), reference=data.get("reference"), status=data.get("status", "POSTED"), created_by=current_user.id)
    db.add(entry)
    db.flush()
    total_debit = total_credit = 0.0
    for line in lines:
        debit = float(line.get("debit_amount") or 0)
        credit = float(line.get("credit_amount") or 0)
        total_debit += debit
        total_credit += credit
        db.add(JournalLine(journal_id=entry.id, account_id=int(line["account_id"]), debit_amount=debit, credit_amount=credit, description=line.get("description")))
    entry.total_debit = total_debit
    entry.total_credit = total_credit
    db.commit()
    return JSONResponse({"message": "Journal entry created", "id": entry.id})


@router.get("/expenses")
def expenses(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    records = db.query(Expense).order_by(Expense.expense_date.desc()).all()
    return render(request, "finance/dashboard.html", db, current_user, expenses=records, expense_mode=True)


@router.post("/expenses")
async def add_expense(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    expense = Expense(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), expense_date=date.fromisoformat(data["expense_date"]), category=data["category"], department_id=int(data["department_id"]) if data.get("department_id") else None, amount=float(data["amount"]), description=data.get("description"), approved_by=current_user.id, status=data.get("status", "APPROVED"), payment_mode=data.get("payment_mode"), payment_date=date.fromisoformat(data["payment_date"]) if data.get("payment_date") else None)
    db.add(expense)
    db.commit()
    return JSONResponse({"message": "Expense added", "id": expense.id})


@router.get("/reports/income-statement")
def income_statement(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    income = db.query(func.coalesce(func.sum(Payment.amount), 0.0)).scalar() or 0.0
    expense = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).scalar() or 0.0
    return {"income": income, "expense": expense, "profit": income - expense}


@router.get("/reports/balance-sheet")
def balance_sheet(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    assets = db.query(func.coalesce(func.sum(Account.opening_balance), 0.0)).filter(Account.account_type == "ASSET").scalar() or 0.0
    liabilities = db.query(func.coalesce(func.sum(Account.opening_balance), 0.0)).filter(Account.account_type == "LIABILITY").scalar() or 0.0
    equity = db.query(func.coalesce(func.sum(Account.opening_balance), 0.0)).filter(Account.account_type == "EQUITY").scalar() or 0.0
    return {"assets": assets, "liabilities": liabilities, "equity": equity}
