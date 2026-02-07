from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.settings import Setting

class SettingController:
    @staticmethod
    async def get(db: AsyncSession, key: str):
        result = await db.execute(select(Setting).where(Setting.key == key))
        return result.scalars().first()

    @staticmethod
    async def get_all(db: AsyncSession):
        result = await db.execute(select(Setting))
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, key: str, value: any):
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalars().first()
        if not setting:
            setting = Setting(key=key, value=value)
            db.add(setting)
        else:
            setting.value = value
        await db.commit()
        await db.refresh(setting)
        return setting
