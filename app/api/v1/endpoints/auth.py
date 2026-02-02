from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core import security
from app.core.config import settings
from app.models.user import User
from sqlalchemy import select

router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Audit Log: Login
    from app.services.audit_service import AuditService

    await AuditService.log_action(
        db, user.id, "LOGIN", "users", f"User {user.username} logged in"
    )
    await db.commit()  # Commit explícito para guardar el log si no hay otra transacción

    return {
        "access_token": security.create_access_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }
