from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # noqa: F401
from app.api.routes import (
    ai,
    ambulance,
    appointments,
    auth,
    billing,
    dashboard,
    doctors,
    emergency,
    finance,
    hr,
    insurance,
    inventory,
    ipd,
    laboratory,
    notifications,
    opd,
    patients,
    pharmacy,
    radiology,
    reports,
    settings,
)
from app.api.routes.helpers import templates
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Hospital Management System", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router, tags=["Auth"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(opd.router, tags=["OPD"])
app.include_router(ipd.router, tags=["IPD"])
app.include_router(emergency.router, tags=["Emergency"])
app.include_router(laboratory.router, tags=["Laboratory"])
app.include_router(radiology.router, tags=["Radiology"])
app.include_router(pharmacy.router, tags=["Pharmacy"])
app.include_router(billing.router, tags=["Billing"])
app.include_router(insurance.router, tags=["Insurance"])
app.include_router(inventory.router, tags=["Inventory"])
app.include_router(hr.router, tags=["HR"])
app.include_router(finance.router, tags=["Finance"])
app.include_router(ambulance.router, tags=["Ambulance"])
app.include_router(reports.router, tags=["Reports"])
app.include_router(ai.router, tags=["AI"])
app.include_router(notifications.router, tags=["Notifications"])
app.include_router(settings.router, tags=["Settings"])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code in {302, 303, 307} and exc.headers and exc.headers.get("Location"):
        return RedirectResponse(exc.headers["Location"], status_code=exc.status_code)
    template = "errors/404.html" if exc.status_code == 404 else "errors/500.html"
    return templates.TemplateResponse(template, {"request": request, "detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse({"detail": exc.errors()}, status_code=422)


@app.exception_handler(Exception)
async def server_error(request: Request, exc: Exception):
    return templates.TemplateResponse("errors/500.html", {"request": request, "detail": str(exc)}, status_code=500)


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
