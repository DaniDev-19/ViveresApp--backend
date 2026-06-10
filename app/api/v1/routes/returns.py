from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.return_controller import ReturnController
from app.schemas.sale_return import ReturnCreate, ReturnResponse
from app.models.user import User, UserRole

router = APIRouter()


@router.post("/", response_model=ReturnResponse)
async def create_return(
    *,
    db: AsyncSession = Depends(deps.get_db),
    sale_id: int,
    return_in: ReturnCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER])),
):
    try:
        return await ReturnController.create_return(db, sale_id=sale_id, return_in=return_in, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ReturnResponse])
async def get_returns(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sale_id: Optional[int] = None,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await ReturnController.get_multi(db, skip=skip, limit=limit, search=search, sale_id=sale_id)


@router.get("/{return_id}", response_model=ReturnResponse)
async def get_return(
    return_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    result = await ReturnController.get_by_id(db, return_id=return_id)
    if not result:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    return result