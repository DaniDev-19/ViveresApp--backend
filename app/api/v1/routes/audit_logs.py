from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.audit_log_controller import AuditLogController
from app.schemas.audit_log import AuditLogResponse
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    return await AuditLogController.get_multi(db, skip=skip, limit=limit)

