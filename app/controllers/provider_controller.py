from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.provider import Provider
from app.schemas.provider import ProviderCreate

class ProviderController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        query = select(Provider).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, provider_in: ProviderCreate):
        db_obj = Provider(**provider_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update(db: AsyncSession, provider_id: int, provider_in: ProviderCreate):
        result = await db.execute(select(Provider).where(Provider.id == provider_id))
        provider = result.scalars().first()
        if not provider:
            return None
        for field, value in provider_in.model_dump(exclude_unset=True).items():
            setattr(provider, field, value)
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
        return provider

    @staticmethod
    async def delete(db: AsyncSession, provider_id: int):
        result = await db.execute(select(Provider).where(Provider.id == provider_id))
        provider = result.scalars().first()
        if not provider:
            return None
        await db.delete(provider)
        await db.commit()
        return provider
