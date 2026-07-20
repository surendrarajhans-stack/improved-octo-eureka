from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import (
    ai_assistant,
    appointments,
    auth,
    billing,
    dashboard,
    departments,
    doctors,
    finance,
    hr,
    inventory,
    ipd,
    laboratory,
    opd,
    patients,
    payroll,
    pharmacy,
    radiology,
    reports,
    staff,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Complete Nursing Home / Hospital Management System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(departments.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(staff.router)
app.include_router(appointments.router)
app.include_router(opd.router)
app.include_router(ipd.router)
app.include_router(billing.router)
app.include_router(pharmacy.router)
app.include_router(laboratory.router)
app.include_router(radiology.router)
app.include_router(inventory.router)
app.include_router(hr.router)
app.include_router(payroll.router)
app.include_router(finance.router)
app.include_router(reports.router)
app.include_router(ai_assistant.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
