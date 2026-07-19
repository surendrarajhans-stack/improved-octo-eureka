from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: Role = Role.FAMILY_MEMBER
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    password: str | None = Field(default=None, min_length=8)


class UserRead(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    role: Role
    phone: str | None
    is_active: bool


class ResidentCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    emergency_contacts: list[dict] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    preferred_pharmacy: str | None = None
    primary_physician: str | None = None
    room_number: str | None = None
    bed_number: str | None = None


class ResidentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    emergency_contacts: list[dict] | None = None
    allergies: list[str] | None = None
    conditions: list[str] | None = None
    preferred_pharmacy: str | None = None
    primary_physician: str | None = None
    room_number: str | None = None
    bed_number: str | None = None


class ResidentRead(ORMModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    status: ResidentStatus
    emergency_contacts: list[dict]
    allergies: list[str]
    conditions: list[str]
    preferred_pharmacy: str | None
    primary_physician: str | None
    room_number: str | None
    bed_number: str | None


class StatusChangeRequest(BaseModel):
    new_status: ResidentStatus
    reason: str | None = None


class RoomAssignmentRequest(BaseModel):
    room_number: str
    bed_number: str


class FamilyLinkRequest(BaseModel):
    user_id: int
    relationship: str


class CarePlanCreate(BaseModel):
    goals: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    responsible_staff_user_ids: list[int] = Field(default_factory=list)


class VitalCreate(BaseModel):
    blood_pressure: str | None = None
    heart_rate: float | None = None
    temperature: float | None = None
    spo2: float | None = None
    weight: float | None = None
    recorded_at: datetime | None = None


class VitalRead(ORMModel):
    id: int
    resident_id: int
    blood_pressure: str | None
    heart_rate: float | None
    temperature: float | None
    spo2: float | None
    weight: float | None
    recorded_at: datetime
    recorded_by_user_id: int


class MedicationOrderCreate(BaseModel):
    medication_name: str
    dosage: str
    route: str
    schedule_time: str
    prn: bool = False
    indication: str | None = None


class MedicationAdministrationCreate(BaseModel):
    resident_id: int
    status: MedicationAdministrationStatus
    scheduled_for: datetime
    administered_at: datetime | None = None
    reason_code: str | None = None
    notes: str | None = None


class MedicationAdministrationRead(ORMModel):
    id: int
    medication_order_id: int
    resident_id: int
    status: MedicationAdministrationStatus
    scheduled_for: datetime
    administered_at: datetime | None
    reason_code: str | None
    notes: str | None
    recorded_by_user_id: int


class ProgressNoteCreate(BaseModel):
    visibility: NoteVisibility
    content: str


class IncidentCreate(BaseModel):
    resident_id: int | None = None
    severity: IncidentSeverity
    description: str
    follow_up_actions: list[str] = Field(default_factory=list)


class ShiftCreate(BaseModel):
    staff_user_id: int
    start_time: datetime
    end_time: datetime
    role_name: str


class AttendanceCreate(BaseModel):
    staff_user_id: int
    shift_id: int | None = None


class TaskCreate(BaseModel):
    resident_id: int | None = None
    assigned_to_user_id: int
    title: str
    description: str | None = None
    due_at: datetime | None = None
    status: TaskStatus = TaskStatus.TODO


class PayerCreate(BaseModel):
    name: str
    category: PayerCategory
    configuration: dict = Field(default_factory=dict)


class InvoiceLineItemCreate(BaseModel):
    description: str
    amount: float = Field(gt=0)


class InvoiceCreate(BaseModel):
    resident_id: int
    payer_id: int
    invoice_month: str
    due_date: date
    line_items: list[InvoiceLineItemCreate]


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    paid_at: datetime | None = None
    reference: str | None = None


class InvoiceRead(ORMModel):
    id: int
    resident_id: int
    payer_id: int
    invoice_month: str
    due_date: date
    status: str
    created_at: datetime
    updated_at: datetime
    total_amount: float
    paid_amount: float
    balance: float
    line_items: list[dict]
    payments: list[dict]


class FamilyUpdateCreate(BaseModel):
    resident_id: int
    title: str
    content: str
    approved: bool = False


class MessageCreate(BaseModel):
    resident_id: int | None = None
    recipient_user_id: int
    content: str


class InventoryItemCreate(BaseModel):
    name: str
    stock: float = Field(ge=0)
    reorder_threshold: float = Field(ge=0)
    unit: str = "units"


class InventoryUsageCreate(BaseModel):
    item_id: int
    resident_id: int | None = None
    quantity_used: float = Field(gt=0)
    note: str | None = None


class AppointmentCreate(BaseModel):
    resident_id: int
    appointment_type: str
    destination: str
    scheduled_for: datetime
    transport_required: bool = False
    notes: str | None = None


class NotificationRead(ORMModel):
    id: int
    notification_type: NotificationType
    title: str
    body: str
    read: bool
    created_at: datetime


class AuditLogRead(ORMModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str
    details: dict
    created_at: datetime
