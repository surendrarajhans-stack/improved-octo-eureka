from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import record_audit
from app.database import get_db
from app.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    existing_user = db.scalar(select(models.User).where(models.User.email == payload.email))
    if existing_user and existing_user.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
        role=models.Role.FAMILY_MEMBER,
        phone=payload.phone,
    )
    db.add(user)
    db.flush()
    record_audit(
        db, actor_user_id=user.id, action="signup", entity_type="user", entity_id=str(user.id)
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> schemas.TokenResponse:
    user = db.scalar(
        select(models.User).where(
            models.User.email == payload.email, models.User.deleted_at.is_(None)
        )
    )
    if not user or not verify_password(payload.password, user.password_hash):
        record_audit(
            db,
            actor_user_id=user.id if user else None,
            action="login_failed",
            entity_type="auth",
            entity_id=payload.email,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.email)
    record_audit(
        db, actor_user_id=user.id, action="login", entity_type="auth", entity_id=str(user.id)
    )
    db.commit()
    return schemas.TokenResponse(access_token=token)
