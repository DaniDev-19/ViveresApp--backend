from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.provider_controller import ProviderController
from app.schemas.provider import ProviderResponse, ProviderCreate
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[ProviderResponse])
async def get_providers(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await ProviderController.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    *,
    db: AsyncSession = Depends(deps.get_db),
    provider_in: ProviderCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await ProviderController.create(db, provider_in=provider_in)

@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    *,
    db: AsyncSession = Depends(deps.get_db),
    provider_id: int,
    provider_in: ProviderCreate,
    current_user: User = Depends(deps.get_current_active_user),
):
    provider = await ProviderController.update(db, provider_id=provider_id, provider_in=provider_in)
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return provider

@router.delete("/{provider_id}")
async def delete_provider(
    *,
    db: AsyncSession = Depends(deps.get_db),
    provider_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    provider = await ProviderController.delete(db, provider_id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return {"message": "Proveedor eliminado", "id": provider_id}
