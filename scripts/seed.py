import random
from datetime import date, datetime, time, timedelta

import app.models  # noqa: F401
from app.core.permissions import UserRole
from app.core.security import get_password_hash
from app.database import Base, SessionLocal, engine
from app.models.ambulance import AmbulanceTrip, Driver, Vehicle
from app.models.appointment import Appointment, AppointmentQueue
from app.models.billing import BillingRate, Invoice, InvoiceItem, Payment
from app.models.clinical import EmergencyCase, IPDAdmission
from app.models.doctor import Doctor, DoctorSchedule
from app.models.finance import Account, Expense
from app.models.hospital import Bed, Department, Hospital, Ward
from app.models.hr import Employee
from app.models.insurance import InsurancePolicy
from app.models.inventory import InventoryCategory, InventoryItem, Supplier
from app.models.laboratory import LabOrder, LabOrderItem, LabReport, LabTest
from app.models.notification import Notification
from app.models.patient import Patient, PatientAllergy, PatientMedicalHistory
from app.models.pharmacy import DrugInteraction, Medicine, MedicineBatch
from app.models.radiology import RadiologyOrder, RadiologyReport
from app.models.user import User

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def get_or_create(model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance
    params = {**filters, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def seed_hospital():
    hospital = get_or_create(Hospital, name="City General Hospital", code="CGH001", address="100 Health Avenue", city="Springfield", state="State", country="Country", phone="+1-555-100-2000", email="info@citygeneralhospital.com", bed_capacity=120)
    departments = []
    for i, name in enumerate(["General Medicine", "Cardiology", "Orthopedics", "Neurology", "Pediatrics", "Gynecology", "Emergency", "Laboratory", "Radiology", "Pharmacy"], start=1):
        departments.append(get_or_create(Department, hospital_id=hospital.id, name=name, code=f"DPT{i:03d}", floor=str((i % 5) + 1), phone=f"555-20{i:02d}"))
    if not db.query(Ward).count():
        for idx, dept in enumerate(departments[:4], start=1):
            ward = Ward(hospital_id=hospital.id, department_id=dept.id, name=f"{dept.name} Ward", ward_type="GENERAL", total_beds=10, floor=str(idx))
            db.add(ward)
            db.flush()
            for bed_no in range(1, 11):
                db.add(Bed(ward_id=ward.id, bed_number=f"{idx}-{bed_no}", bed_type="STANDARD", status="AVAILABLE"))
        db.commit()
    return hospital, departments


def seed_users_and_doctors(hospital, departments):
    admin = db.query(User).filter_by(username="admin").first()
    if not admin:
        admin = User(hospital_id=hospital.id, username="admin", email="admin@hospital.local", password_hash=get_password_hash("admin123"), full_name="System Administrator", phone="5551000000", role=UserRole.SUPER_ADMIN, is_active=True)
        db.add(admin)
        db.commit()
        db.refresh(admin)
    doctor_names = ["Aarav Sharma", "Priya Iyer", "Rahul Mehta", "Sneha Kapoor", "Vikram Rao"]
    doctors = []
    for idx, full_name in enumerate(doctor_names, start=1):
        username = f"doctor{idx}"
        user = get_or_create(User, hospital_id=hospital.id, username=username, email=f"{username}@hospital.local", password_hash=get_password_hash("doctor123"), full_name=full_name, phone=f"55510010{idx}", role=UserRole.DOCTOR, is_active=True)
        doctor = db.query(Doctor).filter_by(user_id=user.id).first()
        if not doctor:
            doctor = Doctor(user_id=user.id, hospital_id=hospital.id, employee_code=f"DOC{idx:03d}", specialization=departments[idx-1].name, qualification="MD", registration_no=f"REG{idx:04d}", experience_years=5 + idx, consultation_fee=400 + idx * 50, department_id=departments[idx - 1].id, is_available=True, bio=f"Experienced specialist in {departments[idx-1].name}", languages_spoken="English, Hindi")
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
        if not db.query(DoctorSchedule).filter_by(doctor_id=doctor.id).count():
            for day in range(0, 5):
                db.add(DoctorSchedule(doctor_id=doctor.id, day_of_week=day, start_time=time(9, 0), end_time=time(14, 0), slot_duration_minutes=15, max_appointments=20))
            db.commit()
        doctors.append(doctor)
    return admin, doctors


def seed_patients(hospital):
    first_names = ["John", "Emma", "Liam", "Olivia", "Noah", "Ava", "Mason", "Sophia", "Lucas", "Mia", "Arjun", "Anaya", "Kabir", "Isha", "Riya", "Dev", "Sara", "Vihaan", "Aditi", "Neel"]
    patients = []
    for idx, first_name in enumerate(first_names, start=1):
        uhid = f"UHID-{date.today().year}-{idx:06d}"
        patient = db.query(Patient).filter_by(uhid=uhid).first()
        if not patient:
            patient = Patient(hospital_id=hospital.id, uhid=uhid, first_name=first_name, last_name=f"Patient{idx}", dob=date.today() - timedelta(days=365 * (20 + idx % 30)), gender="Male" if idx % 2 else "Female", blood_group=random.choice(["A+", "B+", "O+", "AB+"]), phone=f"999000{idx:04d}", email=f"patient{idx}@mail.com", address="Springfield", emergency_contact_name="Family Member", emergency_contact_phone=f"888000{idx:04d}", emergency_contact_relation="Parent", nationality="Indian", is_active=True)
            db.add(patient)
            db.commit()
            db.refresh(patient)
            db.add(PatientMedicalHistory(patient_id=patient.id, condition=random.choice(["Diabetes", "Hypertension", "Asthma", "Migraine"]), notes="Regular follow-up"))
            db.add(PatientAllergy(patient_id=patient.id, allergen=random.choice(["Dust", "Penicillin", "Peanuts", "Latex"]), reaction="Observed"))
            db.commit()
        patients.append(patient)
    return patients


def seed_appointments(hospital, patients, doctors, admin):
    if db.query(Appointment).count() >= 30:
        return db.query(Appointment).all()
    appointments = []
    for idx in range(30):
        appt_date = date.today() - timedelta(days=random.randint(0, 10))
        doctor = random.choice(doctors)
        patient = random.choice(patients)
        appointment = Appointment(hospital_id=hospital.id, patient_id=patient.id, doctor_id=doctor.id, department_id=doctor.department_id, appointment_date=appt_date, appointment_time=time(9 + (idx % 6), (idx % 4) * 15), slot_number=(idx % 20) + 1, token_number=idx + 1, appointment_type="OPD", status=random.choice(["SCHEDULED", "CONFIRMED", "COMPLETED", "WAITING"]), chief_complaint=random.choice(["Fever", "Back pain", "Headache", "Follow-up"]), priority=random.choice(["NORMAL", "HIGH"]), consultation_fee=doctor.consultation_fee, payment_status="PAID" if idx % 2 == 0 else "PENDING", booked_by=admin.id)
        db.add(appointment)
        db.flush()
        db.add(AppointmentQueue(appointment_id=appointment.id, queue_position=appointment.token_number, waiting_time_minutes=random.randint(5, 30)))
        appointments.append(appointment)
    db.commit()
    return appointments


def seed_ipd(hospital, patients, doctors, departments):
    if db.query(IPDAdmission).count() >= 5:
        return
    beds = db.query(Bed).filter(Bed.status == "AVAILABLE").limit(5).all()
    for idx, bed in enumerate(beds, start=1):
        patient = patients[idx - 1]
        doctor = doctors[idx % len(doctors)]
        admission = IPDAdmission(hospital_id=hospital.id, patient_id=patient.id, doctor_id=doctor.id, department_id=doctor.department_id, ward_id=bed.ward_id, bed_id=bed.id, admission_date=date.today() - timedelta(days=idx), admission_time=time(10, 0), admission_type="ELECTIVE", primary_diagnosis="Observation", attendant_name="Relative", attendant_phone="7770000000", attendant_relation="Sibling", status="ADMITTED")
        bed.status = "OCCUPIED"
        bed.current_patient_id = patient.id
        db.add(admission)
    db.commit()


def seed_lab_and_radiology(hospital, patients, doctors):
    tests_catalog = [("CBC", "LAB001"), ("LFT", "LAB002"), ("RFT", "LAB003"), ("Lipid Profile", "LAB004"), ("Blood Sugar", "LAB005"), ("Thyroid", "LAB006"), ("Urine Routine", "LAB007"), ("X-Ray Chest", "RAD001"), ("MRI Brain", "RAD002"), ("CT Abdomen", "RAD003")]
    for idx, (name, code) in enumerate(tests_catalog, start=1):
        if not db.query(LabTest).filter_by(test_code=code).first():
            db.add(LabTest(hospital_id=hospital.id, test_name=name, test_code=code, category="Radiology" if code.startswith("RAD") else "Pathology", normal_range="Normal", unit="unit", price=200 + idx * 50, turnaround_hours=24, is_active=True))
    db.commit()
    if not db.query(LabOrder).count():
        tests = db.query(LabTest).filter(LabTest.test_code.like("LAB%")).all()
        for idx in range(5):
            order = LabOrder(hospital_id=hospital.id, patient_id=patients[idx].id, doctor_id=doctors[idx % len(doctors)].id, sample_type="Blood", priority="ROUTINE", status="COMPLETED")
            db.add(order)
            db.flush()
            test = tests[idx % len(tests)]
            item = LabOrderItem(order_id=order.id, test_id=test.id, status="COMPLETED", result_value=str(10 + idx), verified_by=doctors[idx % len(doctors)].user_id, verified_at=datetime.utcnow())
            db.add(item)
            db.flush()
            db.add(LabReport(order_id=order.id, patient_id=order.patient_id, interpretation="Within acceptable range"))
        db.commit()
    if not db.query(RadiologyOrder).count():
        for idx in range(3):
            order = RadiologyOrder(hospital_id=hospital.id, patient_id=patients[idx].id, doctor_id=doctors[idx].id, study_type=random.choice(["XRAY", "MRI", "CT"]), body_part="Chest", clinical_history="Pain", priority="URGENT", status="COMPLETED")
            db.add(order)
            db.flush()
            db.add(RadiologyReport(order_id=order.id, patient_id=order.patient_id, radiologist_id=doctors[idx].user_id, findings="No acute abnormality", impression="Stable", recommendations="Clinical correlation", is_verified=True))
        db.commit()


def seed_pharmacy(hospital, patients):
    medicine_names = [f"Medicine {idx}" for idx in range(1, 56)]
    if db.query(Medicine).count() < 50:
        for idx, name in enumerate(medicine_names, start=1):
            med = Medicine(hospital_id=hospital.id, name=name, generic_name=f"Generic {idx}", category=random.choice(["Antibiotic", "Analgesic", "Vitamin", "Cardiac"]), form=random.choice(["TABLET", "CAPSULE", "SYRUP"]), manufacturer="Medico", unit="Strip", reorder_level=10, description="Stock medicine")
            db.add(med)
            db.flush()
            db.add(MedicineBatch(medicine_id=med.id, batch_number=f"BATCH{idx:03d}", expiry_date=date.today() + timedelta(days=180 + idx), manufacture_date=date.today() - timedelta(days=90), purchase_price=10 + idx, selling_price=15 + idx, quantity_purchased=100, quantity_available=random.randint(5, 80)))
        db.commit()
    meds = db.query(Medicine).limit(4).all()
    if meds and not db.query(DrugInteraction).count():
        db.add(DrugInteraction(medicine1_id=meds[0].id, medicine2_id=meds[1].id, severity="MAJOR", description="Increased bleeding risk", clinical_effect="Monitor closely"))
        db.add(DrugInteraction(medicine1_id=meds[2].id, medicine2_id=meds[3].id, severity="MODERATE", description="May cause drowsiness", clinical_effect="Advise caution"))
        db.commit()


def seed_billing(hospital, patients, doctors):
    for idx, rate_name in enumerate(["Consultation", "CBC", "MRI", "Bed Charge", "Pharmacy Dispense"], start=1):
        get_or_create(BillingRate, hospital_id=hospital.id, service_type="GENERAL", service_name=rate_name, price=250 * idx, tax_percent=5)
    if db.query(Invoice).count() < 10:
        for idx in range(10):
            invoice = Invoice(hospital_id=hospital.id, patient_id=patients[idx].id, invoice_number=f"INV-{date.today().year}-{idx+1:05d}", visit_type="OPD", subtotal=500 + idx * 100, total_amount=500 + idx * 100, net_payable=500 + idx * 100, status="PAID", advance_paid=500 + idx * 100)
            db.add(invoice)
            db.flush()
            db.add(InvoiceItem(invoice_id=invoice.id, service_type="CONSULTATION", description="Consultation Fee", quantity=1, unit_price=invoice.total_amount, total=invoice.total_amount))
            db.add(Payment(invoice_id=invoice.id, patient_id=invoice.patient_id, amount=invoice.total_amount, payment_mode=random.choice(["CASH", "CARD", "UPI"]), transaction_id=f"TXN{idx:05d}", received_by=doctors[idx % len(doctors)].user_id, status="SUCCESS"))
        db.commit()


def seed_hr_inventory_finance_ambulance(hospital, departments, admin):
    if not db.query(Employee).count():
        for idx in range(1, 11):
            db.add(Employee(hospital_id=hospital.id, employee_code=f"EMP{idx:03d}", first_name=f"Staff{idx}", last_name="Member", phone=f"700000{idx:04d}", email=f"staff{idx}@hospital.local", department_id=departments[idx % len(departments)].id, designation=random.choice(["Nurse", "Technician", "Accountant", "Receptionist"]), employment_type="PERMANENT", join_date=date.today() - timedelta(days=400 + idx), salary=25000 + idx * 1000))
        db.commit()
    category = get_or_create(InventoryCategory, hospital_id=hospital.id, name="Medical Supplies", type="MEDICAL")
    get_or_create(Supplier, hospital_id=hospital.id, name="Health Supplier", code="SUP001", contact_person="Vendor", phone="6660001111", email="vendor@mail.com")
    if not db.query(InventoryItem).count():
        for idx in range(1, 16):
            db.add(InventoryItem(hospital_id=hospital.id, category_id=category.id, name=f"Item {idx}", code=f"ITM{idx:03d}", unit="pcs", reorder_level=10, current_stock=random.randint(3, 40), location="Store Room"))
        db.commit()
    if not db.query(Account).count():
        db.add(Account(hospital_id=hospital.id, account_code="1000", account_name="Cash", account_type="ASSET", opening_balance=100000))
        db.add(Account(hospital_id=hospital.id, account_code="4000", account_name="Revenue", account_type="INCOME", opening_balance=0))
        db.add(Expense(hospital_id=hospital.id, expense_date=date.today(), category="Utilities", amount=15000, description="Monthly electricity", approved_by=admin.id, status="APPROVED", payment_mode="BANK"))
        db.commit()
    if not db.query(Driver).count():
        driver = Driver(hospital_id=hospital.id, name="Ambulance Driver", phone="5559000000", license_number="DL12345")
        db.add(driver)
        db.flush()
        vehicle = Vehicle(hospital_id=hospital.id, registration_no="AMB-001", vehicle_type="BASIC", model="Force", capacity=2, driver_id=driver.id, status="AVAILABLE")
        db.add(vehicle)
        db.flush()
        db.add(AmbulanceTrip(hospital_id=hospital.id, vehicle_id=vehicle.id, driver_id=driver.id, pickup_address="Airport Road", destination="City General Hospital", trip_type="EMERGENCY", start_time=datetime.utcnow() - timedelta(hours=2), end_time=datetime.utcnow() - timedelta(hours=1), distance_km=12.5, fare=1200, status="COMPLETED"))
        db.commit()


def seed_other(hospital, patients, doctors, admin):
    if not db.query(InsurancePolicy).count():
        for idx in range(5):
            db.add(InsurancePolicy(hospital_id=hospital.id, patient_id=patients[idx].id, policy_number=f"POL{idx:04d}", insurer_name="Health Insurance Co", coverage_amount=100000, copay_percent=10, start_date=date.today() - timedelta(days=30), end_date=date.today() + timedelta(days=330), is_active=True))
        db.commit()
    if not db.query(EmergencyCase).count():
        for idx in range(5):
            db.add(EmergencyCase(hospital_id=hospital.id, patient_id=patients[idx].id, esi_level=(idx % 5) + 1, chief_complaint=random.choice(["Accident", "Chest pain", "Breathlessness"]), triage_notes="Under observation", attending_doctor_id=doctors[idx % len(doctors)].id, disposition=random.choice(["ADMITTED", "DISCHARGED"])))
        db.commit()
    if not db.query(Notification).count():
        db.add(Notification(user_id=admin.id, type="EMAIL", subject="Welcome", message="System seeded successfully.", status="SENT", sent_at=datetime.utcnow()))
        db.add(Notification(user_id=admin.id, type="PUSH", subject="Low Stock Alert", message="Review inventory low-stock dashboard.", status="PENDING"))
        db.commit()


def main():
    hospital, departments = seed_hospital()
    admin, doctors = seed_users_and_doctors(hospital, departments)
    patients = seed_patients(hospital)
    seed_appointments(hospital, patients, doctors, admin)
    seed_ipd(hospital, patients, doctors, departments)
    seed_lab_and_radiology(hospital, patients, doctors)
    seed_pharmacy(hospital, patients)
    seed_billing(hospital, patients, doctors)
    seed_hr_inventory_finance_ambulance(hospital, departments, admin)
    seed_other(hospital, patients, doctors, admin)
    print("Seed complete: admin/admin123")


if __name__ == "__main__":
    main()
    db.close()
