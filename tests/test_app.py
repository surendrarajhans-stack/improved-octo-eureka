from datetime import date, datetime, timezone

from app import models
from app.enums import MedicationAdministrationStatus, PayerCategory, Role
from app.security import get_password_hash


def create_staff_user(db_session, email: str, role: Role) -> models.User:
    user = models.User(
        email=email,
        full_name=email.split("@")[0].title(),
        password_hash=get_password_hash("Password123!"),
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def login_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": " ".join(["Bearer", token])}


def create_resident(client, headers: dict[str, str]) -> int:
    response = client.post(
        "/residents",
        headers=headers,
        json={
            "first_name": "Martha",
            "last_name": "Jones",
            "date_of_birth": "1948-03-10",
            "gender": "Female",
            "emergency_contacts": [{"name": "Paul Jones", "phone": "555-9000"}],
            "allergies": ["Latex"],
            "conditions": ["COPD"],
            "preferred_pharmacy": "North Pharmacy",
            "primary_physician": "Dr. Stone",
            "room_number": "201",
            "bed_number": "B",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_auth_signup_login_and_profile(client):
    signup = client.post(
        "/auth/signup",
        json={
            "email": "family@example.com",
            "full_name": "Family Member",
            "password": "Password123!",
            "role": "Admin",
        },
    )
    assert signup.status_code == 201, signup.text
    assert signup.json()["role"] == "FamilyMember"

    login = client.post(
        "/auth/login",
        json={"email": "family@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    me = client.get("/users/me", headers={"Authorization": " ".join(["Bearer", token])})
    assert me.status_code == 200
    assert me.json()["email"] == "family@example.com"


def test_resident_crud_and_status_history(client, db_session):
    create_staff_user(db_session, "nurse@example.com", Role.NURSE)
    headers = login_headers(client, "nurse@example.com", "Password123!")

    resident_id = create_resident(client, headers)

    update = client.patch(
        f"/residents/{resident_id}",
        headers=headers,
        json={"room_number": "301", "bed_number": "A", "allergies": ["Latex", "Peanuts"]},
    )
    assert update.status_code == 200, update.text
    assert update.json()["room_number"] == "301"

    status_change = client.post(
        f"/residents/{resident_id}/status",
        headers=headers,
        json={"new_status": "hospitalized", "reason": "ER transfer"},
    )
    assert status_change.status_code == 200, status_change.text
    assert status_change.json()["status"] == "hospitalized"


def test_medication_administration_flow(client, db_session):
    create_staff_user(db_session, "nurse@example.com", Role.NURSE)
    create_staff_user(db_session, "doctor@example.com", Role.DOCTOR)
    headers = login_headers(client, "nurse@example.com", "Password123!")
    doctor_headers = login_headers(client, "doctor@example.com", "Password123!")
    resident_id = create_resident(client, headers)

    order = client.post(
        f"/residents/{resident_id}/medication-orders",
        headers=doctor_headers,
        json={
            "medication_name": "Metformin",
            "dosage": "500 mg",
            "route": "PO",
            "schedule_time": "09:00",
            "prn": False,
        },
    )
    assert order.status_code == 201, order.text
    order_id = order.json()["id"]

    administration = client.post(
        f"/medication-orders/{order_id}/administrations",
        headers=headers,
        json={
            "resident_id": resident_id,
            "status": MedicationAdministrationStatus.ADMINISTERED,
            "scheduled_for": datetime.now(timezone.utc).isoformat(),
            "administered_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Given with water",
        },
    )
    assert administration.status_code == 201, administration.text

    mar = client.get(f"/residents/{resident_id}/mar", headers=headers)
    assert mar.status_code == 200, mar.text
    assert mar.json()[0]["administrations"][0]["status"] == "administered"


def test_billing_payment_updates_balance(client, db_session):
    create_staff_user(db_session, "nurse@example.com", Role.NURSE)
    create_staff_user(db_session, "accountant@example.com", Role.ACCOUNTANT)
    nurse_headers = login_headers(client, "nurse@example.com", "Password123!")
    accountant_headers = login_headers(client, "accountant@example.com", "Password123!")
    resident_id = create_resident(client, nurse_headers)

    payer = client.post(
        "/billing/payers",
        headers=accountant_headers,
        json={"name": "Private Pay", "category": PayerCategory.PRIVATE, "configuration": {}},
    )
    assert payer.status_code == 201, payer.text
    payer_id = payer.json()["id"]

    invoice = client.post(
        "/billing/invoices",
        headers=accountant_headers,
        json={
            "resident_id": resident_id,
            "payer_id": payer_id,
            "invoice_month": date.today().strftime("%Y-%m"),
            "due_date": date.today().isoformat(),
            "line_items": [
                {"description": "Room and board", "amount": 1200.0},
                {"description": "Supplies", "amount": 150.0},
            ],
        },
    )
    assert invoice.status_code == 201, invoice.text
    assert invoice.json()["balance"] == 1350.0

    payment = client.post(
        f"/billing/invoices/{invoice.json()['id']}/payments",
        headers=accountant_headers,
        json={"amount": 350.0, "reference": "CHK-350"},
    )
    assert payment.status_code == 200, payment.text
    assert payment.json()["paid_amount"] == 350.0
    assert payment.json()["balance"] == 1000.0
