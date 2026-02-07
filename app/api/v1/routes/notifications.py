from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.notification_controller import NotificationController
from app.schemas.notification import NotificationResponse
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    return await NotificationController.get_multi(db, skip=skip, limit=limit)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
@router.put("/{notification_id}", response_model=NotificationResponse)
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return await NotificationController.mark_read(db, notification_id)

@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return await NotificationController.mark_all_read(db)

@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    from sqlalchemy import func
    from app.models.notification import Notification
    result = await db.execute(select(func.count(Notification.id)).where(Notification.is_read == False))
    return result.scalar() or 0
