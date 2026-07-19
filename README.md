# Nursing Home Management System

A production-oriented MVP backend for nursing home operations built with **FastAPI**, **SQLAlchemy**, **Alembic**, and **JWT-based authentication**.

## Included modules

- Secure auth with password hashing, JWT login, profile management, and RBAC
- Resident management with demographics, emergency contacts, allergies, conditions, status audit trail, and room/bed history
- Clinical workflows: care plans, vitals, medication orders, MAR basics, progress notes, and incident reporting
- Staffing and operations: shifts, attendance, task board, inventory, appointments, notifications, and secure messaging
- Billing: configurable payers, invoices, line items, payments, balances, monthly statements, and receivables dashboard metrics
- Family portal endpoints for approved updates, visit schedule, billing visibility, and messaging
- Immutable audit log endpoints for compliance-oriented traceability

## Stack

- FastAPI API server
- SQLAlchemy ORM
- Alembic migrations
- SQLite for quick local setup, PostgreSQL-ready via Docker Compose
- Pytest + FastAPI TestClient for integration coverage
- Ruff for linting/formatting

## Quick start

1. Copy environment values:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Apply migrations:
   ```bash
   alembic upgrade head
   ```
4. Seed demo data:
   ```bash
   python scripts/seed.py
   ```
5. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Open docs at `http://127.0.0.1:8000/docs`

## Docker

```bash
docker compose up --build
```

## Demo credentials

Created by `python scripts/seed.py`:

- `admin@example.com` / `AdminPass123!`
- `doctor@example.com` / `DoctorPass123!`
- `nurse@example.com` / `NursePass123!`
- `accountant@example.com` / `AccountPass123!`
- `family@example.com` / `FamilyPass123!`

## Core API overview

### Auth and users
- `POST /auth/signup` - self-register as `FamilyMember`
- `POST /auth/login` - obtain bearer token
- `GET /users/me` / `PATCH /users/me` - profile management
- `POST /users` - admin-only staff/user creation
- `GET /users` - admin/reception list users

### Residents
- `POST /residents`, `GET /residents`, `GET /residents/{id}`, `PATCH /residents/{id}`, `DELETE /residents/{id}`
- `POST /residents/{id}/status`
- `POST /residents/{id}/room-assignments`
- `POST /residents/{id}/family-links`

### Clinical
- `POST /residents/{id}/care-plans`
- `POST /residents/{id}/vitals`, `GET /residents/{id}/vitals`
- `POST /residents/{id}/medication-orders`
- `POST /medication-orders/{id}/administrations`
- `GET /residents/{id}/mar`
- `POST /residents/{id}/notes`, `GET /residents/{id}/notes`
- `POST /incidents`, `GET /clinical/due-medications`, `GET /reports/incidents`

### Scheduling and operations
- `POST /scheduling/shifts`
- `POST /scheduling/attendance`
- `POST /scheduling/tasks`, `GET /scheduling/tasks`
- `POST /operations/inventory-items`, `GET /operations/inventory-items`
- `POST /operations/inventory-usage`
- `POST /operations/appointments`
- `GET /notifications`
- `POST /messages`, `GET /messages`

### Billing and dashboards
- `POST /billing/payers`
- `POST /billing/invoices`, `GET /billing/invoices/{id}`
- `POST /billing/invoices/{id}/payments`
- `GET /billing/statements/monthly`
- `GET /dashboard/admin`
- `GET /audit-logs`

### Family portal
- `POST /family/updates`
- `GET /family/portal/updates`
- `GET /family/portal/visit-schedule`

## Validation and tests

Run linting:
```bash
python -m ruff check .
python -m ruff format --check .
```

Run tests:
```bash
pytest
```

## Architecture notes

- Public self-signup is restricted to family portal users; staff creation is intended to happen through controlled admin workflows or seed/bootstrap flows.
- Audit logs are append-only and capture key auth, resident, clinical, billing, messaging, and operational events.
- Residents and users use soft deletes where destructive removal would harm traceability.
- This MVP is API-first. FastAPI's OpenAPI/Swagger UI acts as the initial operator and integration surface.

## Known gaps / assumptions

- No dedicated browser frontend is included; the API and generated docs provide the primary interaction surface.
- Notifications are in-app and query-driven; there is no email/SMS delivery worker yet.
- The initial migration uses metadata-driven table creation for a compact bootstrap.
