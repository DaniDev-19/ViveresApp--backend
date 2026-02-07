from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.purchase_controller import PurchaseController
from app.schemas.purchase_order import PurchaseOrderResponse, PurchaseOrderCreate, PurchaseOrderReceipt
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[PurchaseOrderResponse])
async def get_purchases(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await PurchaseController.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    *,
    db: AsyncSession = Depends(deps.get_db),
    order_in: PurchaseOrderCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await PurchaseController.create(db, order_in=order_in)

@router.put("/{order_id}/receive", response_model=PurchaseOrderResponse)
async def receive_purchase_order(
    *,
    db: AsyncSession = Depends(deps.get_db),
    order_id: int,
    receipt_in: PurchaseOrderReceipt,
    current_user: User = Depends(deps.get_current_active_user),
):
    order = await PurchaseController.receive(db, order_id=order_id, receipt_in=receipt_in)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada o ya completada")
    return order
