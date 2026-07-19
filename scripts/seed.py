import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import models
from app.database import SessionLocal, init_db
from app.enums import (
    IncidentSeverity,
    MedicationAdministrationStatus,
    NoteVisibility,
    PayerCategory,
    ResidentStatus,
    Role,
    TaskStatus,
)
from app.security import get_password_hash


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.scalar(select(models.User).where(models.User.email == "admin@example.com")):
            return
        now = datetime.now(timezone.utc)
        admin = models.User(
            email="admin@example.com",
            full_name="Avery Admin",
            password_hash=get_password_hash("AdminPass123!"),
            role=Role.ADMIN,
            phone="555-1000",
        )
        doctor = models.User(
            email="doctor@example.com",
            full_name="Drew Doctor",
            password_hash=get_password_hash("DoctorPass123!"),
            role=Role.DOCTOR,
        )
        nurse = models.User(
            email="nurse@example.com",
            full_name="Nina Nurse",
            password_hash=get_password_hash("NursePass123!"),
            role=Role.NURSE,
        )
        accountant = models.User(
            email="accountant@example.com",
            full_name="Alex Accountant",
            password_hash=get_password_hash("AccountPass123!"),
            role=Role.ACCOUNTANT,
        )
        family = models.User(
            email="family@example.com",
            full_name="Frank Family",
            password_hash=get_password_hash("FamilyPass123!"),
            role=Role.FAMILY_MEMBER,
        )
        db.add_all([admin, doctor, nurse, accountant, family])
        db.flush()

        resident = models.Resident(
            first_name="Eleanor",
            last_name="Brooks",
            date_of_birth=date(1942, 5, 14),
            gender="Female",
            status=ResidentStatus.ACTIVE,
            emergency_contacts=[
                {"name": "Frank Family", "phone": "555-2222", "relationship": "Son"}
            ],
            allergies=["Penicillin"],
            conditions=["Hypertension", "Type 2 Diabetes"],
            preferred_pharmacy="Green Valley Pharmacy",
            primary_physician="Drew Doctor",
            room_number="101",
            bed_number="A",
        )
        db.add(resident)
        db.flush()

        db.add(models.FamilyLink(resident_id=resident.id, user_id=family.id, relationship="Son"))
        db.add(
            models.ResidentStatusHistory(
                resident_id=resident.id,
                new_status=ResidentStatus.ACTIVE,
                changed_by_user_id=admin.id,
                reason="Initial admit",
            )
        )
        db.add(
            models.RoomAssignmentHistory(
                resident_id=resident.id,
                room_number="101",
                bed_number="A",
                assigned_by_user_id=admin.id,
            )
        )
        db.add(
            models.CarePlan(
                resident_id=resident.id,
                goals=["Maintain stable blood pressure"],
                tasks=["Daily vitals", "Medication adherence"],
                responsible_staff_user_ids=[nurse.id, doctor.id],
            )
        )
        order = models.MedicationOrder(
            resident_id=resident.id,
            medication_name="Lisinopril",
            dosage="10 mg",
            route="PO",
            schedule_time="08:00",
            prn=False,
            ordered_by_user_id=doctor.id,
        )
        db.add(order)
        db.flush()
        db.add(
            models.MedicationAdministration(
                medication_order_id=order.id,
                resident_id=resident.id,
                status=MedicationAdministrationStatus.ADMINISTERED,
                scheduled_for=now - timedelta(hours=2),
                administered_at=now - timedelta(hours=2),
                recorded_by_user_id=nurse.id,
                notes="Taken with breakfast",
            )
        )
        db.add(
            models.VitalRecord(
                resident_id=resident.id,
                blood_pressure="128/76",
                heart_rate=72,
                temperature=98.4,
                spo2=97,
                weight=142.2,
                recorded_by_user_id=nurse.id,
            )
        )
        db.add(
            models.ProgressNote(
                resident_id=resident.id,
                author_user_id=nurse.id,
                visibility=NoteVisibility.FAMILY_APPROVED,
                content="Resident participated in morning activity and tolerated meals well.",
            )
        )
        db.add(
            models.IncidentReport(
                resident_id=resident.id,
                reported_by_user_id=nurse.id,
                severity=IncidentSeverity.LOW,
                description="Minor near-fall during transfer; no injury observed.",
                follow_up_actions=["Reinforced transfer belt usage"],
            )
        )
        db.add(
            models.TaskBoardItem(
                resident_id=resident.id,
                assigned_to_user_id=nurse.id,
                title="Evening wound check",
                description="Inspect left heel dressing.",
                due_at=now + timedelta(hours=8),
                status=TaskStatus.TODO,
            )
        )
        payer = models.Payer(
            name="Traditional Medicare",
            category=PayerCategory.MEDICARE,
            configuration={"plan_code": "MCR-A"},
        )
        db.add(payer)
        db.flush()
        invoice = models.Invoice(
            resident_id=resident.id,
            payer_id=payer.id,
            invoice_month=now.strftime("%Y-%m"),
            due_date=date.today() + timedelta(days=15),
        )
        db.add(invoice)
        db.flush()
        db.add_all(
            [
                models.InvoiceLineItem(
                    invoice_id=invoice.id, description="Room and board", amount=3200.0
                ),
                models.InvoiceLineItem(
                    invoice_id=invoice.id, description="Medication management", amount=450.0
                ),
            ]
        )
        db.add(
            models.Payment(
                invoice_id=invoice.id,
                amount=500.0,
                reference="DEMO-500",
                received_by_user_id=accountant.id,
            )
        )
        db.add(
            models.FamilyUpdate(
                resident_id=resident.id,
                author_user_id=nurse.id,
                title="Weekly Update",
                content="Vitals remain stable and appetite is improving.",
                approved=True,
            )
        )
        db.add(
            models.Appointment(
                resident_id=resident.id,
                appointment_type="Cardiology Follow-up",
                destination="Regional Heart Clinic",
                scheduled_for=now + timedelta(days=7),
                transport_required=True,
            )
        )
        db.add(models.InventoryItem(name="Gloves", stock=250, reorder_threshold=100, unit="pairs"))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
