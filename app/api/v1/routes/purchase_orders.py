from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.purchase_controller import PurchaseController
from app.schemas.purchase_order import PurchaseOrderResponse, PurchaseOrderCreate, PurchaseOrderReceipt
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/", response_model=List[PurchaseOrderResponse])
async def get_purchases(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    return await PurchaseController.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    *,
    db: AsyncSession = Depends(deps.get_db),
    order_in: PurchaseOrderCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    return await PurchaseController.create(db, order_in=order_in)

@router.put("/{order_id}/receive", response_model=PurchaseOrderResponse)
async def receive_purchase_order(
    *,
    db: AsyncSession = Depends(deps.get_db),
    order_id: int,
    receipt_in: PurchaseOrderReceipt,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    order = await PurchaseController.receive(db, order_id=order_id, receipt_in=receipt_in)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada o ya completada")
    return order

@router.delete("/{order_id}")
async def delete_purchase_order(
    *,
    db: AsyncSession = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    result = await PurchaseController.delete(db, order_id=order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if result is False:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar una orden que ya fue recibida",
        )
    return {"message": "Orden eliminada", "id": order_id}

