import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import record_audit
from app.database import get_db
from app.deps import CurrentUser, ensure_resident_access, get_resident_or_404, require_roles
from app.enums import IncidentSeverity, NoteVisibility, NotificationType, Role

router = APIRouter(tags=["clinical"])
CLINICAL_ROLES = (Role.ADMIN, Role.DOCTOR, Role.NURSE, Role.CAREGIVER)


@router.post("/residents/{resident_id}/care-plans", status_code=status.HTTP_201_CREATED)
def create_care_plan(
    resident_id: int,
    payload: schemas.CarePlanCreate,
    current_user: models.User = Depends(require_roles(*CLINICAL_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    ensure_resident_access(db, current_user, resident_id)
    care_plan = models.CarePlan(resident_id=resident_id, **payload.model_dump())
    db.add(care_plan)
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="care_plan_created",
        entity_type="resident",
        entity_id=str(resident_id),
    )
    db.commit()
    db.refresh(care_plan)
    return {"id": care_plan.id, **payload.model_dump()}


@router.post(
    "/residents/{resident_id}/vitals",
    response_model=schemas.VitalRead,
    status_code=status.HTTP_201_CREATED,
)
def chart_vitals(
    resident_id: int,
    payload: schemas.VitalCreate,
    current_user: models.User = Depends(require_roles(*CLINICAL_ROLES)),
    db: Session = Depends(get_db),
) -> models.VitalRecord:
    ensure_resident_access(db, current_user, resident_id)
    vital = models.VitalRecord(
        resident_id=resident_id,
        recorded_by_user_id=current_user.id,
        recorded_at=payload.recorded_at or datetime.now(timezone.utc),
        **payload.model_dump(exclude={"recorded_at"}),
    )
    db.add(vital)
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="vitals_recorded",
        entity_type="resident",
        entity_id=str(resident_id),
    )
    db.commit()
    db.refresh(vital)
    return vital


@router.get("/residents/{resident_id}/vitals", response_model=list[schemas.VitalRead])
def list_vitals(
    resident_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[models.VitalRecord]:
    ensure_resident_access(db, current_user, resident_id)
    vitals = db.scalars(
        select(models.VitalRecord)
        .where(models.VitalRecord.resident_id == resident_id)
        .order_by(models.VitalRecord.recorded_at.desc())
    )
    return list(vitals)


@router.post("/residents/{resident_id}/medication-orders", status_code=status.HTTP_201_CREATED)
def create_medication_order(
    resident_id: int,
    payload: schemas.MedicationOrderCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.DOCTOR, Role.NURSE)),
    db: Session = Depends(get_db),
) -> dict:
    ensure_resident_access(db, current_user, resident_id)
    order = models.MedicationOrder(
        resident_id=resident_id, ordered_by_user_id=current_user.id, **payload.model_dump()
    )
    db.add(order)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="medication_order_created",
        entity_type="medication_order",
        entity_id=str(order.id),
    )
    db.commit()
    db.refresh(order)
    return {"id": order.id, **payload.model_dump(), "active": order.active}


@router.post(
    "/medication-orders/{order_id}/administrations",
    response_model=schemas.MedicationAdministrationRead,
    status_code=status.HTTP_201_CREATED,
)
def administer_medication(
    order_id: int,
    payload: schemas.MedicationAdministrationCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.NURSE, Role.CAREGIVER)),
    db: Session = Depends(get_db),
) -> models.MedicationAdministration:
    order = db.get(models.MedicationOrder, order_id)
    if not order or not order.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medication order not found"
        )
    if order.resident_id != payload.resident_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Resident/order mismatch"
        )
    administration = models.MedicationAdministration(
        medication_order_id=order_id,
        recorded_by_user_id=current_user.id,
        administered_at=payload.administered_at,
        **payload.model_dump(exclude={"administered_at"}),
    )
    db.add(administration)
    if payload.status != "administered":
        db.add(
            models.Notification(
                user_id=order.ordered_by_user_id,
                notification_type=NotificationType.DUE_MED,
                title=f"Medication {payload.status}",
                body=(
                    f"{order.medication_name} for resident #{order.resident_id} "
                    f"was {payload.status}."
                ),
            )
        )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="medication_administered",
        entity_type="medication_order",
        entity_id=str(order_id),
        details={"status": payload.status, "resident_id": payload.resident_id},
    )
    db.commit()
    db.refresh(administration)
    return administration


