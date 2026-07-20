from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.notification import Notification
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications")


@router.get("")
def notification_list(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter((Notification.user_id == current_user.id) | (Notification.user_id.is_(None))).order_by(Notification.created_at.desc()).all()
    return render(request, "reports/dashboard.html", db, current_user, notifications=notifications, notifications_mode=True)


@router.post("/mark-read/{notification_id}")
def mark_read(notification_id: int, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    notification.status = "READ"
    notification.read_at = datetime.utcnow()
    db.commit()
    return JSONResponse({"message": "Marked as read"})


@router.get("/unread-count")
def unread_count(current_user=Depends(require_auth), db: Session = Depends(get_db)):
    count = db.query(func.count(Notification.id)).filter(Notification.user_id == current_user.id, Notification.status != "READ").scalar() or 0
    return {"count": count}


@router.post("/send")
async def send_notification(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    notification = NotificationService(db).create_notification(int(data["user_id"]) if data.get("user_id") else None, data.get("type", "EMAIL"), data["subject"], data["message"], int(data["patient_id"]) if data.get("patient_id") else None)
    return JSONResponse({"message": "Notification sent", "id": notification.id})
