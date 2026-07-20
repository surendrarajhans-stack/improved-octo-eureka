from datetime import date

from app.core.permissions import UserRole
from app.core.security import get_password_hash
from app.models.billing import Invoice
from app.models.hospital import Department, Hospital
from app.models.pharmacy import DrugInteraction, Medicine
from app.models.user import User


def seed_auth_data(db):
    hospital = Hospital(name="Test Hospital", code="TEST001")
    db.add(hospital)
    db.flush()
    dept = Department(hospital_id=hospital.id, name="General Medicine", code="GEN")
    db.add(dept)
    user = User(hospital_id=hospital.id, username="admin", email="admin@test.com", password_hash=get_password_hash("admin123"), full_name="Admin User", role=UserRole.SUPER_ADMIN, is_active=True)
    db.add(user)
    db.commit()
    return hospital, dept, user


def login(client):
    response = client.post("/auth/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    assert response.status_code in (303, 302)
    return response


def test_login_page(client):
    response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 200


def test_dashboard_requires_auth(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in [302, 303, 307, 401]


def test_login_flow(client, db):
    seed_auth_data(db)
    response = client.post("/auth/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_create_patient(client, db):
    hospital, dept, user = seed_auth_data(db)
    login(client)
    response = client.post("/patients", data={"first_name": "Jane", "last_name": "Doe", "hospital_id": hospital.id, "phone": "1234567890", "gender": "Female"}, follow_redirects=False)
    assert response.status_code == 303
    patient_list = client.get("/patients")
    assert "UHID-" in patient_list.text


def test_create_appointment(client, db):
    from app.models.doctor import Doctor
    from app.models.patient import Patient

    hospital, dept, user = seed_auth_data(db)
    doctor_user = User(hospital_id=hospital.id, username="doc", email="doc@test.com", password_hash=get_password_hash("doc123"), full_name="Doctor Test", role=UserRole.DOCTOR, is_active=True)
    db.add(doctor_user)
    db.flush()
    doctor = Doctor(user_id=doctor_user.id, hospital_id=hospital.id, employee_code="DOC001", specialization="General", department_id=dept.id, consultation_fee=500)
    patient = Patient(hospital_id=hospital.id, uhid=f"UHID-{date.today().year}-000001", first_name="Patient", last_name="One")
    db.add_all([doctor, patient])
    db.commit()
    login(client)
    response = client.post("/appointments", data={"patient_id": patient.id, "doctor_id": doctor.id, "department_id": dept.id, "appointment_date": str(date.today()), "appointment_time": "10:00"}, follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/appointments")
    assert "Token" in page.text


def test_billing_invoice(client, db):
    from app.models.patient import Patient

    hospital, dept, user = seed_auth_data(db)
    patient = Patient(hospital_id=hospital.id, uhid=f"UHID-{date.today().year}-000002", first_name="Bill", last_name="Patient")
    db.add(patient)
    db.commit()
    login(client)
    payload = '[{"service_type":"CONSULTATION","description":"Fee","quantity":1,"unit_price":500,"discount":0,"tax_percent":0}]'
    response = client.post("/billing/invoices", data={"patient_id": patient.id, "visit_type": "OPD", "items": payload})
    assert response.status_code == 200
    assert db.query(Invoice).count() == 1


def test_api_patients_list(client, db):
    from app.models.patient import Patient

    hospital, dept, user = seed_auth_data(db)
    db.add(Patient(hospital_id=hospital.id, uhid=f"UHID-{date.today().year}-000003", first_name="Api", last_name="Patient"))
    db.commit()
    login(client)
    response = client.get("/patients")
    assert response.status_code == 200
    assert "Api Patient" in response.text


def test_ai_drug_interaction(client, db):
    hospital, dept, user = seed_auth_data(db)
    med1 = Medicine(hospital_id=hospital.id, name="Drug A")
    med2 = Medicine(hospital_id=hospital.id, name="Drug B")
    db.add_all([med1, med2])
    db.flush()
    db.add(DrugInteraction(medicine1_id=med1.id, medicine2_id=med2.id, severity="MAJOR", description="Interaction"))
    db.commit()
    login(client)
    response = client.post("/ai/drug-interaction", json={"medicine_ids": [med1.id, med2.id]})
    assert response.status_code == 200
    assert response.json()[0]["severity"] == "MAJOR"


def test_emergency_register(client, db):
    hospital, dept, user = seed_auth_data(db)
    login(client)
    response = client.post("/emergency/register", data={"hospital_id": hospital.id, "chief_complaint": "Chest pain", "esi_level": 2})
    assert response.status_code == 200
    assert response.json()["message"] == "Emergency case registered"


def test_lab_order_create(client, db):
    from app.models.doctor import Doctor
    from app.models.laboratory import LabTest
    from app.models.patient import Patient

    hospital, dept, user = seed_auth_data(db)
    patient = Patient(hospital_id=hospital.id, uhid=f"UHID-{date.today().year}-000004", first_name="Lab", last_name="Patient")
    doctor_user = User(hospital_id=hospital.id, username="labdoc", email="labdoc@test.com", password_hash=get_password_hash("doc123"), full_name="Lab Doctor", role=UserRole.DOCTOR, is_active=True)
    db.add_all([patient, doctor_user])
    db.flush()
    doctor = Doctor(user_id=doctor_user.id, hospital_id=hospital.id, employee_code="DOC002", specialization="Pathology", department_id=dept.id)
    test = LabTest(hospital_id=hospital.id, test_name="CBC", test_code="CBC01", price=100)
    db.add_all([doctor, test])
    db.commit()
    login(client)
    response = client.post("/laboratory/orders", data={"patient_id": patient.id, "doctor_id": doctor.id, "test_ids": f"[{test.id}]"})
    assert response.status_code == 200
    assert response.json()["message"] == "Lab order created"


def test_settings_create_user(client, db):
    hospital, dept, user = seed_auth_data(db)
    login(client)
    response = client.post("/settings/users", data={"hospital_id": hospital.id, "username": "newuser", "email": "new@user.com", "password": "password123", "full_name": "New User", "role": "RECEPTIONIST"})
    assert response.status_code == 200
    assert response.json()["message"] == "User created"
