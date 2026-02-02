import asyncio
import logging
from sqlalchemy import text
from app.db.session import engine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_data():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT username, role FROM users LIMIT 5"))
            for row in result:
                logger.info(f"User: {row.username}, Role: {row.role}")

    except Exception as e:
        logger.error(f"Error checking data: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_data())
