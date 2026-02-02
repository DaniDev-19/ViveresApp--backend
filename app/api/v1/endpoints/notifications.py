from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationUpdate
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def read_notifications(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Listar las últimas notificaciones.
    """
    query = (
        select(Notification)
        .order_by(desc(Notification.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/unread-count", response_model=int)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Contar notificaciones no leídas.
    """
    from sqlalchemy import func

    query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.is_read == False)
    )
    result = await db.execute(query)
    return result.scalar()


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_in: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Marcar notificación como leída.
    """
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = notification_in.is_read
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


@router.post("/mark-all-read")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Marcar todas como leídas.
    """
    await db.execute(
        update(Notification).where(Notification.is_read.is_(False)).values(is_read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}
