from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_token_from_request
from app.security import decode_access_token
from app.models import Patient

router = APIRouter(tags=["Frontend Views"])
templates = Jinja2Templates(directory="templates")

def get_current_user_from_cookie(request: Request):
    token = get_token_from_request(request)
    if not token:
        return None
    payload = decode_access_token(token)
    return payload

@router.get("/", response_class=HTMLResponse)
def index_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if user_payload:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")

from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse

@router.get("/manifest.json")
def manifest_view():
    data = {
        "id": "/",
        "name": "MedSphere AI Hospital Operating System",
        "short_name": "MedSphere AI",
        "description": "Next-Generation AI Operating System for Clinical Operations and Hospital Governance",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "dir": "ltr",
        "lang": "en",
        "background_color": "#0b0f19",
        "theme_color": "#0d9488",
        "orientation": "portrait-primary",
        "categories": ["medical", "business", "productivity"],
        "icons": [
            {
                "src": "https://hospital.technocons.com/static/launchericon-192x192.png",
                "type": "image/png",
                "sizes": "192x192",
                "purpose": "any maskable"
            },
            {
                "src": "https://hospital.technocons.com/static/launchericon-512x512.png",
                "type": "image/png",
                "sizes": "512x512",
                "purpose": "any maskable"
            }
        ]
    }
    return JSONResponse(content=data, headers={"Access-Control-Allow-Origin": "*"})

@router.get("/icon-192.png")
@router.get("/icon-512.png")
@router.get("/apple-touch-icon.png")
def icon_view():
    return FileResponse("static/icon.png", media_type="image/png", headers={"Access-Control-Allow-Origin": "*"})

@router.get("/sw.js")
@router.get("/service-worker.js")
def service_worker_view():
    sw_script = """
const CACHE_NAME = 'medsphere-v1';
self.addEventListener('install', event => {
  self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
"""
    return HTMLResponse(content=sw_script, media_type="application/javascript", headers={"Access-Control-Allow-Origin": "*"})

@router.get("/login", response_class=HTMLResponse)
def login_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if user_payload:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request=request, name="login.html")

@router.get("/register", response_class=HTMLResponse)
def register_view(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "user": user_payload,
        "active_page": "dashboard"
    })

@router.get("/users", response_class=HTMLResponse)
def users_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="users.html", context={
        "user": user_payload,
        "active_page": "users"
    })

@router.get("/patients", response_class=HTMLResponse)
def patients_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="patients.html", context={
        "user": user_payload,
        "active_page": "patients"
    })

@router.get("/patients/{patient_id}", response_class=HTMLResponse)
def patient_detail_view(patient_id: int, request: Request, db: Session = Depends(get_db)):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return templates.TemplateResponse(request=request, name="patient_detail.html", context={
        "user": user_payload,
        "patient": patient,
        "active_page": "patients"
    })

@router.get("/appointments", response_class=HTMLResponse)
def appointments_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="appointments.html", context={
        "user": user_payload,
        "active_page": "appointments"
    })

@router.get("/prescriptions", response_class=HTMLResponse)
def prescriptions_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="prescriptions.html", context={
        "user": user_payload,
        "active_page": "prescriptions"
    })

@router.get("/billing", response_class=HTMLResponse)
def billing_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="billing.html", context={
        "user": user_payload,
        "active_page": "billing"
    })

@router.get("/inventory", response_class=HTMLResponse)
def inventory_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="inventory.html", context={
        "user": user_payload,
        "active_page": "inventory"
    })

@router.get("/lab", response_class=HTMLResponse)
def lab_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="lab.html", context={
        "user": user_payload,
        "active_page": "lab"
    })

@router.get("/audit", response_class=HTMLResponse)
def audit_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="audit.html", context={
        "user": user_payload,
        "active_page": "audit"
    })

@router.get("/ai-assistant", response_class=HTMLResponse)
def ai_assistant_view(request: Request):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="ai_assistant.html", context={
        "user": user_payload,
        "active_page": "ai-assistant"
    })
