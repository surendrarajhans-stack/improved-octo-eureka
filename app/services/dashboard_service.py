from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.billing import Invoice, Payment
from app.models.ipd import Admission, Bed, BedStatus
from app.models.master import Patient


async def get_dashboard_stats(db: AsyncSession) -> dict:
    today = date.today()

    # Total patients
    total_patients_result = await db.execute(select(func.count(Patient.id)))
    total_patients = total_patients_result.scalar() or 0

    # Appointments today
    appts_today_result = await db.execute(
        select(func.count(Appointment.id)).where(Appointment.appointment_date == today)
    )
    appointments_today = appts_today_result.scalar() or 0

    # Bed occupancy
    total_beds_result = await db.execute(select(func.count(Bed.id)))
    total_beds = total_beds_result.scalar() or 0

    occupied_beds_result = await db.execute(
        select(func.count(Bed.id)).where(Bed.status == BedStatus.OCCUPIED)
    )
    occupied_beds = occupied_beds_result.scalar() or 0

    # Revenue today (payments)
    revenue_today_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            func.date(Payment.payment_date) == today
        )
    )
    revenue_today = float(revenue_today_result.scalar() or 0)

    # Active admissions
    active_admissions_result = await db.execute(
        select(func.count(Admission.id)).where(Admission.is_discharged == False)  # noqa: E712
    )
    active_admissions = active_admissions_result.scalar() or 0

    # Pending invoices
    pending_invoices_result = await db.execute(
        select(func.sum(Invoice.total_amount - Invoice.paid_amount)).where(
            Invoice.status.in_(["PENDING", "PARTIALLY_PAID"])
        )
    )
    pending_revenue = float(pending_invoices_result.scalar() or 0)

    return {
        "total_patients": total_patients,
        "appointments_today": appointments_today,
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "bed_occupancy_rate": round(
            (occupied_beds / total_beds * 100) if total_beds > 0 else 0, 2
        ),
        "revenue_today": revenue_today,
        "active_admissions": active_admissions,
        "pending_revenue": pending_revenue,
    }


async def get_recent_activity(db: AsyncSession, limit: int = 10) -> dict:
    # Recent appointments
    recent_appts_result = await db.execute(
        select(Appointment).order_by(Appointment.created_at.desc()).limit(limit)
    )
    recent_appointments = recent_appts_result.scalars().all()

    # Recent admissions
    recent_admissions_result = await db.execute(
        select(Admission).order_by(Admission.admission_date.desc()).limit(limit)
    )
    recent_admissions = recent_admissions_result.scalars().all()

    # Recent payments
    recent_payments_result = await db.execute(
        select(Payment).order_by(Payment.payment_date.desc()).limit(limit)
    )
    recent_payments = recent_payments_result.scalars().all()

    return {
        "recent_appointments": [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "doctor_id": a.doctor_id,
                "appointment_date": str(a.appointment_date),
                "status": a.status.value if hasattr(a.status, "value") else a.status,
            }
            for a in recent_appointments
        ],
        "recent_admissions": [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "doctor_id": a.doctor_id,
                "admission_date": str(a.admission_date),
                "is_discharged": a.is_discharged,
            }
            for a in recent_admissions
        ],
        "recent_payments": [
            {
                "id": p.id,
                "invoice_id": p.invoice_id,
                "amount": float(p.amount),
                "payment_date": str(p.payment_date),
                "payment_method": (
                    p.payment_method.value if hasattr(p.payment_method, "value") else p.payment_method
                ),
            }
            for p in recent_payments
        ],
    }
