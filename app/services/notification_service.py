from datetime import datetime

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.patient import Patient


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, user_id: int | None, type: str, subject: str, message: str, patient_id: int | None = None):
        notification = Notification(
            user_id=user_id,
            patient_id=patient_id,
            type=type,
            subject=subject,
            message=message,
            status="SENT",
            sent_at=datetime.utcnow(),
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def send_appointment_reminder(self, appointment_id: int):
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return None
        return self.create_notification(
            None,
            "SMS",
            "Appointment Reminder",
            f"Reminder: appointment token #{appointment.token_number} on {appointment.appointment_date}",
            appointment.patient_id,
        )

    def send_medicine_reminder(self, patient_id: int, prescription_id: int):
        return self.create_notification(None, "PUSH", "Medicine Reminder", f"Prescription {prescription_id} is active.", patient_id)

    def send_birthday_wishes(self, patient_id: int):
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None
        return self.create_notification(None, "EMAIL", "Birthday Wishes", f"Happy Birthday, {patient.first_name}!", patient_id)

    def send_report_ready(self, patient_id: int, report_type: str, report_id: int):
        return self.create_notification(None, "EMAIL", f"{report_type} Report Ready", f"Your report #{report_id} is ready.", patient_id)
