# AI Hospital Management System

Production-ready FastAPI hospital management platform with JWT auth, SQLAlchemy ORM, Alembic migrations, Bootstrap/Jinja UI, analytics, billing, diagnostics, pharmacy, HR, finance, ambulance, reports, and rule-based AI insights.

## Quick Start

```bash
python -m pip install -e ".[dev]"
alembic upgrade head
python scripts/seed.py
uvicorn main:app --reload
```

Login with `admin / admin123` after seeding.

## Features

- Patient registration with UHID and QR support
- Doctor scheduling and appointment queue
- OPD/IPD/emergency workflows
- Laboratory, radiology, pharmacy, billing, insurance, inventory
- HR, finance, ambulance, notifications, reports
- AI forecasts for revenue, patient load, bed occupancy, medicine demand

## Development

```bash
python -m ruff check . --fix
pytest tests/test_app.py -v
```
