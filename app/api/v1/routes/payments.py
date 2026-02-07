from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.payment_controller import PaymentController
from app.schemas.payment import PaymentResponse
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[PaymentResponse])
async def get_payments(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await PaymentController.get_multi(db, skip=skip, limit=limit)

@router.get("/sale/{sale_id}", response_model=List[PaymentResponse])
async def get_payments_by_sale(
    sale_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return await PaymentController.get_by_sale(db, sale_id=sale_id)
