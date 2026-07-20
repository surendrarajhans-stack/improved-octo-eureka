from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def _resolve_user(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id), User.is_deleted.is_(False)).first()


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = _resolve_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("access_token")
    return _resolve_user(token, db)


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/auth/login"}, detail="Authentication required")
    return user
