from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.web_order_controller import WebOrderController
from app.schemas.web_order import WebOrderCreate, WebOrderResponse, WebOrderPagination
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=WebOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_web_order(
    *,
    db: AsyncSession = Depends(deps.get_db),
    order_in: WebOrderCreate,
):
    return await WebOrderController.create(db, order_in=order_in)

@router.get("/", response_model=WebOrderPagination)
async def get_web_orders(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await WebOrderController.get_multi(db, skip=skip, limit=limit, status_filter=status_filter)

@router.put("/{order_id}/status", response_model=WebOrderResponse)
async def update_order_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    order_id: int,
    status: str,
    current_user: User = Depends(deps.get_current_active_user),
):
    order = await WebOrderController.update_status(db, order_id=order_id, status=status, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order
