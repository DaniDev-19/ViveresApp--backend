from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.exchange_rate import ExchangeRate
from app.services.currency import currency_service

class ExchangeRateController:
    @staticmethod
    async def get_current(db: AsyncSession, currency: str = "USD"):
        result = await db.execute(select(ExchangeRate).where(ExchangeRate.currency == currency).order_by(ExchangeRate.fetched_at.desc()))
        return result.scalars().first()

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(ExchangeRate).order_by(ExchangeRate.fetched_at.desc()).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def refresh(db: AsyncSession):
        # Opcional: Limpiar registros antiguos para no saturar si se desea
        # await db.execute(delete(ExchangeRate))
        return await currency_service.update_rates(db)
