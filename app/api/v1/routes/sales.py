from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.sale_controller import SaleController
from app.schemas.sale import SaleCreate, SaleResponse
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/stats")
async def get_sales_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    return await SaleController.get_stats(db)

@router.get("/", response_model=List[SaleResponse])
async def get_sales(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    only_today: bool = False,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await SaleController.get_multi(db, skip=skip, limit=limit, search=search, only_today=only_today)

@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    *,
    db: AsyncSession = Depends(deps.get_db),
    sale_in: SaleCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER])),
):
    try:
        return await SaleController.create(db, sale_in=sale_in, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al procesar la venta")

@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    sale = await SaleController.get_by_id(db, sale_id=sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return sale

