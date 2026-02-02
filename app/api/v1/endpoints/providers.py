from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.purchase import Provider
from app.schemas.all_schemas import ProviderCreate, ProviderResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=List[ProviderResponse])
async def read_providers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve providers.
    """
    query = select(Provider).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ProviderResponse)
async def create_provider(
    *,
    db: AsyncSession = Depends(get_db),
    provider_in: ProviderCreate,
) -> Any:
    """
    Create new provider.
    """
    db_provider = Provider(**provider_in.model_dump())
    db.add(db_provider)
    await db.commit()
    await db.refresh(db_provider)

    # Audit
    await AuditService.log_action(
        db, 1, "CREATE", "providers", f"Created provider {db_provider.name}"
    )

    return db_provider


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    *,
    db: AsyncSession = Depends(get_db),
    provider_id: int,
    provider_in: ProviderCreate,
) -> Any:
    """
    Update a provider.
    """
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    for field, value in provider_in.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)

    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    # Audit
    await AuditService.log_action(
        db, 1, "UPDATE", "providers", f"Updated provider {provider.id}"
    )

    return provider


@router.delete("/{provider_id}")
async def delete_provider(
    *,
    db: AsyncSession = Depends(get_db),
    provider_id: int,
) -> Any:
    """
    Delete a provider.
    """
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    await db.delete(provider)
    await db.commit()

    # Audit
    await AuditService.log_action(
        db, 1, "DELETE", "providers", f"Deleted provider {provider.name}"
    )

    return {"message": "Proveedor eliminado exitosamente", "id": provider_id}
