from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.sale_item_controller import SaleItemController
from app.schemas.sale_item import SaleItemResponse
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/", response_model=List[SaleItemResponse])
async def get_sale_items(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await SaleItemController.get_multi(db, skip=skip, limit=limit)

@router.get("/sale/{sale_id}", response_model=List[SaleItemResponse])
async def get_sale_items_by_sale(
    sale_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await SaleItemController.get_by_sale(db, sale_id=sale_id)

