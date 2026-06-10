from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.sale_controller import SaleController
from app.controllers.return_controller import ReturnController
from app.controllers.exchange_controller import ExchangeController
from app.schemas.sale import SaleCreate, SaleResponse
from app.schemas.sale_return import ReturnCreate, ReturnResponse
from app.schemas.sale_exchange import ExchangeCreate, ExchangeResponse
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
    date_filter: Optional[str] = None,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await SaleController.get_multi(
        db,
        skip=skip,
        limit=limit,
        search=search,
        only_today=only_today,
        date_filter=date_filter
    )

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

@router.delete("/{sale_id}")
async def delete_sale(
    *,
    db: AsyncSession = Depends(deps.get_db),
    sale_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    sale = await SaleController.delete(db, sale_id=sale_id, user_id=current_user.id)
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return {"message": "Venta eliminada y stock restaurado", "id": sale_id}


# ── Returns ──────────────────────────────────────────────────────────────

@router.post("/{sale_id}/return", response_model=ReturnResponse)
async def create_sale_return(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la operación de devolución: {str(e)}")

@router.delete("/{sale_id}/return/{return_id}")
async def delete_sale_return(
    *,
    db: AsyncSession = Depends(deps.get_db),
    sale_id: int,
    return_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    deleted = await ReturnController.delete_return(db, return_id=return_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    return {"message": "Devolución eliminada y cambios revertidos", "id": return_id}


# ── Exchanges ────────────────────────────────────────────────────────────

@router.post("/{sale_id}/exchange", response_model=ExchangeResponse)
async def create_sale_exchange(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la operación de cambio: {str(e)}")

@router.delete("/{sale_id}/exchange/{exchange_id}")
async def delete_sale_exchange(
    *,
    db: AsyncSession = Depends(deps.get_db),
    sale_id: int,
    exchange_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    deleted = await ExchangeController.delete_exchange(db, exchange_id=exchange_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cambio no encontrado")
    return {"message": "Cambio eliminado y cambios revertidos", "id": exchange_id}