from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.enums import Role
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


DBSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DBSession, token: Annotated[str, Depends(oauth2_scheme)]) -> models.User:
    email = decode_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication"
        )
    user = db.scalar(
        select(models.User).where(models.User.email == email, models.User.deleted_at.is_(None))
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[models.User], models.User]:
    def dependency(current_user: CurrentUser) -> models.User:
        if roles and current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return dependency


def get_resident_or_404(db: Session, resident_id: int) -> models.Resident:
    resident = db.get(models.Resident, resident_id)
    if not resident or resident.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")
    return resident


def ensure_resident_access(
    db: Session, current_user: models.User, resident_id: int
) -> models.Resident:
    resident = get_resident_or_404(db, resident_id)
    if current_user.role == Role.FAMILY_MEMBER:
        link = db.scalar(
            select(models.FamilyLink).where(
                models.FamilyLink.user_id == current_user.id,
                models.FamilyLink.resident_id == resident_id,
            )
        )
        if not link:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Resident access denied"
            )
    return resident
