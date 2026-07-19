from enum import StrEnum


class Role(StrEnum):
    ADMIN = "Admin"
    DOCTOR = "Doctor"
    NURSE = "Nurse"
    CAREGIVER = "Caregiver"
    RECEPTIONIST = "Receptionist"
    ACCOUNTANT = "Accountant"
    FAMILY_MEMBER = "FamilyMember"


class ResidentStatus(StrEnum):
    ACTIVE = "active"
    HOSPITALIZED = "hospitalized"
    DISCHARGED = "discharged"
    DECEASED = "deceased"


class NoteVisibility(StrEnum):
    STAFF = "staff"
    CLINICAL = "clinical"
    FAMILY_APPROVED = "family_approved"
    PRIVATE = "private"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MedicationAdministrationStatus(StrEnum):
    ADMINISTERED = "administered"
    MISSED = "missed"
    REFUSED = "refused"


class PayerCategory(StrEnum):
    PRIVATE = "private"
    INSURANCE = "insurance"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    OTHER = "other"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class NotificationType(StrEnum):
    DUE_MED = "due_med"
    INCIDENT = "incident"
    SHIFT_REMINDER = "shift_reminder"
    MESSAGE = "message"
