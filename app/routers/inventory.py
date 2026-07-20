from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.inventory import InventoryItem, PurchaseOrder, PurchaseOrderItem, StockMovement
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderItemResponse,
    PurchaseOrderItemUpdate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    StockMovementCreate,
    StockMovementResponse,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


async def _generate_po_number(db: AsyncSession) -> str:
    year = datetime.now().year
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.po_number.like(f"PO-{year}-%")
        )
    )
    count = result.scalar() or 0
    return f"PO-{year}-{count + 1:04d}"


@router.get("/items", response_model=list[InventoryItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED
)
async def create_item(
    data: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = InventoryItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_item(
    item_id: int,
    data: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    await db.delete(item)
    await db.flush()


@router.get("/purchase-orders", response_model=list[PurchaseOrderResponse])
async def list_pos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PurchaseOrder).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_po(
    data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    po_number = await _generate_po_number(db)
    po = PurchaseOrder(**data.model_dump(), po_number=po_number)
    db.add(po)
    await db.flush()
    await db.refresh(po)
    return po


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_po(
    po_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.put("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def update_po(
    po_id: int,
    data: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(po, key, value)
    await db.flush()
    await db.refresh(po)
    return po


@router.post(
    "/purchase-order-items",
    response_model=PurchaseOrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_po_item(
    data: PurchaseOrderItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = PurchaseOrderItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/purchase-order-items/{item_id}", response_model=PurchaseOrderItemResponse)
async def update_po_item(
    item_id: int,
    data: PurchaseOrderItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Purchase order item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.get("/stock-movements", response_model=list[StockMovementResponse])
async def list_stock_movements(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(StockMovement).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/stock-movements",
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_stock_movement(
    data: StockMovementCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    movement = StockMovement(**data.model_dump())
    db.add(movement)

    # Update inventory item stock
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == data.item_id))
    inv_item = result.scalar_one_or_none()
    if inv_item:
        if data.movement_type == "IN":
            inv_item.current_stock = float(inv_item.current_stock) + float(data.quantity)
        elif data.movement_type == "OUT":
            inv_item.current_stock = float(inv_item.current_stock) - float(data.quantity)

    await db.flush()
    await db.refresh(movement)
    return movement
