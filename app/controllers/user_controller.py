from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core import security

class UserController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100, search: str = None):
        query = select(User)
        if search:
            query = query.where(or_(User.username.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, user_in: UserCreate):
        hashed_password = security.get_password_hash(user_in.password)
        db_obj = User(
            email=user_in.email, username=user_in.username,
            password_hash=hashed_password, role=user_in.role, is_active=user_in.is_active
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update(db: AsyncSession, user_id: int, user_in: UserUpdate):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return None
        
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = security.get_password_hash(update_data["password"])
            del update_data["password"]
            
        for field, value in update_data.items():
            setattr(user, field, value)
            
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return None
        await db.delete(user)
        await db.commit()
        return user
