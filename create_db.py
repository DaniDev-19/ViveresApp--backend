import asyncio
import asyncpg
from app.core.config import settings


async def create_database():
    db_url = settings.DATABASE_URL
    # Parse URL to get user/pass/host but connect to 'postgres' db
    # Assumes URL format: postgresql+asyncpg://user:pass@host:port/dbname

    # We strip 'postgresql+asyncpg://' to parse it easily or just use string manipulation
    # This is a bit hacky but works for dev.

    # Extract dbname
    base_url = db_url.rsplit("/", 1)[0]
    target_db_name = db_url.rsplit("/", 1)[1]

    # Connect to default 'postgres' database
    sys_db_url = f"{base_url}/postgres"

    # We need to remove the driver for asyncpg direct usage or use URL parsing
    # Let's clean the URL for asyncpg: 'postgresql://...'
    sys_db_url = sys_db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        print(f"Connecting to {sys_db_url} to check DB {target_db_name}...")
        conn = await asyncpg.connect(sys_db_url)

        # Check if db exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", target_db_name
        )

        if not exists:
            print(f"Creating database {target_db_name}...")
            await conn.execute(f'CREATE DATABASE "{target_db_name}"')
            print("Database created!")
        else:
            print(f"Database {target_db_name} already exists.")

        await conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == "__main__":
    asyncio.run(create_database())
