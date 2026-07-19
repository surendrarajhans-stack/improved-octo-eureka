from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import record_audit
from app.database import get_db
from app.deps import CurrentUser, ensure_resident_access, require_roles
from app.enums import NotificationType, Role

router = APIRouter(tags=["operations", "family", "communications"])


@router.post("/scheduling/shifts", status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: schemas.ShiftCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.RECEPTIONIST)),
    db: Session = Depends(get_db),
) -> dict:
    shift = models.Shift(**payload.model_dump())
    db.add(shift)
    db.flush()
    db.add(
        models.Notification(
            user_id=payload.staff_user_id,
            notification_type=NotificationType.SHIFT_REMINDER,
            title="Shift scheduled",
            body=f"Shift starts at {payload.start_time.isoformat()}",
        )
    )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="shift_created",
        entity_type="shift",
        entity_id=str(shift.id),
    )
    db.commit()
    return {"id": shift.id, **payload.model_dump()}


@router.post("/scheduling/attendance", status_code=status.HTTP_201_CREATED)
def check_in(
    payload: schemas.AttendanceCreate,
    current_user: models.User = Depends(
        require_roles(Role.ADMIN, Role.NURSE, Role.CAREGIVER, Role.DOCTOR, Role.RECEPTIONIST)
    ),
    db: Session = Depends(get_db),
) -> dict:
    if (
        current_user.role not in {Role.ADMIN, Role.RECEPTIONIST}
        and current_user.id != payload.staff_user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot check in another user"
        )
    record = models.AttendanceRecord(**payload.model_dump())
    db.add(record)
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="attendance_checked_in",
        entity_type="attendance",
        entity_id="pending",
    )
    db.commit()
    db.refresh(record)
    return {"id": record.id, "check_in_at": record.check_in_at}


@router.post("/scheduling/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: schemas.TaskCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.NURSE, Role.CAREGIVER)),
    db: Session = Depends(get_db),
) -> dict:
    if payload.resident_id is not None:
        ensure_resident_access(db, current_user, payload.resident_id)
    task = models.TaskBoardItem(**payload.model_dump())
    db.add(task)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="task_created",
        entity_type="task",
        entity_id=str(task.id),
    )
    db.commit()
    return {"id": task.id, **payload.model_dump()}


@router.get("/scheduling/tasks")
def list_tasks(current_user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    query = select(models.TaskBoardItem)
    if current_user.role in {Role.CAREGIVER, Role.NURSE, Role.DOCTOR}:
        query = query.where(models.TaskBoardItem.assigned_to_user_id == current_user.id)
    tasks = db.scalars(query.order_by(models.TaskBoardItem.created_at.desc()))
    return [
        {
            "id": item.id,
            "title": item.title,
            "status": item.status,
            "resident_id": item.resident_id,
            "due_at": item.due_at,
        }
        for item in tasks
    ]


@router.post("/family/updates", status_code=status.HTTP_201_CREATED)
def create_family_update(
    payload: schemas.FamilyUpdateCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.DOCTOR, Role.NURSE)),
    db: Session = Depends(get_db),
) -> dict:
    ensure_resident_access(db, current_user, payload.resident_id)
    update = models.FamilyUpdate(author_user_id=current_user.id, **payload.model_dump())
    db.add(update)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="family_update_created",
        entity_type="resident",
        entity_id=str(payload.resident_id),
    )
    db.commit()
    return {"id": update.id, **payload.model_dump()}


@router.get("/family/portal/updates")
def family_updates_portal(
    current_user: models.User = Depends(require_roles(Role.FAMILY_MEMBER)),
    db: Session = Depends(get_db),
) -> list[dict]:
    resident_ids = list(
        db.scalars(
            select(models.FamilyLink.resident_id).where(
                models.FamilyLink.user_id == current_user.id
            )
        )
    )
    updates = db.scalars(
        select(models.FamilyUpdate)
        .where(
            models.FamilyUpdate.resident_id.in_(resident_ids or [-1]),
            models.FamilyUpdate.approved.is_(True),
        )
        .order_by(models.FamilyUpdate.created_at.desc())
    )
    return [
        {
            "id": item.id,
            "resident_id": item.resident_id,
            "title": item.title,
            "content": item.content,
        }
        for item in updates
    ]


