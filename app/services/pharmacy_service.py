from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pharmacy import Medicine, MedicineStock


async def dispense_medicine(
    db: AsyncSession, medicine_id: int, quantity: int, reference_id: str = ""
) -> None:
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id))
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    if medicine.current_stock < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {medicine.current_stock}",
        )

    medicine.current_stock -= quantity
    stock_entry = MedicineStock(
        medicine_id=medicine_id,
        quantity_added=0,
        quantity_used=quantity,
        transaction_type="OUT",
        reference_id=reference_id,
    )
    db.add(stock_entry)


async def restock_medicine(
    db: AsyncSession, medicine_id: int, quantity: int, reference_id: str = ""
) -> None:
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id))
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    medicine.current_stock += quantity
    stock_entry = MedicineStock(
        medicine_id=medicine_id,
        quantity_added=quantity,
        quantity_used=0,
        transaction_type="IN",
        reference_id=reference_id,
    )
    db.add(stock_entry)


async def get_low_stock_medicines(db: AsyncSession) -> list:
    result = await db.execute(
        select(Medicine).where(
            Medicine.current_stock <= Medicine.reorder_level
        )
    )
    return result.scalars().all()
