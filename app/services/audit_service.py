from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: int,
        action: str,
        table_name: str = None,
        details: str = None,
        commit: bool = True,
    ):
        """
        Registra una acción en la bitácora.
        """
        audit = AuditLog(
            user_id=user_id, action=action, table_name=table_name, details=details
        )
        db.add(audit)
        if commit:
            await db.commit()
        return audit

