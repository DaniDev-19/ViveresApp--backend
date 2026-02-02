from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.web_order import Customer
from app.api import deps
from app.models.user import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class CustomerCreate(BaseModel):
    cedula: str
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None


class CustomerUpdate(BaseModel):
    cedula: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    cedula: str
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[CustomerResponse])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Obtiene la lista de clientes con búsqueda opcional.
    """
    stmt = select(Customer)
    
    if search:
        stmt = stmt.where(
            Customer.name.ilike(f"%{search}%") | 
            Customer.cedula.ilike(f"%{search}%") |
            Customer.phone.ilike(f"%{search}%")
        )
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Crea un nuevo cliente (registro rápido desde POS).
    """
    # Verificar si ya existe
    stmt = select(Customer).where(Customer.cedula == customer_in.cedula)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un cliente con cédula {customer_in.cedula}"
        )
    
    db_customer = Customer(**customer_in.dict())
    db.add(db_customer)
    await db.commit()
    await db.refresh(db_customer)
    return db_customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Actualiza los datos de un cliente.
    """
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    update_data = customer_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Elimina un cliente.
    """
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    await db.delete(customer)
    await db.commit()
    return {"message": "Cliente eliminado exitosamente", "id": customer_id}
