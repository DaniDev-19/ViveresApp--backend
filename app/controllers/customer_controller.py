from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

class CustomerController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100, search: str = None):
        stmt = select(Customer)
        if search:
            stmt = stmt.where(or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.cedula.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%")
            ))
        result = await db.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_by_cedula(db: AsyncSession, cedula: str):
        result = await db.execute(select(Customer).where(Customer.cedula == cedula))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, customer_in: CustomerCreate):
        db_obj = Customer(**customer_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update(db: AsyncSession, customer_id: int, customer_in: CustomerUpdate):
        customer = await db.get(Customer, customer_id)
        if not customer:
            return None
        update_data = customer_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        return customer

    @staticmethod
    async def delete(db: AsyncSession, customer_id: int):
        customer = await db.get(Customer, customer_id)
        if not customer:
            return None
        await db.delete(customer)
        await db.commit()
        return customer
