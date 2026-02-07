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
    ):
        """
        Registra una acción en la bitácora.
        """
        audit = AuditLog(
            user_id=user_id, action=action, table_name=table_name, details=details
        )
        db.add(audit)
        # Nota: Normalmente se hace commit fuera, pero para asegurar el log
        # podríamos hacer un commit parcial o dejarlo a la transacción principal.
        # Por seguridad y consistencia, lo dejamos a la transacción principal.
        return audit
