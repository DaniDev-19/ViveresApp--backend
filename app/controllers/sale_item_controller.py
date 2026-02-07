from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sale_item import SaleItem

class SaleItemController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(SaleItem).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_by_sale(db: AsyncSession, sale_id: int):
        result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
        return result.scalars().all()
