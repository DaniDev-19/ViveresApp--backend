from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.exchange_controller import ExchangeController
from app.schemas.sale_exchange import ExchangeCreate, ExchangeResponse
from app.models.user import User, UserRole

router = APIRouter()


@router.post("/", response_model=ExchangeResponse)
async def create_exchange(
    *,
    db: AsyncSession = Depends(deps.get_db),
    sale_id: int,
    exchange_in: ExchangeCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER])),
):
    try:
        return await ExchangeController.create_exchange(db, sale_id=sale_id, exchange_in=exchange_in, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ExchangeResponse])
async def get_exchanges(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sale_id: Optional[int] = None,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await ExchangeController.get_multi(db, skip=skip, limit=limit, search=search, sale_id=sale_id)


@router.get("/{exchange_id}", response_model=ExchangeResponse)
async def get_exchange(
    exchange_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    result = await ExchangeController.get_by_id(db, exchange_id=exchange_id)
    if not result:
        raise HTTPException(status_code=404, detail="Cambio no encontrado")
    return result