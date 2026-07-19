from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.enums import (
    IncidentSeverity,
    MedicationAdministrationStatus,
    NoteVisibility,
    NotificationType,
    PayerCategory,
    ResidentStatus,
    Role,
    TaskStatus,
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Resident(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "residents"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    date_of_birth: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(50))
    status: Mapped[ResidentStatus] = mapped_column(
        Enum(ResidentStatus, native_enum=False), index=True
    )
    emergency_contacts: Mapped[list] = mapped_column(JSON, default=list)
    allergies: Mapped[list] = mapped_column(JSON, default=list)
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    preferred_pharmacy: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_physician: Mapped[str | None] = mapped_column(String(255), nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bed_number: Mapped[str | None] = mapped_column(String(50), nullable=True)


class ResidentStatusHistory(Base):
    __tablename__ = "resident_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    previous_status: Mapped[ResidentStatus | None] = mapped_column(
        Enum(ResidentStatus, native_enum=False), nullable=True
    )
    new_status: Mapped[ResidentStatus] = mapped_column(Enum(ResidentStatus, native_enum=False))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RoomAssignmentHistory(Base):
    __tablename__ = "room_assignment_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    room_number: Mapped[str] = mapped_column(String(50))
    bed_number: Mapped[str] = mapped_column(String(50))
    assigned_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    assigned_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class CarePlan(TimestampMixin, Base):
    __tablename__ = "care_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    goals: Mapped[list] = mapped_column(JSON, default=list)
    tasks: Mapped[list] = mapped_column(JSON, default=list)
    responsible_staff_user_ids: Mapped[list] = mapped_column(JSON, default=list)


class VitalRecord(TimestampMixin, Base):
    __tablename__ = "vital_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    blood_pressure: Mapped[str | None] = mapped_column(String(50), nullable=True)
    heart_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    spo2: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    recorded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class MedicationOrder(TimestampMixin, Base):
    __tablename__ = "medication_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    medication_name: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str] = mapped_column(String(100))
    route: Mapped[str] = mapped_column(String(50))
    schedule_time: Mapped[str] = mapped_column(String(20))
    prn: Mapped[bool] = mapped_column(Boolean, default=False)
    indication: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    ordered_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class MedicationAdministration(TimestampMixin, Base):
    __tablename__ = "medication_administrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    medication_order_id: Mapped[int] = mapped_column(ForeignKey("medication_orders.id"), index=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    status: Mapped[MedicationAdministrationStatus] = mapped_column(
        Enum(MedicationAdministrationStatus, native_enum=False)
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    administered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class ProgressNote(TimestampMixin, Base):
    __tablename__ = "progress_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    visibility: Mapped[NoteVisibility] = mapped_column(Enum(NoteVisibility, native_enum=False))
    content: Mapped[str] = mapped_column(Text)


class IncidentReport(TimestampMixin, Base):
    __tablename__ = "incident_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int | None] = mapped_column(
        ForeignKey("residents.id"), nullable=True, index=True
    )
    reported_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, native_enum=False), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    follow_up_actions: Mapped[list] = mapped_column(JSON, default=list)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class Shift(TimestampMixin, Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    role_name: Mapped[str] = mapped_column(String(100))


class AttendanceRecord(TimestampMixin, Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("shifts.id"), nullable=True)
    check_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TaskBoardItem(TimestampMixin, Base):
    __tablename__ = "task_board_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int | None] = mapped_column(
        ForeignKey("residents.id"), nullable=True, index=True
    )
    assigned_to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False), default=TaskStatus.TODO
    )


class Payer(TimestampMixin, Base):
    __tablename__ = "payers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    category: Mapped[PayerCategory] = mapped_column(Enum(PayerCategory, native_enum=False))
    configuration: Mapped[dict] = mapped_column(JSON, default=dict)


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    payer_id: Mapped[int] = mapped_column(ForeignKey("payers.id"))
    invoice_month: Mapped[str] = mapped_column(String(7), index=True)
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="open")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class FamilyLink(TimestampMixin, Base):
    __tablename__ = "family_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    relationship: Mapped[str] = mapped_column(String(100))


class FamilyUpdate(TimestampMixin, Base):
    __tablename__ = "family_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int | None] = mapped_column(
        ForeignKey("residents.id"), nullable=True, index=True
    )
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)


class InventoryItem(TimestampMixin, Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    stock: Mapped[float] = mapped_column(Float, default=0)
    reorder_threshold: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(50), default="units")


class InventoryUsage(TimestampMixin, Base):
    __tablename__ = "inventory_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), index=True)
    resident_id: Mapped[int | None] = mapped_column(ForeignKey("residents.id"), nullable=True)
    quantity_used: Mapped[float] = mapped_column(Float)
    recorded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id"), index=True)
    appointment_type: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(255))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    transport_required: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str] = mapped_column(String(100), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
