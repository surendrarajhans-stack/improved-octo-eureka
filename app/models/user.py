from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.permissions import UserRole
from app.database import Base
from app.models.base import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.GUEST)
    is_active = Column(Boolean, default=True)
    profile_photo = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)

    audit_logs = relationship("AuditLog", back_populates="user")


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = relationship("Permission", back_populates="role_rel", cascade="all, delete-orphan")


class Permission(TimestampMixin, Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    module = Column(String(100), nullable=False)
    can_create = Column(Boolean, default=False)
    can_read = Column(Boolean, default=True)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_approve = Column(Boolean, default=False)
    can_print = Column(Boolean, default=False)
    can_export = Column(Boolean, default=False)

    role_rel = relationship("Role", back_populates="permissions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    module = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
