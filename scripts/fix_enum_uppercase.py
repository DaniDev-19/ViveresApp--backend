import asyncio
import logging
from sqlalchemy import text
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_enum_uppercase():
    try:
        async with engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            
            # Agregar valores en MAYÚSCULAS para coincidir con el comportamiento de SQLAlchemy
            logger.info("Agregando 'INVENTORY_MANAGER' (mayúsculas)...")
            try:
                await conn.execute(text("ALTER TYPE userrole ADD VALUE 'INVENTORY_MANAGER'"))
                logger.info("OK: INVENTORY_MANAGER agregado.")
            except Exception as e:
                logger.warning(f"Info: {e}")

            logger.info("Agregando 'DELIVERY' (mayúsculas)...")
            try:
                await conn.execute(text("ALTER TYPE userrole ADD VALUE 'DELIVERY'"))
                logger.info("OK: DELIVERY agregado.")
            except Exception as e:
                logger.warning(f"Info: {e}")

    except Exception as e:
        logger.error(f"Error fatal: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_enum_uppercase())
