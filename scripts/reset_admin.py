import asyncio
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password
from sqlalchemy.future import select

async def reset_admin():
    async with AsyncSessionLocal() as db:
        try:
            print("--- Iniciando Reseteo de Administrador ---")
            result = await db.execute(select(User).filter(User.username == "admin"))
            user = result.scalars().first()
            
            pwd = "admin123"
            new_hash = get_password_hash(pwd)
            
            if not user:
                print("El usuario 'admin' no existe. Creándolo...")
                user = User(
                    username="admin",
                    email="admin@viveresapp.com",
                    password_hash=new_hash,
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(user)
            else:
                print(f"Usuario 'admin' encontrado. Actualizando contraseña a: {pwd}")
                user.password_hash = new_hash
                db.add(user)
            
            await db.commit()
            print("Confirmando cambios...")
            
            # Verificación inmediata
            check_res = await db.execute(select(User).filter(User.username == "admin"))
            check_user = check_res.scalars().first()
            is_valid = verify_password(pwd, check_user.password_hash)
            
            print(f"Reseteo completado.")
            print(f"Usuario: {check_user.username}")
            print(f"Nueva Contraseña Probada: {pwd}")
            print(f"¿Verificación Exitosa?: {'SÍ' if is_valid else 'NO'}")
            
        except Exception as e:
            print(f"Error crítico en el proceso: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(reset_admin())
