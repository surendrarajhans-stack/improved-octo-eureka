from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer


class TimestampMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    created_by = Column(Integer, nullable=True)
