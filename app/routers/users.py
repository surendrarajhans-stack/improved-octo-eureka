from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import record_audit
from app.database import get_db
from app.deps import CurrentUser, require_roles
from app.enums import Role
from app.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.UserRead, status_code=201)
def create_user(
    payload: schemas.UserCreate,
    current_user: models.User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> models.User:
    existing_user = db.scalar(select(models.User).where(models.User.email == payload.email))
    if existing_user and existing_user.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        phone=payload.phone,
    )
    db.add(user)
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="user_created",
        entity_type="user",
        entity_id=str(user.id),
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=schemas.UserRead)
def read_me(current_user: CurrentUser) -> models.User:
    return current_user


@router.patch("/me", response_model=schemas.UserRead)
def update_me(
    payload: schemas.UserUpdate, current_user: CurrentUser, db: Session = Depends(get_db)
) -> models.User:
    for field, value in payload.model_dump(exclude_unset=True, exclude={"password"}).items():
        setattr(current_user, field, value)
    if payload.password:
        current_user.password_hash = get_password_hash(payload.password)
    record_audit(
        db,
        actor_user_id=current_user.id,
        action="profile_updated",
        entity_type="user",
        entity_id=str(current_user.id),
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("", response_model=list[schemas.UserRead])
def list_users(
    _: models.User = Depends(require_roles(Role.ADMIN, Role.RECEPTIONIST)),
    db: Session = Depends(get_db),
) -> list[models.User]:
    return list(
        db.scalars(
            select(models.User).where(models.User.deleted_at.is_(None)).order_by(models.User.id)
        )
    )
