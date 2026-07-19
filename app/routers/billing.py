from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import record_audit
from app.database import get_db
from app.deps import CurrentUser, ensure_resident_access, require_roles
from app.enums import MedicationAdministrationStatus, Role, TaskStatus

router = APIRouter(tags=["billing", "dashboard", "audit"])


def serialize_invoice(db: Session, invoice: models.Invoice) -> schemas.InvoiceRead:
    line_items = list(
        db.scalars(
            select(models.InvoiceLineItem).where(models.InvoiceLineItem.invoice_id == invoice.id)
        )
    )
    payments = list(
        db.scalars(select(models.Payment).where(models.Payment.invoice_id == invoice.id))
    )
    total_amount = round(sum(item.amount for item in line_items), 2)
    paid_amount = round(sum(payment.amount for payment in payments), 2)
    balance = round(total_amount - paid_amount, 2)
    return schemas.InvoiceRead(
        id=invoice.id,
        resident_id=invoice.resident_id,
        payer_id=invoice.payer_id,
        invoice_month=invoice.invoice_month,
        due_date=invoice.due_date,
        status=invoice.status,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        total_amount=total_amount,
        paid_amount=paid_amount,
        balance=balance,
        line_items=[
            {"description": item.description, "amount": item.amount} for item in line_items
        ],
        payments=[
            {
                "id": payment.id,
                "amount": payment.amount,
                "paid_at": payment.paid_at,
                "reference": payment.reference,
            }
            for payment in payments
        ],
    )


@router.post("/billing/payers", status_code=status.HTTP_201_CREATED)
def create_payer(
    payload: schemas.PayerCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> dict:
    payer = models.Payer(**payload.model_dump())
    db.add(payer)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="payer_created",
        entity_type="payer",
        entity_id=str(payer.id),
    )
    db.commit()
    return {"id": payer.id, **payload.model_dump()}


@router.post(
    "/billing/invoices", response_model=schemas.InvoiceRead, status_code=status.HTTP_201_CREATED
)
def create_invoice(
    payload: schemas.InvoiceCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> schemas.InvoiceRead:
    ensure_resident_access(db, current_user, payload.resident_id)
    if not db.get(models.Payer, payload.payer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payer not found")
    invoice = models.Invoice(
        resident_id=payload.resident_id,
        payer_id=payload.payer_id,
        invoice_month=payload.invoice_month,
        due_date=payload.due_date,
    )
    db.add(invoice)
    db.flush()
    db.add_all(
        [
            models.InvoiceLineItem(
                invoice_id=invoice.id, description=item.description, amount=item.amount
            )
            for item in payload.line_items
        ]
    )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="invoice_created",
        entity_type="invoice",
        entity_id=str(invoice.id),
    )
    db.commit()
    db.refresh(invoice)
    return serialize_invoice(db, invoice)


@router.get("/billing/invoices/{invoice_id}", response_model=schemas.InvoiceRead)
def get_invoice(
    invoice_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> schemas.InvoiceRead:
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    ensure_resident_access(db, current_user, invoice.resident_id)
    if current_user.role not in {
        Role.ADMIN,
        Role.ACCOUNTANT,
        Role.FAMILY_MEMBER,
        Role.RECEPTIONIST,
    }:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invoice access denied")
    return serialize_invoice(db, invoice)


@router.post("/billing/invoices/{invoice_id}/payments", response_model=schemas.InvoiceRead)
def record_payment(
    invoice_id: int,
    payload: schemas.PaymentCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> schemas.InvoiceRead:
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    payment = models.Payment(
        invoice_id=invoice_id,
        amount=payload.amount,
        paid_at=payload.paid_at or datetime.now(timezone.utc),
        reference=payload.reference,
        received_by_user_id=current_user.id,
    )
    db.add(payment)
    db.flush()
    invoice_snapshot = serialize_invoice(db, invoice)
    invoice.status = "paid" if invoice_snapshot.balance <= 0 else "partial"
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="payment_recorded",
        entity_type="invoice",
        entity_id=str(invoice.id),
    )
    db.commit()
    db.refresh(invoice)
    return serialize_invoice(db, invoice)


@router.get("/billing/statements/monthly", response_model=None)
def monthly_statement(
    year: int,
    month: int,
    current_user: CurrentUser,
    resident_id: int | None = None,
    csv_export: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Response | list[dict]:
    invoice_month = f"{year:04d}-{month:02d}"
    query = select(models.Invoice).where(models.Invoice.invoice_month == invoice_month)
    if resident_id:
        ensure_resident_access(db, current_user, resident_id)
        query = query.where(models.Invoice.resident_id == resident_id)
    elif current_user.role == Role.FAMILY_MEMBER:
        allowed_ids = list(
            db.scalars(
                select(models.FamilyLink.resident_id).where(
                    models.FamilyLink.user_id == current_user.id
                )
            )
        )
        query = query.where(models.Invoice.resident_id.in_(allowed_ids or [-1]))
    elif current_user.role not in {Role.ADMIN, Role.ACCOUNTANT, Role.RECEPTIONIST}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Statement access denied")
    invoices = [
        serialize_invoice(db, invoice) for invoice in db.scalars(query.order_by(models.Invoice.id))
    ]
    rows = [invoice.model_dump() for invoice in invoices]
    if not csv_export:
        return rows
    lines = ["invoice_id,resident_id,invoice_month,total_amount,paid_amount,balance,status"]
    for row in rows:
        lines.append(
            f"{row['id']},{row['resident_id']},{row['invoice_month']},{row['total_amount']},{row['paid_amount']},{row['balance']},{row['status']}"
        )
    return Response(content="\n".join(lines), media_type="text/csv")


@router.get("/dashboard/admin")
def admin_dashboard(
    _: models.User = Depends(require_roles(Role.ADMIN, Role.ACCOUNTANT, Role.NURSE)),
    db: Session = Depends(get_db),
) -> dict:
    occupancy = db.scalar(
        select(func.count())
        .select_from(models.Resident)
        .where(models.Resident.deleted_at.is_(None), models.Resident.status == "active")
    )
    incidents_open = db.scalar(
        select(func.count())
        .select_from(models.IncidentReport)
        .where(models.IncidentReport.resolved.is_(False))
    )
    med_total = db.scalar(select(func.count()).select_from(models.MedicationAdministration)) or 0
    med_completed = (
        db.scalar(
            select(func.count())
            .select_from(models.MedicationAdministration)
            .where(
                models.MedicationAdministration.status
                == MedicationAdministrationStatus.ADMINISTERED
            )
        )
        or 0
    )
    overdue_tasks = db.scalar(
        select(func.count())
        .select_from(models.TaskBoardItem)
        .where(
            models.TaskBoardItem.status != TaskStatus.DONE,
            models.TaskBoardItem.due_at.is_not(None),
            models.TaskBoardItem.due_at < datetime.now(timezone.utc),
        )
    )
    invoices = list(db.scalars(select(models.Invoice)))
    receivables = round(sum(serialize_invoice(db, invoice).balance for invoice in invoices), 2)
    return {
        "occupancy": occupancy,
        "open_incidents": incidents_open,
        "med_pass_completion_rate": round((med_completed / med_total) * 100, 2) if med_total else 0,
        "overdue_tasks": overdue_tasks,
        "receivables": receivables,
    }


@router.get("/audit-logs", response_model=list[schemas.AuditLogRead])
def list_audit_logs(
    _: models.User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> list[models.AuditLog]:
    return list(db.scalars(select(models.AuditLog).order_by(models.AuditLog.created_at.desc())))
