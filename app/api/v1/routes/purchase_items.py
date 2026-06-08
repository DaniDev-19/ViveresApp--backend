from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.purchase_item_controller import PurchaseItemController
from app.schemas.purchase_item import PurchaseItemResponse
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/", response_model=List[PurchaseItemResponse])
async def get_purchase_items(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    return await PurchaseItemController.get_multi(db, skip=skip, limit=limit)

@router.get("/purchase/{purchase_id}", response_model=List[PurchaseItemResponse])
async def get_purchase_items_by_purchase(
    purchase_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    return await PurchaseItemController.get_by_purchase(db, purchase_id=purchase_id)

