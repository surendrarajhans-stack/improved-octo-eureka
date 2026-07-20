"""Comprehensive tests for HMS."""

from httpx import AsyncClient


class TestAuth:
    async def test_register_first_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register/first",
            json={
                "username": "admin",
                "email": "admin@test.com",
                "password": "admin123",
                "full_name": "Admin User",
                "role": "ADMIN",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "ADMIN"

    async def test_login(self, client: AsyncClient, admin_token: str):
        assert admin_token is not None
        assert len(admin_token) > 10

    async def test_login_invalid_credentials(self, client: AsyncClient):
        # Create admin first
        await client.post(
            "/auth/register/first",
            json={
                "username": "admin",
                "email": "admin@test.com",
                "password": "admin123",
                "full_name": "Admin User",
                "role": "ADMIN",
            },
        )
        resp = await client.post(
            "/auth/login",
            data={"username": "admin", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    async def test_get_me(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"

    async def test_register_user_as_admin(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/auth/register",
            json={
                "username": "doctor1",
                "email": "doctor1@test.com",
                "password": "doc123",
                "full_name": "Dr. Test",
                "role": "DOCTOR",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "DOCTOR"

    async def test_cannot_register_second_admin_without_token(self, client: AsyncClient):
        # First user
        await client.post(
            "/auth/register/first",
            json={
                "username": "admin",
                "email": "admin@test.com",
                "password": "admin123",
                "full_name": "Admin",
                "role": "ADMIN",
            },
        )
        # Second call to /register/first should fail
        resp = await client.post(
            "/auth/register/first",
            json={
                "username": "admin2",
                "email": "admin2@test.com",
                "password": "admin123",
                "full_name": "Admin2",
                "role": "ADMIN",
            },
        )
        assert resp.status_code == 400


class TestDepartments:
    async def test_create_department(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/departments/",
            json={"name": "Cardiology", "description": "Heart department"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Cardiology"

    async def test_list_departments(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/departments/",
            json={"name": "Neurology"},
            headers=auth_headers,
        )
        resp = await client.get("/departments/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_department(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/departments/",
            json={"name": "Oncology"},
            headers=auth_headers,
        )
        dept_id = create_resp.json()["id"]
        resp = await client.get(f"/departments/{dept_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Oncology"

    async def test_update_department(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/departments/",
            json={"name": "Old Name"},
            headers=auth_headers,
        )
        dept_id = create_resp.json()["id"]
        resp = await client.put(
            f"/departments/{dept_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    async def test_delete_department(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/departments/",
            json={"name": "ToDelete"},
            headers=auth_headers,
        )
        dept_id = create_resp.json()["id"]
        resp = await client.delete(f"/departments/{dept_id}", headers=auth_headers)
        assert resp.status_code == 204


class TestPatients:
    async def test_create_patient(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/patients/",
            json={
                "full_name": "John Patient",
                "phone": "1234567890",
                "gender": "Male",
                "blood_group": "O+",
                "dob": "1990-01-01",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["full_name"] == "John Patient"
        assert "patient_id" in data
        assert data["patient_id"].startswith("P-")

    async def test_list_patients(self, client: AsyncClient, auth_headers: dict):
        for i in range(3):
            await client.post(
                "/patients/",
                json={"full_name": f"Patient {i}", "phone": f"123456789{i}"},
                headers=auth_headers,
            )
        resp = await client.get("/patients/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_get_patient(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/patients/",
            json={"full_name": "Jane Patient", "phone": "9999999999"},
            headers=auth_headers,
        )
        patient_id = create_resp.json()["id"]
        resp = await client.get(f"/patients/{patient_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Jane Patient"

    async def test_update_patient(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post(
            "/patients/",
            json={"full_name": "Original Name", "phone": "1111111111"},
            headers=auth_headers,
        )
        patient_id = create_resp.json()["id"]
        resp = await client.put(
            f"/patients/{patient_id}",
            json={"full_name": "Updated Name", "phone": "2222222222"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    async def test_patient_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/patients/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestDoctors:
    async def _create_dept_and_user(self, client, auth_headers):
        dept = await client.post(
            "/departments/", json={"name": "Test Dept"}, headers=auth_headers
        )
        user = await client.post(
            "/auth/register",
            json={
                "username": "testdoc",
                "email": "testdoc@test.com",
                "password": "doc123",
                "full_name": "Test Doc",
                "role": "DOCTOR",
            },
            headers=auth_headers,
        )
        return dept.json()["id"], user.json()["id"]

    async def test_create_doctor(self, client: AsyncClient, auth_headers: dict):
        dept_id, user_id = await self._create_dept_and_user(client, auth_headers)
        resp = await client.post(
            "/doctors/",
            json={
                "user_id": user_id,
                "department_id": dept_id,
                "specialization": "Cardiology",
                "qualification": "MBBS, MD",
                "license_number": "DOC001",
                "consultation_fee": 500.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["specialization"] == "Cardiology"

    async def test_list_doctors(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/doctors/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAppointments:
    async def _setup(self, client, auth_headers):
        """Create patient, dept, user, doctor."""
        dept = await client.post(
            "/departments/", json={"name": "Test Dept"}, headers=auth_headers
        )
        patient = await client.post(
            "/patients/",
            json={"full_name": "Test Patient", "phone": "1234567890"},
            headers=auth_headers,
        )
        user = await client.post(
            "/auth/register",
            json={
                "username": "doc_appt",
                "email": "docappt@test.com",
                "password": "doc123",
                "full_name": "Appt Doctor",
                "role": "DOCTOR",
            },
            headers=auth_headers,
        )
        doctor = await client.post(
            "/doctors/",
            json={
                "user_id": user.json()["id"],
                "department_id": dept.json()["id"],
                "specialization": "General",
                "qualification": "MBBS",
                "license_number": "A001",
                "consultation_fee": 300.0,
            },
            headers=auth_headers,
        )
        return dept.json()["id"], patient.json()["id"], doctor.json()["id"]

    async def test_create_appointment(self, client: AsyncClient, auth_headers: dict):
        dept_id, patient_id, doctor_id = await self._setup(client, auth_headers)
        resp = await client.post(
            "/appointments/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "department_id": dept_id,
                "appointment_date": "2026-08-01",
                "appointment_time": "10:00:00",
                "reason": "Routine checkup",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "SCHEDULED"

    async def test_confirm_appointment(self, client: AsyncClient, auth_headers: dict):
        dept_id, patient_id, doctor_id = await self._setup(client, auth_headers)
        create = await client.post(
            "/appointments/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "department_id": dept_id,
                "appointment_date": "2026-08-01",
                "appointment_time": "10:00:00",
            },
            headers=auth_headers,
        )
        appt_id = create.json()["id"]
        resp = await client.post(
            f"/appointments/{appt_id}/confirm", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CONFIRMED"

    async def test_cancel_appointment(self, client: AsyncClient, auth_headers: dict):
        dept_id, patient_id, doctor_id = await self._setup(client, auth_headers)
        create = await client.post(
            "/appointments/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "department_id": dept_id,
                "appointment_date": "2026-08-01",
                "appointment_time": "11:00:00",
            },
            headers=auth_headers,
        )
        appt_id = create.json()["id"]
        resp = await client.post(
            f"/appointments/{appt_id}/cancel", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"


class TestBilling:
    async def _create_patient(self, client, auth_headers):
        resp = await client.post(
            "/patients/",
            json={"full_name": "Billing Patient", "phone": "5555555555"},
            headers=auth_headers,
        )
        return resp.json()["id"]

    async def test_create_invoice(self, client: AsyncClient, auth_headers: dict):
        patient_id = await self._create_patient(client, auth_headers)
        resp = await client.post(
            "/billing/invoices",
            json={
                "patient_id": patient_id,
                "total_amount": 1000.0,
                "paid_amount": 0.0,
                "discount": 0.0,
                "tax": 0.0,
                "status": "PENDING",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["invoice_number"].startswith("INV-")
        assert data["total_amount"] == 1000.0

    async def test_pay_invoice(self, client: AsyncClient, auth_headers: dict):
        patient_id = await self._create_patient(client, auth_headers)
        invoice_resp = await client.post(
            "/billing/invoices",
            json={
                "patient_id": patient_id,
                "total_amount": 500.0,
                "paid_amount": 0.0,
                "status": "PENDING",
            },
            headers=auth_headers,
        )
        invoice_id = invoice_resp.json()["id"]

        pay_resp = await client.post(
            f"/billing/invoices/{invoice_id}/pay",
            json={
                "invoice_id": invoice_id,
                "amount": 500.0,
                "payment_method": "CASH",
            },
            headers=auth_headers,
        )
        assert pay_resp.status_code == 200
        assert pay_resp.json()["amount"] == 500.0

    async def test_list_invoices(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/billing/invoices", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestPharmacy:
    async def test_create_medicine(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/pharmacy/medicines",
            json={
                "name": "Aspirin 100mg",
                "generic_name": "Aspirin",
                "category": "Analgesic",
                "unit": "Tablet",
                "unit_price": 1.5,
                "current_stock": 200,
                "reorder_level": 50,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Aspirin 100mg"

    async def test_list_medicines(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/pharmacy/medicines", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_pharmacy_order(self, client: AsyncClient, auth_headers: dict):
        # Create dependencies
        dept = await client.post(
            "/departments/", json={"name": "Pharma Dept"}, headers=auth_headers
        )
        patient = await client.post(
            "/patients/",
            json={"full_name": "Pharma Patient", "phone": "6666666666"},
            headers=auth_headers,
        )
        user = await client.post(
            "/auth/register",
            json={
                "username": "pharma_doc",
                "email": "pharmadoc@test.com",
                "password": "doc123",
                "full_name": "Pharma Doc",
                "role": "DOCTOR",
            },
            headers=auth_headers,
        )
        doctor = await client.post(
            "/doctors/",
            json={
                "user_id": user.json()["id"],
                "department_id": dept.json()["id"],
                "specialization": "General",
                "qualification": "MBBS",
                "license_number": "P001",
                "consultation_fee": 300.0,
            },
            headers=auth_headers,
        )

        resp = await client.post(
            "/pharmacy/orders",
            json={
                "patient_id": patient.json()["id"],
                "doctor_id": doctor.json()["id"],
                "total_amount": 100.0,
                "status": "PENDING",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "PENDING"


class TestLaboratory:
    async def test_create_lab_test(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/laboratory/tests",
            json={
                "name": "Blood Glucose",
                "category": "Biochemistry",
                "price": 80.0,
                "turnaround_hours": 12,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Blood Glucose"

    async def test_list_lab_tests(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/laboratory/tests", headers=auth_headers)
        assert resp.status_code == 200

    async def test_create_lab_order(self, client: AsyncClient, auth_headers: dict):
        dept = await client.post(
            "/departments/", json={"name": "Lab Dept"}, headers=auth_headers
        )
        patient = await client.post(
            "/patients/",
            json={"full_name": "Lab Patient", "phone": "7777777777"},
            headers=auth_headers,
        )
        user = await client.post(
            "/auth/register",
            json={
                "username": "lab_doc",
                "email": "labdoc@test.com",
                "password": "doc123",
                "full_name": "Lab Doc",
                "role": "DOCTOR",
            },
            headers=auth_headers,
        )
        doctor = await client.post(
            "/doctors/",
            json={
                "user_id": user.json()["id"],
                "department_id": dept.json()["id"],
                "specialization": "Pathology",
                "qualification": "MBBS",
                "license_number": "L001",
                "consultation_fee": 300.0,
            },
            headers=auth_headers,
        )
        resp = await client.post(
            "/laboratory/orders",
            json={
                "patient_id": patient.json()["id"],
                "doctor_id": doctor.json()["id"],
                "priority": "NORMAL",
                "total_amount": 200.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["priority"] == "NORMAL"


class TestDashboard:
    async def test_dashboard_stats(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_patients" in data
        assert "appointments_today" in data
        assert "bed_occupancy_rate" in data
        assert "revenue_today" in data

    async def test_recent_activity(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/dashboard/recent-activity", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "recent_appointments" in data
        assert "recent_admissions" in data
        assert "recent_payments" in data


class TestAI:
    async def test_predict_readmission(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/ai/predict-readmission",
            json={
                "patient_age": 70,
                "diagnosis": "Heart Failure",
                "previous_admissions": 2,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

    async def test_suggest_diagnosis(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/ai/suggest-diagnosis",
            json={"symptoms": ["fever", "cough", "headache"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    async def test_bed_occupancy_forecast(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/ai/bed-occupancy-forecast?days=7", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "forecast" in data
        assert "trend" in data


class TestReports:
    async def test_revenue_report(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/reports/revenue", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_revenue" in data

    async def test_patient_statistics(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/reports/patient-statistics", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_patients" in data

    async def test_department_performance(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/reports/department-performance", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_inventory_status(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/reports/inventory-status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_medicines" in data


class TestIPD:
    async def test_create_ward(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/ipd/wards",
            json={
                "name": "General Ward A",
                "ward_type": "GENERAL",
                "floor": 1,
                "capacity": 20,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["ward_type"] == "GENERAL"

    async def test_create_bed(self, client: AsyncClient, auth_headers: dict):
        ward_resp = await client.post(
            "/ipd/wards",
            json={"name": "Test Ward", "ward_type": "PRIVATE", "floor": 2, "capacity": 5},
            headers=auth_headers,
        )
        ward_id = ward_resp.json()["id"]
        resp = await client.post(
            "/ipd/beds",
            json={"bed_number": "B-001", "ward_id": ward_id, "status": "AVAILABLE"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "AVAILABLE"

    async def test_admit_patient(self, client: AsyncClient, auth_headers: dict):
        # Create ward, bed, patient, doctor
        ward = await client.post(
            "/ipd/wards",
            json={"name": "Admit Ward", "ward_type": "GENERAL", "floor": 1, "capacity": 10},
            headers=auth_headers,
        )
        ward_id = ward.json()["id"]
        bed = await client.post(
            "/ipd/beds",
            json={"bed_number": "A-001", "ward_id": ward_id, "status": "AVAILABLE"},
            headers=auth_headers,
        )
        bed_id = bed.json()["id"]

        dept = await client.post(
            "/departments/", json={"name": "IPD Dept"}, headers=auth_headers
        )
        patient = await client.post(
            "/patients/",
            json={"full_name": "IPD Patient", "phone": "8888888888"},
            headers=auth_headers,
        )
        user = await client.post(
            "/auth/register",
            json={
                "username": "ipd_doc",
                "email": "ipddoc@test.com",
                "password": "doc123",
                "full_name": "IPD Doctor",
                "role": "DOCTOR",
            },
            headers=auth_headers,
        )
        doctor = await client.post(
            "/doctors/",
            json={
                "user_id": user.json()["id"],
                "department_id": dept.json()["id"],
                "specialization": "Surgery",
                "qualification": "MBBS",
                "license_number": "I001",
                "consultation_fee": 700.0,
            },
            headers=auth_headers,
        )

        resp = await client.post(
            f"/ipd/beds/{bed_id}/admit-patient",
            json={
                "patient_id": patient.json()["id"],
                "doctor_id": doctor.json()["id"],
                "bed_id": bed_id,
                "diagnosis": "Appendicitis",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_discharged"] is False

    async def test_discharge_patient(self, client: AsyncClient, auth_headers: dict):
        # Create and admit patient
        ward = await client.post(
            "/ipd/wards",
            json={"name": "Discharge Ward", "ward_type": "GENERAL", "floor": 1, "capacity": 5},
            headers=auth_headers,
        )
        bed = await client.post(
            "/ipd/beds",
            json={"bed_number": "D-001", "ward_id": ward.json()["id"], "status": "AVAILABLE"},
            headers=auth_headers,
        )
        dept = await client.post(
            "/departments/", json={"name": "Disch Dept"}, headers=auth_headers
        )
        patient = await client.post(
            "/patients/",
            json={"full_name": "Discharge Patient", "phone": "9999999991"},
            headers=auth_headers,
        )
        user = await client.post(
            "/auth/register",
            json={
                "username": "disch_doc",
                "email": "dischdoc@test.com",
                "password": "doc123",
                "full_name": "Disch Doctor",
                "role": "DOCTOR",
            },
            headers=auth_headers,
        )
        doctor = await client.post(
            "/doctors/",
            json={
                "user_id": user.json()["id"],
                "department_id": dept.json()["id"],
                "specialization": "General",
                "qualification": "MBBS",
                "license_number": "D001",
                "consultation_fee": 500.0,
            },
            headers=auth_headers,
        )
        admission = await client.post(
            f"/ipd/beds/{bed.json()['id']}/admit-patient",
            json={
                "patient_id": patient.json()["id"],
                "doctor_id": doctor.json()["id"],
                "bed_id": bed.json()["id"],
            },
            headers=auth_headers,
        )
        admission_id = admission.json()["id"]

        resp = await client.post(
            f"/ipd/admissions/{admission_id}/discharge",
            params={"discharge_notes": "Recovered well"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_discharged"] is True
