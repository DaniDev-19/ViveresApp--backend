from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        query = select(Category).order_by(Category.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, category_in: CategoryCreate):
        db_obj = Category(**category_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update(db: AsyncSession, category_id: int, category_in: CategoryUpdate):
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalars().first()
        if not category:
            return None
        for field, value in category_in.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category_id: int):
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalars().first()
        if not category:
            return None
        await db.delete(category)
        await db.commit()
        return category

    @staticmethod
    async def count_products(db: AsyncSession, category_id: int) -> int:
        result = await db.execute(
            select(func.count()).select_from(Product).where(Product.category_id == category_id)
        )
        return result.scalar() or 0
