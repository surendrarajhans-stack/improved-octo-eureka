from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.radiology import (
    RadiologyOrder,
    RadiologyOrderItem,
    RadiologyResult,
    RadiologyTest,
)
from app.schemas.radiology import (
    RadiologyOrderCreate,
    RadiologyOrderItemCreate,
    RadiologyOrderItemResponse,
    RadiologyOrderItemUpdate,
    RadiologyOrderResponse,
    RadiologyOrderUpdate,
    RadiologyResultCreate,
    RadiologyResultResponse,
    RadiologyResultUpdate,
    RadiologyTestCreate,
    RadiologyTestResponse,
    RadiologyTestUpdate,
)

router = APIRouter(prefix="/radiology", tags=["Radiology"])


@router.get("/tests", response_model=list[RadiologyTestResponse])
async def list_tests(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyTest).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/tests", response_model=RadiologyTestResponse, status_code=status.HTTP_201_CREATED
)
async def create_test(
    data: RadiologyTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    test = RadiologyTest(**data.model_dump())
    db.add(test)
    await db.flush()
    await db.refresh(test)
    return test


@router.get("/tests/{test_id}", response_model=RadiologyTestResponse)
async def get_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyTest).where(RadiologyTest.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Radiology test not found")
    return test


@router.put("/tests/{test_id}", response_model=RadiologyTestResponse)
async def update_test(
    test_id: int,
    data: RadiologyTestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyTest).where(RadiologyTest.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Radiology test not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(test, key, value)
    await db.flush()
    await db.refresh(test)
    return test


@router.get("/orders", response_model=list[RadiologyOrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyOrder).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/orders", response_model=RadiologyOrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_order(
    data: RadiologyOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = RadiologyOrder(**data.model_dump())
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


@router.get("/orders/{order_id}", response_model=RadiologyOrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyOrder).where(RadiologyOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Radiology order not found")
    return order


@router.put("/orders/{order_id}", response_model=RadiologyOrderResponse)
async def update_order(
    order_id: int,
    data: RadiologyOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyOrder).where(RadiologyOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Radiology order not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    await db.flush()
    await db.refresh(order)
    return order


@router.post(
    "/order-items",
    response_model=RadiologyOrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order_item(
    data: RadiologyOrderItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = RadiologyOrderItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/order-items/{item_id}", response_model=RadiologyOrderItemResponse)
async def update_order_item(
    item_id: int,
    data: RadiologyOrderItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyOrderItem).where(RadiologyOrderItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Radiology order item not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.post(
    "/results", response_model=RadiologyResultResponse, status_code=status.HTTP_201_CREATED
)
async def create_result(
    data: RadiologyResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rad_result = RadiologyResult(**data.model_dump())
    db.add(rad_result)
    await db.flush()
    await db.refresh(rad_result)
    return rad_result


@router.put("/results/{result_id}", response_model=RadiologyResultResponse)
async def update_result(
    result_id: int,
    data: RadiologyResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(RadiologyResult).where(RadiologyResult.id == result_id))
    rad_result = result.scalar_one_or_none()
    if not rad_result:
        raise HTTPException(status_code=404, detail="Radiology result not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rad_result, key, value)
    await db.flush()
    await db.refresh(rad_result)
    return rad_result
