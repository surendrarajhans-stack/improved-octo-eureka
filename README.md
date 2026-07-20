# HMS - Complete Nursing Home Management System

## Setup

```bash
pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-settings \
    "python-jose[cryptography]" "passlib[bcrypt]" python-multipart \
    httpx pytest pytest-asyncio aiosqlite greenlet "pydantic[email]"
cp .env.example .env
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

## Testing

```bash
pip install ruff
python -m ruff check .
pytest tests/test_app.py -v
```

## API Documentation

Visit http://localhost:8000/docs for Swagger UI.

## Default Credentials

- Admin: username=`admin` / ******
- Doctor: username=`dr_john` / ******
- Staff: username=`nurse_ann` / ******

## Modules

- **Authentication & RBAC** – JWT tokens, role-based access (Admin, Doctor, Nurse, Receptionist, Pharmacist, Lab Technician, Radiologist, HR, Accountant, Patient)
- **Dashboard & Analytics** – Real-time stats: patients today, appointments, bed occupancy, revenue
- **Master Data** – Departments, Doctors, Patients, Staff
- **Appointments & Reception** – Schedule, confirm, cancel appointments
- **OPD Management** – Visits, prescriptions, vital signs
- **IPD & Bed Management** – Wards, beds, admissions, daily rounds, discharge
- **Billing & Payments** – Invoices, payments (Cash/Card/Insurance/Online/Cheque), insurance claims
- **Pharmacy** – Medicines, orders, stock management
- **Laboratory** – Tests, orders, results
- **Radiology** – Tests (X-Ray/CT/MRI/Ultrasound), orders, results
- **Inventory Management** – Items, purchase orders, stock movements
- **HR & Payroll** – Employees, leave requests, attendance, payroll, salary components
- **Finance & Accounting** – Chart of accounts, double-entry transactions, budgets
- **Reports & Analytics** – Revenue, patient stats, department performance, inventory status
- **AI Assistant & Predictive Features** – Readmission risk prediction, diagnosis suggestions, bed occupancy forecast

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database ORM**: SQLAlchemy 2.0 with async support
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Testing**: pytest + httpx AsyncClient
- **Linting**: ruff

