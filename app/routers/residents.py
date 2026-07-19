from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import record_audit
from app.database import get_db
from app.deps import CurrentUser, ensure_resident_access, get_resident_or_404, require_roles
from app.enums import ResidentStatus, Role

router = APIRouter(prefix="/residents", tags=["residents"])
STAFF_ROLES = (Role.ADMIN, Role.DOCTOR, Role.NURSE, Role.CAREGIVER, Role.RECEPTIONIST)


@router.post("", response_model=schemas.ResidentRead, status_code=status.HTTP_201_CREATED)
def create_resident(
    payload: schemas.ResidentCreate,
    current_user: models.User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
) -> models.Resident:
    resident = models.Resident(status=ResidentStatus.ACTIVE, **payload.model_dump())
    db.add(resident)
    db.flush()
    db.add(
        models.ResidentStatusHistory(
            resident_id=resident.id,
            previous_status=None,
            new_status=ResidentStatus.ACTIVE,
            reason="Resident created",
            changed_by_user_id=current_user.id,
        )
    )
    if resident.room_number and resident.bed_number:
        db.add(
            models.RoomAssignmentHistory(
                resident_id=resident.id,
                room_number=resident.room_number,
                bed_number=resident.bed_number,
                assigned_by_user_id=current_user.id,
            )
        )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="resident_created",
        entity_type="resident",
        entity_id=str(resident.id),
    )
    db.commit()
    db.refresh(resident)
    return resident


@router.get("", response_model=list[schemas.ResidentRead])
def list_residents(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[models.Resident]:
    query = (
        select(models.Resident)
        .where(models.Resident.deleted_at.is_(None))
        .order_by(models.Resident.id)
    )
    residents = list(db.scalars(query))
    if current_user.role == Role.FAMILY_MEMBER:
        allowed_ids = {
            resident_id
            for resident_id in db.scalars(
                select(models.FamilyLink.resident_id).where(
                    models.FamilyLink.user_id == current_user.id
                )
            )
        }
        return [resident for resident in residents if resident.id in allowed_ids]
    return residents


@router.get("/{resident_id}", response_model=schemas.ResidentRead)
def get_resident(
    resident_id: int, current_user: CurrentUser, db: Session = Depends(get_db)
) -> models.Resident:
    return ensure_resident_access(db, current_user, resident_id)


@router.patch("/{resident_id}", response_model=schemas.ResidentRead)
def update_resident(
    resident_id: int,
    payload: schemas.ResidentUpdate,
    current_user: models.User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
) -> models.Resident:
    resident = get_resident_or_404(db, resident_id)
    room_change = False
    old_room, old_bed = resident.room_number, resident.bed_number
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field in {"room_number", "bed_number"} and value != getattr(resident, field):
            room_change = True
        setattr(resident, field, value)
    if room_change and resident.room_number and resident.bed_number:
        active_room_assignment = db.scalar(
            select(models.RoomAssignmentHistory)
            .where(
                models.RoomAssignmentHistory.resident_id == resident.id,
                models.RoomAssignmentHistory.assigned_to.is_(None),
            )
            .order_by(models.RoomAssignmentHistory.id.desc())
        )
        if active_room_assignment:
            active_room_assignment.assigned_to = datetime.now(timezone.utc)
        db.add(
            models.RoomAssignmentHistory(
                resident_id=resident.id,
                room_number=resident.room_number,
                bed_number=resident.bed_number,
                assigned_by_user_id=current_user.id,
            )
        )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="resident_updated",
        entity_type="resident",
        entity_id=str(resident.id),
        details={
            "from_room": old_room,
            "from_bed": old_bed,
            "to_room": resident.room_number,
            "to_bed": resident.bed_number,
        },
    )
    db.commit()
    db.refresh(resident)
    return resident


@router.delete("/{resident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resident(
    resident_id: int,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.RECEPTIONIST)),
    db: Session = Depends(get_db),
) -> None:
    resident = get_resident_or_404(db, resident_id)
    resident.deleted_at = datetime.now(timezone.utc)
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="resident_deleted",
        entity_type="resident",
        entity_id=str(resident.id),
    )
    db.commit()


@router.post("/{resident_id}/status", response_model=schemas.ResidentRead)
def change_status(
    resident_id: int,
    payload: schemas.StatusChangeRequest,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.DOCTOR, Role.NURSE)),
    db: Session = Depends(get_db),
) -> models.Resident:
    resident = get_resident_or_404(db, resident_id)
    previous_status = resident.status
    resident.status = payload.new_status
    db.add(
        models.ResidentStatusHistory(
            resident_id=resident.id,
            previous_status=previous_status,
            new_status=payload.new_status,
            reason=payload.reason,
            changed_by_user_id=current_user.id,
        )
    )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="resident_status_changed",
        entity_type="resident",
        entity_id=str(resident.id),
        details={"from": previous_status, "to": payload.new_status, "reason": payload.reason},
    )
    db.commit()
    db.refresh(resident)
    return resident


@router.post("/{resident_id}/room-assignments", response_model=schemas.ResidentRead)
def assign_room(
    resident_id: int,
    payload: schemas.RoomAssignmentRequest,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.RECEPTIONIST, Role.NURSE)),
    db: Session = Depends(get_db),
) -> models.Resident:
    resident = get_resident_or_404(db, resident_id)
    active_room_assignment = db.scalar(
        select(models.RoomAssignmentHistory)
        .where(
            models.RoomAssignmentHistory.resident_id == resident.id,
            models.RoomAssignmentHistory.assigned_to.is_(None),
        )
        .order_by(models.RoomAssignmentHistory.id.desc())
    )
    if active_room_assignment:
        active_room_assignment.assigned_to = datetime.now(timezone.utc)
    resident.room_number = payload.room_number
    resident.bed_number = payload.bed_number
    db.add(
        models.RoomAssignmentHistory(
            resident_id=resident.id,
            room_number=payload.room_number,
            bed_number=payload.bed_number,
            assigned_by_user_id=current_user.id,
        )
    )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="room_assigned",
        entity_type="resident",
        entity_id=str(resident.id),
    )
    db.commit()
    db.refresh(resident)
    return resident


@router.post("/{resident_id}/family-links", status_code=status.HTTP_201_CREATED)
def add_family_link(
    resident_id: int,
    payload: schemas.FamilyLinkRequest,
    current_user: models.User = Depends(require_roles(Role.ADMIN, Role.RECEPTIONIST)),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    resident = get_resident_or_404(db, resident_id)
    family_user = db.get(models.User, payload.user_id)
    if not family_user or family_user.role != Role.FAMILY_MEMBER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Target user must be a family member"
        )
    link_exists = db.scalar(
        select(models.FamilyLink).where(
            models.FamilyLink.user_id == family_user.id,
            models.FamilyLink.resident_id == resident.id,
        )
    )
    if link_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Family link already exists"
        )
    db.add(
        models.FamilyLink(
            user_id=family_user.id, resident_id=resident.id, relationship=payload.relationship
        )
    )
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="family_link_added",
        entity_type="resident",
        entity_id=str(resident.id),
    )
    db.commit()
    return {"status": "linked"}
