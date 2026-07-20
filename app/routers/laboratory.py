from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.laboratory import LabOrder, LabOrderItem, LabResult, LabTest
from app.schemas.laboratory import (
    LabOrderCreate,
    LabOrderItemCreate,
    LabOrderItemResponse,
    LabOrderItemUpdate,
    LabOrderResponse,
    LabOrderUpdate,
    LabResultCreate,
    LabResultResponse,
    LabResultUpdate,
    LabTestCreate,
    LabTestResponse,
    LabTestUpdate,
)

router = APIRouter(prefix="/laboratory", tags=["Laboratory"])


@router.get("/tests", response_model=list[LabTestResponse])
async def list_tests(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabTest).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/tests", response_model=LabTestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    data: LabTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    test = LabTest(**data.model_dump())
    db.add(test)
    await db.flush()
    await db.refresh(test)
    return test


@router.get("/tests/{test_id}", response_model=LabTestResponse)
async def get_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabTest).where(LabTest.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    return test


@router.put("/tests/{test_id}", response_model=LabTestResponse)
async def update_test(
    test_id: int,
    data: LabTestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabTest).where(LabTest.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(test, key, value)
    await db.flush()
    await db.refresh(test)
    return test


@router.get("/orders", response_model=list[LabOrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabOrder).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/orders", response_model=LabOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: LabOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = LabOrder(**data.model_dump())
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


@router.get("/orders/{order_id}", response_model=LabOrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabOrder).where(LabOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return order


@router.put("/orders/{order_id}", response_model=LabOrderResponse)
async def update_order(
    order_id: int,
    data: LabOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabOrder).where(LabOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    await db.flush()
    await db.refresh(order)
    return order


@router.post(
    "/order-items",
    response_model=LabOrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order_item(
    data: LabOrderItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = LabOrderItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/order-items/{item_id}", response_model=LabOrderItemResponse)
async def update_order_item(
    item_id: int,
    data: LabOrderItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabOrderItem).where(LabOrderItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Lab order item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.post(
    "/results", response_model=LabResultResponse, status_code=status.HTTP_201_CREATED
)
async def create_result(
    data: LabResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lab_result = LabResult(**data.model_dump())
    db.add(lab_result)
    await db.flush()
    await db.refresh(lab_result)
    return lab_result


@router.put("/results/{result_id}", response_model=LabResultResponse)
async def update_result(
    result_id: int,
    data: LabResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(LabResult).where(LabResult.id == result_id))
    lab_result = result.scalar_one_or_none()
    if not lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lab_result, key, value)
    await db.flush()
    await db.refresh(lab_result)
    return lab_result
