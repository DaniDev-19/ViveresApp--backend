from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.notification import Notification

class NotificationController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(Notification).order_by(Notification.created_at.desc()).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def mark_read(db: AsyncSession, notification_id: int):
        notification = await db.get(Notification, notification_id)
        if notification:
            notification.is_read = True
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
        return notification

    @staticmethod
    async def mark_all_read(db: AsyncSession):
        await db.execute(update(Notification).where(Notification.is_read == False).values(is_read=True))
        await db.commit()
        return {"message": "All marked as read"}
