from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base
from app.models.base import TimestampMixin


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    type = Column(String(20), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING")
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    metadata_json = Column(Text, nullable=True)


class NotificationTemplate(TimestampMixin, Base):
    __tablename__ = "notification_templates"

    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)
    subject = Column(String(255), nullable=True)
    body_template = Column(Text, nullable=False)
    variables_json = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
