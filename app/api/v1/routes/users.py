from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.user_controller import UserController
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.models.user import UserRole

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: UserResponse = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    return await UserController.get_multi(db, skip=skip, limit=limit, search=search)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: UserResponse = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    return await UserController.create(db, user_in=user_in)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: UserResponse = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    user = await UserController.update(db, user_id=user_id, user_in=user_in)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    current_user: UserResponse = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    user = await UserController.delete(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

