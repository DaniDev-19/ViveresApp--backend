from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.web_order_item import WebOrderItem

class WebOrderItemController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(WebOrderItem).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_by_web_order(db: AsyncSession, web_order_id: int):
        result = await db.execute(select(WebOrderItem).where(WebOrderItem.web_order_id == web_order_id))
        return result.scalars().all()