@router.get("/family/portal/visit-schedule")
def family_visit_schedule(
    current_user: models.User = Depends(require_roles(Role.FAMILY_MEMBER)),
    db: Session = Depends(get_db),
) -> list[dict]:
    resident_ids = list(
        db.scalars(
            select(models.FamilyLink.resident_id).where(
                models.FamilyLink.user_id == current_user.id
            )
        )
    )
    appointments = db.scalars(
        select(models.Appointment)
        .where(models.Appointment.resident_id.in_(resident_ids or [-1]))
        .order_by(models.Appointment.scheduled_for.desc())
    )
    return [
        {
            "id": item.id,
            "resident_id": item.resident_id,
            "type": item.appointment_type,
            "scheduled_for": item.scheduled_for,
        }
        for item in appointments
    ]


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    payload: schemas.MessageCreate, current_user: CurrentUser, db: Session = Depends(get_db)
) -> dict:
    if payload.resident_id is not None:
        ensure_resident_access(db, current_user, payload.resident_id)
        recipient = db.get(models.User, payload.recipient_user_id)
        if not recipient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
        if current_user.role == Role.FAMILY_MEMBER and recipient.role == Role.FAMILY_MEMBER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Family members may only message staff",
            )
    message = models.Message(sender_user_id=current_user.id, **payload.model_dump())
    db.add(message)
    db.flush()
    db.add(
        models.Notification(
            user_id=payload.recipient_user_id,
            notification_type=NotificationType.MESSAGE,
            title="New secure message",
            body=payload.content[:120],
        )
    )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="message_sent",
        entity_type="message",
        entity_id=str(message.id),
    )
    db.commit()
    return {"id": message.id, **payload.model_dump()}


@router.get("/messages")
def list_messages(current_user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    query = select(models.Message).where(
        (models.Message.sender_user_id == current_user.id)
        | (models.Message.recipient_user_id == current_user.id)
    )
    messages = db.scalars(query.order_by(models.Message.created_at.desc()))
    return [
        {
            "id": message.id,
            "resident_id": message.resident_id,
            "sender_user_id": message.sender_user_id,
            "recipient_user_id": message.recipient_user_id,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in messages
    ]


@router.post("/operations/inventory-items", status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: schemas.InventoryItemCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.NURSE)),
    db: Session = Depends(get_db),
) -> dict:
    item = models.InventoryItem(**payload.model_dump())
    db.add(item)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="inventory_item_created",
        entity_type="inventory",
        entity_id=str(item.id),
    )
    db.commit()
    return {"id": item.id, **payload.model_dump()}


@router.get("/operations/inventory-items")
def list_inventory_items(
    low_stock_only: bool = Query(default=False),
    _: models.User = Depends(require_roles(Role.ADMIN, Role.NURSE, Role.CAREGIVER)),
    db: Session = Depends(get_db),
) -> list[dict]:
    items = list(db.scalars(select(models.InventoryItem).order_by(models.InventoryItem.name)))
    if low_stock_only:
        items = [item for item in items if item.stock <= item.reorder_threshold]
    return [
        {
            "id": item.id,
            "name": item.name,
            "stock": item.stock,
            "reorder_threshold": item.reorder_threshold,
            "unit": item.unit,
        }
        for item in items
    ]


@router.post("/operations/inventory-usage", status_code=status.HTTP_201_CREATED)
def record_inventory_usage(
    payload: schemas.InventoryUsageCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.NURSE, Role.CAREGIVER)),
    db: Session = Depends(get_db),
) -> dict:
    item = db.get(models.InventoryItem, payload.item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found"
        )
    if payload.quantity_used > item.stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
    item.stock -= payload.quantity_used
    usage = models.InventoryUsage(recorded_by_user_id=current_user.id, **payload.model_dump())
    db.add(usage)
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="inventory_used",
        entity_type="inventory",
        entity_id=str(item.id),
    )
    db.commit()
    db.refresh(usage)
    return {"id": usage.id, "remaining_stock": item.stock}


@router.post("/operations/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: schemas.AppointmentCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.RECEPTIONIST, Role.NURSE)),
    db: Session = Depends(get_db),
) -> dict:
    ensure_resident_access(db, current_user, payload.resident_id)
    appointment = models.Appointment(**payload.model_dump())
    db.add(appointment)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="appointment_created",
        entity_type="appointment",
        entity_id=str(appointment.id),
    )
    db.commit()
    return {"id": appointment.id, **payload.model_dump()}


@router.get("/notifications", response_model=list[schemas.NotificationRead])
def list_notifications(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[models.Notification]:
    notifications = list(
        db.scalars(
            select(models.Notification)
            .where(models.Notification.user_id == current_user.id)
            .order_by(models.Notification.created_at.desc())
        )
    )
    if current_user.role in {Role.NURSE, Role.CAREGIVER, Role.DOCTOR, Role.ADMIN}:
        due_orders = list(
            db.scalars(
                select(models.MedicationOrder).where(models.MedicationOrder.active.is_(True))
            )
        )
        twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)
        for order in due_orders:
            recent_admin = db.scalar(
                select(models.MedicationAdministration).where(
                    models.MedicationAdministration.medication_order_id == order.id,
                    models.MedicationAdministration.scheduled_for >= twelve_hours_ago,
                )
            )
            if not recent_admin:
                notifications.append(
                    models.Notification(
                        id=-(order.id),
                        user_id=current_user.id,
                        notification_type=NotificationType.DUE_MED,
                        title="Medication due",
                        body=f"{order.medication_name} is due for resident #{order.resident_id}",
                        read=False,
                        created_at=datetime.now(timezone.utc),
                    )
                )
    return notifications
