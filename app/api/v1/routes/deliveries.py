from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.delivery_controller import DeliveryController
from app.schemas.delivery import DeliveryResponse, DeliveryCreate, DeliveryUpdate
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/", response_model=List[DeliveryResponse])
async def get_deliveries(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    provider_id: Optional[int] = None,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.DELIVERY])),
):
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str == UserRole.DELIVERY.value:
        return await DeliveryController.get_multi(
            db, skip=skip, limit=limit, delivery_user_id=current_user.id, provider_id=provider_id, status=status_filter
        )
    return await DeliveryController.get_multi(db, skip=skip, limit=limit, provider_id=provider_id, status=status_filter)

@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(
    delivery_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.DELIVERY])),
):
    delivery = await DeliveryController.get_by_id(db, delivery_id=delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
        
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str == UserRole.DELIVERY.value and delivery.delivery_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver este envío")
        
    return delivery

@router.post("/", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    *,
    db: AsyncSession = Depends(deps.get_db),
    delivery_in: DeliveryCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER])),
):
    return await DeliveryController.create(db, delivery_in=delivery_in)

@router.put("/{delivery_id}", response_model=DeliveryResponse)
async def update_delivery(
    *,
    db: AsyncSession = Depends(deps.get_db),
    delivery_id: int,
    delivery_in: DeliveryUpdate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER])),
):
    delivery = await DeliveryController.update(db, delivery_id=delivery_id, delivery_in=delivery_in)
    if not delivery:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    return delivery

@router.patch("/{delivery_id}/status", response_model=DeliveryResponse)
async def update_delivery_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    delivery_id: int,
    status_str: str,
    cost_usd: Optional[float] = None,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.DELIVERY])),
):
    delivery = await DeliveryController.get_by_id(db, delivery_id=delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
        
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str == UserRole.DELIVERY.value and delivery.delivery_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos para modificar este envío")
        
    from app.schemas.delivery import DeliveryUpdate as DU
    update_data = {"status": status_str}
    if cost_usd is not None:
        update_data["cost_usd"] = cost_usd
    delivery_in = DU(**update_data)
    return await DeliveryController.update(db, delivery_id=delivery_id, delivery_in=delivery_in)

@router.delete("/{delivery_id}")
async def delete_delivery(
    *,
    db: AsyncSession = Depends(deps.get_db),
    delivery_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    delivery = await DeliveryController.delete(db, delivery_id=delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    return {"message": "Envío eliminado", "id": delivery_id}
