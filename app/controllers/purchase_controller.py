from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_item import PurchaseItem
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderReceipt

class PurchaseController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        query = select(PurchaseOrder).options(selectinload(PurchaseOrder.items), selectinload(PurchaseOrder.provider)).offset(skip).limit(limit).order_by(PurchaseOrder.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, order_in: PurchaseOrderCreate):
        order = PurchaseOrder(provider_id=order_in.provider_id, expected_date=order_in.expected_date, notes=order_in.notes, status="pending")
        db.add(order)
        await db.commit()
        await db.refresh(order)
        for item_data in order_in.items:
            item = PurchaseItem(purchase_id=order.id, product_id=item_data.product_id, product_name=item_data.product_name, requested_quantity=item_data.requested_quantity, cost_price=item_data.cost_price, status="pending")
            db.add(item)
        await db.commit()
        result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order.id).options(selectinload(PurchaseOrder.items), selectinload(PurchaseOrder.provider)))
        return result.scalars().first()

    @staticmethod
    async def receive(db: AsyncSession, order_id: int, receipt_in: PurchaseOrderReceipt):
        query = select(PurchaseOrder).where(PurchaseOrder.id == order_id).options(selectinload(PurchaseOrder.provider), selectinload(PurchaseOrder.items).selectinload(PurchaseItem.product))
        result = await db.execute(query)
        order = result.scalars().first()
        if not order or order.status == "completed":
            return None
        
        receipt_map = {item.id: item for item in receipt_in.items}
        for item in order.items:
            receipt_data = receipt_map.get(item.id)
            received_qty = receipt_data.received_quantity if receipt_data else 0
            actual_cost = receipt_data.actual_cost if receipt_data else item.cost_price or 0.0
            item.received_quantity = received_qty
            item.cost_price = actual_cost
            item.status = "verified" if received_qty == item.requested_quantity else "mismatch"
            if item.product:
                item.product.stock_quantity += received_qty
                item.product.cost_price = actual_cost
                item.product.price_usd = actual_cost * (1 + item.product.profit_margin) * (1 + item.product.tax_rate)
        
        order.status = "completed"
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def delete(db: AsyncSession, order_id: int):
        query = (
            select(PurchaseOrder)
            .where(PurchaseOrder.id == order_id)
            .options(selectinload(PurchaseOrder.items))
        )
        result = await db.execute(query)
        order = result.scalars().first()
        if not order:
            return None
        if order.status == "completed":
            return False
        for item in order.items:
            await db.delete(item)
        await db.delete(order)
        await db.commit()
        return order
