from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.product_controller import ProductController
from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    in_stock_only: bool = False,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await ProductController.get_multi(
        db,
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        in_stock_only=in_stock_only,
    )

@router.get("/public", response_model=List[ProductResponse])
async def get_public_products(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
):
    return await ProductController.get_multi(db, skip=skip, limit=limit, search=search, public_only=True)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    *,
    db: AsyncSession = Depends(deps.get_db),
    product_in: ProductCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    return await ProductController.create(db, product_in=product_in, user_id=current_user.id)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    *,
    db: AsyncSession = Depends(deps.get_db),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    product = await ProductController.update(db, product_id=product_id, product_in=product_in, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.delete("/{product_id}")
async def delete_product(
    *,
    db: AsyncSession = Depends(deps.get_db),
    product_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    product = await ProductController.delete(db, product_id=product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado", "id": product_id}

