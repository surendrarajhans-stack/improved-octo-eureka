from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_auth
from app.api.routes.helpers import parse_request_data, render
from app.database import get_db
from app.models.ambulance import AmbulanceTrip, Vehicle

router = APIRouter(prefix="/ambulance")


@router.get("")
def dashboard(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    trips = db.query(AmbulanceTrip).order_by(AmbulanceTrip.start_time.desc()).limit(10).all()
    return render(request, "reports/dashboard.html", db, current_user, vehicles=vehicles, trips=trips, ambulance_mode=True)


@router.get("/vehicles")
def vehicles(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    return render(request, "reports/dashboard.html", db, current_user, vehicles=vehicles, ambulance_mode=True)


@router.post("/vehicles")
async def add_vehicle(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    vehicle = Vehicle(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), registration_no=data["registration_no"], vehicle_type=data["vehicle_type"], model=data.get("model"), capacity=int(data.get("capacity") or 1), driver_id=int(data["driver_id"]) if data.get("driver_id") else None, gps_device_id=data.get("gps_device_id"), status=data.get("status", "AVAILABLE"), last_location=data.get("last_location"))
    db.add(vehicle)
    db.commit()
    return JSONResponse({"message": "Vehicle added", "id": vehicle.id})


@router.get("/trips")
def trips(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    trips = db.query(AmbulanceTrip).order_by(AmbulanceTrip.start_time.desc()).all()
    return render(request, "reports/dashboard.html", db, current_user, trips=trips, ambulance_mode=True)


@router.post("/trips")
async def create_trip(request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    data = await parse_request_data(request)
    trip = AmbulanceTrip(hospital_id=int(data.get("hospital_id") or current_user.hospital_id or 1), vehicle_id=int(data["vehicle_id"]), driver_id=int(data["driver_id"]), patient_id=int(data["patient_id"]) if data.get("patient_id") else None, pickup_address=data.get("pickup_address"), destination=data.get("destination"), trip_type=data["trip_type"], start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None, end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None, distance_km=float(data.get("distance_km") or 0), fare=float(data.get("fare") or 0), status=data.get("status", "REQUESTED"), notes=data.get("notes"))
    db.add(trip)
    db.commit()
    return JSONResponse({"message": "Trip created", "id": trip.id})


@router.put("/trips/{trip_id}/status")
async def update_trip_status(trip_id: int, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    trip = db.query(AmbulanceTrip).filter(AmbulanceTrip.id == trip_id).first()
    data = await parse_request_data(request)
    trip.status = data.get("status", trip.status)
    db.commit()
    return JSONResponse({"message": "Trip updated"})
