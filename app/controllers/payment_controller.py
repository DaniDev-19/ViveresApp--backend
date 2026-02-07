from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.payment import Payment

class PaymentController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(Payment).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_by_sale(db: AsyncSession, sale_id: int):
        result = await db.execute(select(Payment).where(Payment.sale_id == sale_id))
        return result.scalars().all()
