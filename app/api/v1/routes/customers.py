from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.customer_controller import CustomerController
from app.schemas.customer import CustomerResponse, CustomerCreate, CustomerUpdate
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/lookup/{cedula}", response_model=Optional[CustomerResponse])
async def lookup_customer_by_cedula(
    cedula: str,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Endpoint público para buscar clientes por cédula (usado en autocompletado web).
    """
    return await CustomerController.get_by_cedula(db, cedula=cedula)

@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await CustomerController.get_multi(db, skip=skip, limit=limit, search=search)

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    *,
    db: AsyncSession = Depends(deps.get_db),
    customer_in: CustomerCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    existing = await CustomerController.get_by_cedula(db, cedula=customer_in.cedula)
    if existing:
        raise HTTPException(status_code=400, detail="El cliente ya existe")
    return await CustomerController.create(db, customer_in=customer_in)

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    *,
    db: AsyncSession = Depends(deps.get_db),
    customer_id: int,
    customer_in: CustomerUpdate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    customer = await CustomerController.update(db, customer_id=customer_id, customer_in=customer_in)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return customer

@router.delete("/{customer_id}")
async def delete_customer(
    *,
    db: AsyncSession = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    customer = await CustomerController.delete(db, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado", "id": customer_id}

