import base64
from datetime import date
from io import BytesIO

import qrcode
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.user import AuditLog

templates = Jinja2Templates(directory="templates")


def hospital_context(db: Session, user=None) -> dict:
    hospital = db.query(Hospital).first()
    unread_count = 0
    if user:
        unread_count = db.query(func.count(Notification.id)).filter(Notification.user_id == user.id, Notification.status != "READ").scalar() or 0
    return {"hospital": hospital, "current_user": user, "unread_count": unread_count}


async def parse_request_data(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    form = await request.form()
    return dict(form)


def render(request: Request, template: str, db: Session, user=None, **context):
    data = hospital_context(db, user)
    data.update(context)
    return templates.TemplateResponse(template, {"request": request, **data})


def json_message(message: str, **extra):
    payload = {"message": message}
    payload.update(extra)
    return JSONResponse(payload)


def redirect_with_message(url: str, message: str | None = None):
    response = RedirectResponse(url=url, status_code=303)
    if message:
        response.set_cookie("flash_message", message, max_age=10)
    return response


def generate_patient_uhid(db: Session) -> str:
    year = date.today().year
    prefix = f"UHID-{year}-"
    count = db.query(func.count(Patient.id)).filter(Patient.uhid.like(f"{prefix}%")).scalar() or 0
    return f"{prefix}{count + 1:06d}"


def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def paginate(query, page: int, per_page: int):
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def audit(db: Session, user_id: int | None, action: str, module: str, record_id: int | None, new_values=None, old_values=None, ip_address: str | None = None):
    log = AuditLog(user_id=user_id, action=action, module=module, record_id=record_id, new_values=new_values, old_values=old_values, ip_address=ip_address)
    db.add(log)
    db.commit()
    return log