@router.get("/residents/{resident_id}/mar")
def get_mar(
    resident_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[dict]:
    ensure_resident_access(db, current_user, resident_id)
    orders = list(
        db.scalars(
            select(models.MedicationOrder).where(
                models.MedicationOrder.resident_id == resident_id,
                models.MedicationOrder.active.is_(True),
            )
        )
    )
    administrations = list(
        db.scalars(
            select(models.MedicationAdministration).where(
                models.MedicationAdministration.resident_id == resident_id
            )
        )
    )
    by_order: dict[int, list[dict]] = {}
    for administration in administrations:
        by_order.setdefault(administration.medication_order_id, []).append(
            {
                "id": administration.id,
                "status": administration.status,
                "scheduled_for": administration.scheduled_for,
                "administered_at": administration.administered_at,
                "reason_code": administration.reason_code,
            }
        )
    return [
        {
            "order_id": order.id,
            "medication_name": order.medication_name,
            "dosage": order.dosage,
            "route": order.route,
            "schedule_time": order.schedule_time,
            "prn": order.prn,
            "administrations": by_order.get(order.id, []),
        }
        for order in orders
    ]


@router.post("/residents/{resident_id}/notes", status_code=status.HTTP_201_CREATED)
def add_progress_note(
    resident_id: int,
    payload: schemas.ProgressNoteCreate,
    current_user: models.User = Depends(require_roles(*CLINICAL_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    ensure_resident_access(db, current_user, resident_id)
    note = models.ProgressNote(
        resident_id=resident_id, author_user_id=current_user.id, **payload.model_dump()
    )
    db.add(note)
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="progress_note_added",
        entity_type="resident",
        entity_id=str(resident_id),
    )
    db.commit()
    db.refresh(note)
    return {"id": note.id, **payload.model_dump()}


@router.get("/residents/{resident_id}/notes")
def list_progress_notes(
    resident_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[dict]:
    ensure_resident_access(db, current_user, resident_id)
    query = select(models.ProgressNote).where(models.ProgressNote.resident_id == resident_id)
    if current_user.role == Role.FAMILY_MEMBER:
        query = query.where(models.ProgressNote.visibility == NoteVisibility.FAMILY_APPROVED)
    elif current_user.role in {Role.CAREGIVER, Role.NURSE}:
        query = query.where(models.ProgressNote.visibility != NoteVisibility.PRIVATE)
    notes = db.scalars(query.order_by(models.ProgressNote.created_at.desc()))
    return [
        {
            "id": note.id,
            "content": note.content,
            "visibility": note.visibility,
            "created_at": note.created_at,
        }
        for note in notes
    ]


@router.post("/incidents", status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: schemas.IncidentCreate,
    current_user: models.User = Depends(require_roles(*CLINICAL_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    if payload.resident_id is not None:
        get_resident_or_404(db, payload.resident_id)
    incident = models.IncidentReport(reported_by_user_id=current_user.id, **payload.model_dump())
    db.add(incident)
    db.flush()
    if payload.severity in {IncidentSeverity.HIGH, IncidentSeverity.CRITICAL}:
        admin_ids = list(
            db.scalars(
                select(models.User.id).where(
                    models.User.role.in_([Role.ADMIN, Role.DOCTOR]),
                    models.User.deleted_at.is_(None),
                )
            )
        )
        db.add_all(
            [
                models.Notification(
                    user_id=user_id,
                    notification_type=NotificationType.INCIDENT,
                    title=f"{payload.severity.title()} incident reported",
                    body=payload.description,
                )
                for user_id in admin_ids
            ]
        )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="incident_reported",
        entity_type="incident",
        entity_id=str(incident.id),
    )
    db.commit()
    return {"id": incident.id, **payload.model_dump()}


@router.get("/clinical/due-medications")
def due_medications(
    current_user: models.User = Depends(
        require_roles(Role.ADMIN, Role.DOCTOR, Role.NURSE, Role.CAREGIVER)
    ),
    db: Session = Depends(get_db),
) -> list[dict]:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=12)
    today_prefix = now.strftime("%Y-%m-%d")
    orders = list(
        db.scalars(select(models.MedicationOrder).where(models.MedicationOrder.active.is_(True)))
    )
    due_items: list[dict] = []
    for order in orders:
        already_done = db.scalar(
            select(models.MedicationAdministration).where(
                and_(
                    models.MedicationAdministration.medication_order_id == order.id,
                    models.MedicationAdministration.status == "administered",
                    models.MedicationAdministration.scheduled_for >= window_start,
                )
            )
        )
        if not already_done:
            due_items.append(
                {
                    "medication_order_id": order.id,
                    "resident_id": order.resident_id,
                    "medication_name": order.medication_name,
                    "schedule_time": f"{today_prefix}T{order.schedule_time}:00",
                }
            )
    return due_items


@router.get("/reports/incidents", response_model=None)
def incident_report(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    csv_export: bool = Query(default=False),
    _: models.User = Depends(require_roles(Role.ADMIN, Role.DOCTOR, Role.NURSE)),
    db: Session = Depends(get_db),
) -> Response | list[dict]:
    query = select(models.IncidentReport)
    if start:
        query = query.where(models.IncidentReport.created_at >= start)
    if end:
        query = query.where(models.IncidentReport.created_at <= end)
    incidents = list(db.scalars(query.order_by(models.IncidentReport.created_at.desc())))
    rows = [
        {
            "id": item.id,
            "resident_id": item.resident_id,
            "severity": item.severity,
            "description": item.description,
            "created_at": item.created_at.isoformat(),
        }
        for item in incidents
    ]
    if not csv_export:
        return rows
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=["id", "resident_id", "severity", "description", "created_at"]
    )
    writer.writeheader()
    writer.writerows(rows)
    return Response(content=buffer.getvalue(), media_type="text/csv")
