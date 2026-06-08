from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.controllers.setting_controller import SettingController
from app.schemas.settings import SettingResponse, SettingBase
from app.api import deps
from app.models.user import User, UserRole
from typing import List

router = APIRouter()

@router.get("/", response_model=List[SettingResponse])
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return await SettingController.get_all(db)

@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    setting = await SettingController.get(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.post("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    setting_in: SettingBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    return await SettingController.update(db, key, setting_in.value)

