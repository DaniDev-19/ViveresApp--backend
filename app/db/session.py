from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Configuración optimizada para producción
IS_PRODUCTION = os.environ.get("RENDER", False)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=not IS_PRODUCTION,  # Solo mostrar SQL en desarrollo
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Reciclar conexiones cada 30 min
    pool_pre_ping=True,  # Verificar conexión antes de usar
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
