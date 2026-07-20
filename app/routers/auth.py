from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import Role, User
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth_service import authenticate_user, create_user, generate_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = generate_token(user.username)
    return Token(access_token=access_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can register users")
    user = await create_user(db, user_data)
    return user


@router.post(
    "/register/first",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_first_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register the first admin user (only works when no users exist)."""
    result = await db.execute(select(User))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users already exist. Use /auth/register with admin token.",
        )
    user_data.role = Role.ADMIN
    user = await create_user(db, user_data)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()
