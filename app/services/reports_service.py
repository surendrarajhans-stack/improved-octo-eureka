from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.models.master import Department, Patient
from app.models.pharmacy import Medicine


async def get_patient_statistics(db: AsyncSession) -> dict:
    total_result = await db.execute(select(func.count(Patient.id)))
    total = total_result.scalar() or 0

    today = date.today()
    new_today_result = await db.execute(
        select(func.count(Patient.id)).where(
            func.date(Patient.created_at) == today
        )
    )
    new_today = new_today_result.scalar() or 0

    gender_result = await db.execute(
        select(Patient.gender, func.count(Patient.id)).group_by(Patient.gender)
    )
    by_gender = {
        str(row[0] or "Unknown"): int(row[1]) for row in gender_result.all()
    }

    return {
        "total_patients": total,
        "new_patients_today": new_today,
        "by_gender": by_gender,
    }


async def get_department_performance(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Department).where(Department.is_active == True))  # noqa: E712
    departments = result.scalars().all()

    performance = []
    for dept in departments:
        appt_result = await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.department_id == dept.id
            )
        )
        total_appointments = appt_result.scalar() or 0

        completed_result = await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.department_id == dept.id,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
        )
        completed = completed_result.scalar() or 0

        performance.append(
            {
                "department_id": dept.id,
                "department_name": dept.name,
                "total_appointments": total_appointments,
                "completed_appointments": completed,
                "completion_rate": round(
                    (completed / total_appointments * 100) if total_appointments > 0 else 0,
                    2,
                ),
            }
        )

    return performance


async def get_inventory_status(db: AsyncSession) -> dict:
    low_stock_result = await db.execute(
        select(func.count(Medicine.id)).where(
            Medicine.current_stock <= Medicine.reorder_level
        )
    )
    low_stock_count = low_stock_result.scalar() or 0

    out_of_stock_result = await db.execute(
        select(func.count(Medicine.id)).where(Medicine.current_stock == 0)
    )
    out_of_stock = out_of_stock_result.scalar() or 0

    total_result = await db.execute(select(func.count(Medicine.id)))
    total = total_result.scalar() or 0

    return {
        "total_medicines": total,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock,
        "adequate_stock_count": total - low_stock_count,
    }
