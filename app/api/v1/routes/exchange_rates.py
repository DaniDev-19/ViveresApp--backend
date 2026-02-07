from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.exchange_rate_controller import ExchangeRateController
from app.schemas.exchange_rate import ExchangeRateResponse
from app.models.user import User

router = APIRouter()

@router.get("/current", response_model=ExchangeRateResponse)
async def get_current_rate(
    currency: str = "USD",
    db: AsyncSession = Depends(deps.get_db),
):
    rate = await ExchangeRateController.get_current(db, currency=currency)
    if not rate:
        raise HTTPException(status_code=404, detail="Tasa no encontrada")
    return rate

@router.get("/", response_model=List[ExchangeRateResponse])
@router.get("/history", response_model=List[ExchangeRateResponse])
async def get_history(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
):
    return await ExchangeRateController.get_multi(db, skip=skip, limit=limit)

@router.post("/refresh")
async def refresh_rates(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return await ExchangeRateController.refresh(db)
