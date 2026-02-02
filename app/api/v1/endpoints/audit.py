from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.models.audit import AuditLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    table_name: str | None
    details: str | None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AuditLogResponse])
async def read_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Recuperar bitácora de auditoría.
    TODO: Restringir solo a ADMINs cuando tengamos el middleware de Auth listo.
    """
    result = await db.execute(
        select(AuditLog).order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)
    )
    return result.scalars().all()
