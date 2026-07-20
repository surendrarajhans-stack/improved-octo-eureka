from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.permissions import UserRole


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    role: UserRole = UserRole.GUEST
    hospital_id: int | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    hospital_id: int | None = None
    username: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    role: UserRole
    is_active: bool
    last_login: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
