from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.web_order_item_controller import WebOrderItemController
from app.schemas.web_order_item import WebOrderItemResponse
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[WebOrderItemResponse])
async def get_web_order_items(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await WebOrderItemController.get_multi(db, skip=skip, limit=limit)

@router.get("/order/{web_order_id}", response_model=List[WebOrderItemResponse])
async def get_web_order_items_by_order(
    web_order_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return await WebOrderItemController.get_by_web_order(db, web_order_id=web_order_id)
