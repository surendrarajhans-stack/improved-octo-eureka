"""Seed the database with initial data."""

import asyncio
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password

# Import all models to ensure they're registered
from app.models import (  # noqa: F401
    finance,
    hr,
    inventory,
    opd,
    payroll,
    radiology,
)
from app.models.appointment import Appointment, AppointmentStatus
from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentMethod
from app.models.ipd import Bed, BedStatus, Ward, WardType
from app.models.laboratory import LabTest
from app.models.master import Department, Doctor, Patient, Staff
from app.models.pharmacy import Medicine
from app.models.user import Role, User


async def seed(session: AsyncSession) -> None:
    print("Seeding database...")

    # ── 1. Admin user ───────────────────────────────────────────────────────
    admin = User(
        username="admin",
        email="admin@hms.local",
        hashed_password=hash_password("admin123"),
        full_name="System Administrator",
        role=Role.ADMIN,
    )
    session.add(admin)
    await session.flush()
    print(f"  Created admin user: id={admin.id}")

    # ── 2. Departments ──────────────────────────────────────────────────────
    dept_names = [
        ("General Medicine", "Outpatient and inpatient general medicine"),
        ("Surgery", "Surgical procedures and post-op care"),
        ("Pediatrics", "Care for infants, children, and adolescents"),
        ("Gynecology", "Women health and obstetrics"),
        ("Emergency", "24/7 emergency and trauma care"),
    ]
    departments = []
    for name, desc in dept_names:
        dept = Department(name=name, description=desc, is_active=True)
        session.add(dept)
        departments.append(dept)
    await session.flush()
    print(f"  Created {len(departments)} departments")

    # ── 3. Doctor users ─────────────────────────────────────────────────────
    doctor_data = [
        ("dr_john", "john.doe@hms.local", "Dr. John Doe", "General Physician", "MBBS, MD", "LIC001", 500.0),
        ("dr_jane", "jane.smith@hms.local", "Dr. Jane Smith", "Surgeon", "MBBS, MS", "LIC002", 800.0),
        ("dr_peter", "peter.jones@hms.local", "Dr. Peter Jones", "Pediatrician", "MBBS, DCH", "LIC003", 600.0),
        ("dr_mary", "mary.wilson@hms.local", "Dr. Mary Wilson", "Gynecologist", "MBBS, DGO", "LIC004", 700.0),
        ("dr_alex", "alex.kumar@hms.local", "Dr. Alex Kumar", "Emergency Physician", "MBBS, MRCEM", "LIC005", 650.0),
    ]
    doctor_users = []
    doctors = []
    for i, (username, email, full_name, specialization, qualification, lic, fee) in enumerate(
        doctor_data
    ):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password("doctor123"),
            full_name=full_name,
            role=Role.DOCTOR,
        )
        session.add(user)
        doctor_users.append(user)
    await session.flush()

    for i, user in enumerate(doctor_users):
        _, _, _, specialization, qualification, lic, fee = doctor_data[i]
        doc = Doctor(
            user_id=user.id,
            department_id=departments[i].id,
            specialization=specialization,
            qualification=qualification,
            license_number=lic,
            consultation_fee=fee,
            is_available=True,
        )
        session.add(doc)
        doctors.append(doc)
    await session.flush()
    print(f"  Created {len(doctors)} doctors")

    # ── 4. Staff users ──────────────────────────────────────────────────────
    staff_data = [
        ("nurse_ann", "ann@hms.local", "Ann Taylor", Role.NURSE, "Head Nurse"),
        ("recept_bob", "bob@hms.local", "Bob Carter", Role.RECEPTIONIST, "Receptionist"),
        ("pharma_sam", "sam@hms.local", "Sam Lee", Role.PHARMACIST, "Pharmacist"),
    ]
    staff_members = []
    for i, (username, email, full_name, role, designation) in enumerate(staff_data):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password("staff123"),
            full_name=full_name,
            role=role,
        )
        session.add(user)
        await session.flush()
        staff = Staff(
            user_id=user.id,
            department_id=departments[i].id,
            designation=designation,
            employee_id=f"EMP{i + 1:03d}",
            joining_date=date(2022, 1, 15),
            salary=35000.0,
        )
        session.add(staff)
        staff_members.append(staff)
    await session.flush()
    print(f"  Created {len(staff_members)} staff members")

    # ── 5. Patients ─────────────────────────────────────────────────────────
    patient_data = [
        ("Alice Brown", "1985-03-15", "Female", "A+", "9876543210"),
        ("Bob Davis", "1972-07-22", "Male", "B+", "9876543211"),
        ("Carol Evans", "1990-11-30", "Female", "O+", "9876543212"),
        ("David Foster", "1965-05-12", "Male", "AB+", "9876543213"),
        ("Eva Green", "1995-09-08", "Female", "B-", "9876543214"),
        ("Frank Harris", "1958-12-25", "Male", "A-", "9876543215"),
        ("Grace Irving", "2000-02-14", "Female", "O-", "9876543216"),
        ("Henry Johnson", "1980-06-18", "Male", "AB-", "9876543217"),
        ("Iris King", "1975-04-03", "Female", "A+", "9876543218"),
        ("Jack Lewis", "1988-10-20", "Male", "B+", "9876543219"),
    ]
    patients = []
    year = datetime.now().year
    for i, (name, dob_str, gender, blood_group, phone) in enumerate(patient_data):
        p = Patient(
            patient_id=f"P-{year}-{i + 1:04d}",
            full_name=name,
            dob=date.fromisoformat(dob_str),
            gender=gender,
            blood_group=blood_group,
            phone=phone,
            email=f"{name.lower().replace(' ', '.')}@email.com",
            address=f"{i + 100} Main Street, City",
            emergency_contact="Emergency Person",
            emergency_phone=f"987654321{i}",
        )
        session.add(p)
        patients.append(p)
    await session.flush()
    print(f"  Created {len(patients)} patients")

    # ── 6. Appointments ──────────────────────────────────────────────────────
    today = date.today()
    appt_statuses = [
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CONFIRMED,
    ]
    for i in range(10):
        appt = Appointment(
            patient_id=patients[i].id,
            doctor_id=doctors[i % 5].id,
            department_id=departments[i % 5].id,
            appointment_date=today + timedelta(days=i - 3),
            appointment_time=time(9 + i % 8, 0),
            status=appt_statuses[i],
            reason=f"Regular checkup - patient {i + 1}",
            created_by=admin.id,
        )
        session.add(appt)
    await session.flush()
    print("  Created 10 appointments")

    # ── 7. Wards and beds ───────────────────────────────────────────────────
    ward_types = list(WardType)
    all_beds = []
    for wt in ward_types:
        ward = Ward(
            name=f"{wt.value.replace('_', ' ').title()} Ward",
            ward_type=wt,
            floor=ward_types.index(wt) + 1,
            capacity=10,
        )
        session.add(ward)
        await session.flush()
        for j in range(5):
            bed = Bed(
                bed_number=f"{wt.value[:2]}-{j + 1:02d}",
                ward_id=ward.id,
                status=BedStatus.AVAILABLE,
            )
            session.add(bed)
            all_beds.append(bed)
    await session.flush()
    print(f"  Created {len(ward_types)} wards with 5 beds each")

    # ── 8. Medicines ─────────────────────────────────────────────────────────
    med_data = [
        ("Paracetamol 500mg", "Paracetamol", "Analgesic", "PharmaCo", "Tablet", 2.5, 50, 500),
        ("Amoxicillin 250mg", "Amoxicillin", "Antibiotic", "MedLab", "Capsule", 5.0, 30, 300),
        ("Metformin 500mg", "Metformin", "Anti-diabetic", "DiabetoCare", "Tablet", 3.5, 100, 1000),
        ("Atorvastatin 20mg", "Atorvastatin", "Statin", "HeartPharma", "Tablet", 8.0, 50, 400),
        ("Omeprazole 20mg", "Omeprazole", "Antacid", "GastroMed", "Capsule", 4.0, 40, 300),
        ("Amlodipine 5mg", "Amlodipine", "Antihypertensive", "CardioLab", "Tablet", 6.0, 50, 500),
        ("Normal Saline 500ml", "Sodium Chloride", "IV Fluid", "InfusionCo", "Bottle", 35.0, 20, 100),
        ("Insulin Regular", "Insulin", "Antidiabetic", "BioPharma", "Vial", 150.0, 10, 50),
    ]
    for name, generic, cat, mfr, unit, price, reorder, stock in med_data:
        med = Medicine(
            name=name,
            generic_name=generic,
            category=cat,
            manufacturer=mfr,
            unit=unit,
            unit_price=price,
            reorder_level=reorder,
            current_stock=stock,
            is_available=True,
        )
        session.add(med)
    await session.flush()
    print("  Created 8 medicines")

    # ── 9. Lab tests ─────────────────────────────────────────────────────────
    lab_tests = [
        ("Complete Blood Count", "CBC", "Hematology", "4.5-11 x10^9/L", "x10^9/L", 150.0),
        ("Blood Glucose Fasting", "BG", "Biochemistry", "70-100 mg/dL", "mg/dL", 80.0),
        ("HbA1c", "HbA1c", "Biochemistry", "<5.7%", "%", 350.0),
        ("Lipid Profile", "LP", "Biochemistry", "<200 mg/dL", "mg/dL", 400.0),
        ("Urine Analysis", "UA", "Microbiology", "Normal", None, 100.0),
        ("Thyroid Function Test", "TFT", "Endocrinology", "0.4-4.0 mIU/L", "mIU/L", 500.0),
    ]
    for name, cat, category, normal_range, unit, price in lab_tests:
        lt = LabTest(
            name=name,
            category=category,
            normal_range=normal_range,
            unit=unit,
            price=price,
            turnaround_hours=24,
        )
        session.add(lt)
    await session.flush()
    print("  Created 6 lab tests")

    # ── 10. Sample invoice and payment ──────────────────────────────────────
    invoice = Invoice(
        invoice_number=f"INV-{year}-0001",
        patient_id=patients[0].id,
        total_amount=1500.0,
        paid_amount=0.0,
        discount=0.0,
        tax=0.0,
        status=InvoiceStatus.PENDING,
    )
    session.add(invoice)
    await session.flush()

    payment = Payment(
        invoice_id=invoice.id,
        amount=1500.0,
        payment_method=PaymentMethod.CASH,
        notes="Full payment",
    )
    session.add(payment)
    invoice.paid_amount = 1500.0
    invoice.status = InvoiceStatus.PAID
    await session.flush()
    print("  Created sample invoice and payment")

    await session.commit()
    print("\nDatabase seeded successfully!")
    print("\nDefault credentials:")
    print("  Admin  - username: admin    / password: admin123")
    print("  Doctor - username: dr_john  / password: doctor123")
    print("  Staff  - username: nurse_ann / password: staff123")


async def main() -> None:
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if already seeded
        from sqlalchemy import select
        result = await session.execute(select(User))
        if result.scalar_one_or_none() is not None:
            print("Database already has data. Skipping seed.")
            return
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
