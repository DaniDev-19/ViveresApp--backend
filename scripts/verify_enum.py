import asyncio
import logging
from sqlalchemy import text
from app.db.session import engine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_enum():
    try:
        async with engine.connect() as conn:
            # Consulta para obtener los valores del enum 'userrole'
            result = await conn.execute(text("SELECT unnest(enum_range(NULL::userrole))"))
            values = [row[0] for row in result.fetchall()]
            logger.info(f"Valores actuales en userrole: {values}")
            
            expected = {'admin', 'worker', 'inventory_manager', 'delivery', 'INVENTORY_MANAGER', 'DELIVERY'}
            current = set(values)
            
            # Verificamos si al menos los uppercase (que usa el backend) están presentes
            required = {'ADMIN', 'WORKER', 'INVENTORY_MANAGER', 'DELIVERY'}
            
            if required.issubset(current):
                logger.info(f"VERIFICACIÓN EXITOSA: Los roles requeridos {required} están presentes.")
                logger.info(f"Todos los valores en DB: {current}")
            else:
                logger.error(f"FALTAN ROLES. Requerido: {required}, Encontrado: {current}")

    except Exception as e:
        logger.error(f"Error al verificar: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_enum())
