from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.category_controller import CategoryController
from app.schemas.category import CategoryResponse, CategoryCreate, CategoryUpdate
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse], dependencies=[Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER]))])
async def get_categories(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 1000,
):
    return await CategoryController.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER]))])
async def create_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_in: CategoryCreate,
):
    return await CategoryController.create(db, category_in=category_in)


@router.put("/{category_id}", response_model=CategoryResponse, dependencies=[Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER]))])
async def update_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
    category_in: CategoryUpdate,
):
    category = await CategoryController.update(db, category_id=category_id, category_in=category_in)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@router.delete("/{category_id}", dependencies=[Depends(deps.verify_roles([UserRole.ADMIN]))])
async def delete_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_id: int,
):
    count = await CategoryController.count_products(db, category_id)
    if count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: {count} producto(s) usan esta categoría",
        )
    category = await CategoryController.delete(db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return {"message": "Categoría eliminada", "id": category_id}

