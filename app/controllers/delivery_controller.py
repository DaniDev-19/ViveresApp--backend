from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.delivery import Delivery
from app.schemas.delivery import DeliveryCreate, DeliveryUpdate

class DeliveryController:
    @staticmethod
    async def get_by_id(db: AsyncSession, delivery_id: int) -> Optional[Delivery]:
        query = (
            select(Delivery)
            .options(selectinload(Delivery.delivery_user), selectinload(Delivery.provider))
            .where(Delivery.id == delivery_id)
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        delivery_user_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        status: Optional[str] = None
    ):
        query = (
            select(Delivery)
            .options(selectinload(Delivery.delivery_user), selectinload(Delivery.provider))
            .order_by(Delivery.created_at.desc())
        )
        if delivery_user_id is not None:
            query = query.where(Delivery.delivery_user_id == delivery_user_id)
        if provider_id is not None:
            query = query.where(Delivery.provider_id == provider_id)
        if status is not None:
            query = query.where(Delivery.status == status)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, delivery_in: DeliveryCreate) -> Delivery:
        db_obj = Delivery(**delivery_in.model_dump())
        if db_obj.status == "completed":
            db_obj.completed_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Load relationships
        query = (
            select(Delivery)
            .options(selectinload(Delivery.delivery_user), selectinload(Delivery.provider))
            .where(Delivery.id == db_obj.id)
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def update(db: AsyncSession, delivery_id: int, delivery_in: DeliveryUpdate) -> Optional[Delivery]:
        query = (
            select(Delivery)
            .options(selectinload(Delivery.delivery_user), selectinload(Delivery.provider))
            .where(Delivery.id == delivery_id)
        )
        result = await db.execute(query)
        delivery = result.scalars().first()
        if not delivery:
            return None
            
        update_data = delivery_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(delivery, field, value)
            
        if "status" in update_data:
            if update_data["status"] == "completed":
                delivery.completed_at = datetime.now(timezone.utc)
            else:
                delivery.completed_at = None
                
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        return delivery

    @staticmethod
    async def delete(db: AsyncSession, delivery_id: int) -> Optional[Delivery]:
        query = select(Delivery).where(Delivery.id == delivery_id)
        result = await db.execute(query)
        delivery = result.scalars().first()
        if not delivery:
            return None
        await db.delete(delivery)
        await db.commit()
        return delivery
