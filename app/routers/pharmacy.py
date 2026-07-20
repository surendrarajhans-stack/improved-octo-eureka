from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.pharmacy import Medicine, MedicineStock, PharmacyOrder, PharmacyOrderItem
from app.schemas.pharmacy import (
    MedicineCreate,
    MedicineResponse,
    MedicineStockCreate,
    MedicineStockResponse,
    MedicineUpdate,
    PharmacyOrderCreate,
    PharmacyOrderItemCreate,
    PharmacyOrderItemResponse,
    PharmacyOrderResponse,
    PharmacyOrderUpdate,
)
from app.services.pharmacy_service import get_low_stock_medicines

router = APIRouter(prefix="/pharmacy", tags=["Pharmacy"])


@router.get("/medicines", response_model=list[MedicineResponse])
async def list_medicines(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Medicine).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/medicines", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED
)
async def create_medicine(
    data: MedicineCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    medicine = Medicine(**data.model_dump())
    db.add(medicine)
    await db.flush()
    await db.refresh(medicine)
    return medicine


@router.get("/medicines/low-stock", response_model=list[MedicineResponse])
async def low_stock_medicines(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_low_stock_medicines(db)


@router.get("/medicines/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(
    medicine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id))
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine


@router.put("/medicines/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: int,
    data: MedicineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id))
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(medicine, key, value)
    await db.flush()
    await db.refresh(medicine)
    return medicine


@router.delete("/medicines/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(
    medicine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id))
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    medicine.is_available = False
    await db.flush()


@router.get("/orders", response_model=list[PharmacyOrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PharmacyOrder).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/orders", response_model=PharmacyOrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_order(
    data: PharmacyOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = PharmacyOrder(**data.model_dump())
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


@router.get("/orders/{order_id}", response_model=PharmacyOrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PharmacyOrder).where(PharmacyOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Pharmacy order not found")
    return order


@router.put("/orders/{order_id}", response_model=PharmacyOrderResponse)
async def update_order(
    order_id: int,
    data: PharmacyOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PharmacyOrder).where(PharmacyOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Pharmacy order not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    await db.flush()
    await db.refresh(order)
    return order


@router.post(
    "/order-items",
    response_model=PharmacyOrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order_item(
    data: PharmacyOrderItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = PharmacyOrderItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.post(
    "/stock", response_model=MedicineStockResponse, status_code=status.HTTP_201_CREATED
)
async def add_stock(
    data: MedicineStockCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stock = MedicineStock(**data.model_dump())
    db.add(stock)

    # Update medicine current stock
    result = await db.execute(select(Medicine).where(Medicine.id == data.medicine_id))
    medicine = result.scalar_one_or_none()
    if medicine:
        medicine.current_stock += data.quantity_added
        medicine.current_stock -= data.quantity_used

    await db.flush()
    await db.refresh(stock)
    return stock
