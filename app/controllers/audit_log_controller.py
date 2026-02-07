from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit_log import AuditLog

class AuditLogController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit))
        return result.scalars().all()
