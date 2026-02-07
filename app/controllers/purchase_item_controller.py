from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.purchase_item import PurchaseItem

class PurchaseItemController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(PurchaseItem).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_by_purchase(db: AsyncSession, purchase_id: int):
        result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
        return result.scalars().all()
