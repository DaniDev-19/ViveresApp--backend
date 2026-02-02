import asyncio
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.future import select

async def create_initial_user():
    async with AsyncSessionLocal() as db:
        try:
            # Verificar si ya existe
            result = await db.execute(select(User).filter(User.username == "admin"))
            user = result.scalars().first()
            
            if user:
                print("El usuario 'admin' ya existe.")
                return

            new_user = User(
                username="admin",
                email="admin@viveresapp.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(new_user)
            await db.commit()
            print("Usuario administrador creado exitosamente:")
            print("Usuario: admin")
            print("Contraseña: admin123")
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(create_initial_user())
