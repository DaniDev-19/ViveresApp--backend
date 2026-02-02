from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification


class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession, title: str, message: str, type: str = "info"
    ) -> Notification:
        notification = Notification(title=title, message=message, type=type)
        db.add(notification)
        await db.flush()
        return notification
