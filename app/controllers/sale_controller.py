from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, cast, String, func
from datetime import datetime, timedelta
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.product import Product
from app.schemas.sale import SaleCreate

class SaleController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100, search: str = None):
        from sqlalchemy.orm import selectinload
        
        stmt = select(Sale).options(
            selectinload(Sale.items).selectinload(SaleItem.product),
            selectinload(Sale.payments),
            selectinload(Sale.customer)
        ).order_by(desc(Sale.created_at))

        if search:
            stmt = stmt.where(cast(Sale.id, String).like(f"%{search}%"))
        
        result = await db.execute(stmt.offset(skip).limit(limit))
        sales = result.scalars().all()
        
        for sale in sales:
            if sale.customer:
                sale.customer_name = sale.customer.name
                sale.customer_phone = sale.customer.phone
                sale.customer_cedula = sale.customer.cedula
            for item in sale.items:
                if item.product:
                    item.name = item.product.name
                    item.barcode = item.product.barcode if item.product else None
        return sales

    @staticmethod
    async def create(db: AsyncSession, sale_in: SaleCreate, user_id: int):
        # Validar que se haya seleccionado un cliente
        if not sale_in.customer_id:
            raise ValueError("Debe seleccionar un cliente para crear la venta")
        
        subtotal_usd = 0.0
        total_tax_usd = 0.0
        db_items = []

        for item in sale_in.items:
            product = await db.get(Product, item.product_id)
            if not product or product.stock_quantity < item.quantity:
                raise ValueError(f"Stock insuficiente o producto {item.product_id} no encontrado")

            product.stock_quantity -= item.quantity
            price = item.matched_price if item.matched_price else product.price_usd
            item_subtotal = price * item.quantity
            item_tax = item_subtotal * product.tax_rate
            
            subtotal_usd += item_subtotal
            total_tax_usd += item_tax
            db_items.append(SaleItem(
                product_id=product.id, quantity=item.quantity, 
                unit_price_usd=price, tax_rate=product.tax_rate, 
                applied_margin=product.profit_margin
            ))

        total_usd = subtotal_usd + total_tax_usd + (sale_in.delivery_amount_usd if sale_in.has_delivery else 0)
        db_sale = Sale(
            total_amount_usd=total_usd, total_tax_usd=total_tax_usd,
            has_delivery=sale_in.has_delivery, delivery_amount_usd=sale_in.delivery_amount_usd,
            user_id=user_id, customer_id=sale_in.customer_id, status="completed"
        )
        db.add(db_sale)
        await db.flush()

        for item in db_items:
            item.sale_id = db_sale.id
            db.add(item)

        for p_in in sale_in.payments:
            payment = Payment(
                sale_id=db_sale.id, method=p_in.method, amount=p_in.amount,
                currency=p_in.currency, exchange_rate=p_in.exchange_rate,
                amount_usd_equivalent=p_in.amount / p_in.exchange_rate if p_in.currency == "VES" else p_in.amount
            )
            db.add(payment)

        await db.commit()
        await db.refresh(db_sale, ["items", "payments", "customer"])
        return db_sale

    @staticmethod
    async def get_by_id(db: AsyncSession, sale_id: int):
        from sqlalchemy.orm import selectinload
        
        stmt = select(Sale).where(Sale.id == sale_id).options(
            selectinload(Sale.items).selectinload(SaleItem.product),
            selectinload(Sale.payments),
            selectinload(Sale.customer)
        )
        result = await db.execute(stmt)
        sale = result.scalar_one_or_none()
        
        if sale:
            if sale.customer:
                sale.customer_name = sale.customer.name
                sale.customer_phone = sale.customer.phone
                sale.customer_cedula = sale.customer.cedula
            for item in sale.items:
                if item.product:
                    item.name = item.product.name
                    item.barcode = item.product.barcode if item.product else None
        return sale
    @staticmethod
    async def get_stats(db: AsyncSession):
        now = datetime.now()
        
        # Start of periods
        start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_week = start_day - timedelta(days=now.weekday())
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        async def get_total(start_date):
            stmt = select(func.sum(Sale.total_amount_usd)).where(
                Sale.created_at >= start_date,
                Sale.status == "completed"
            )
            res = await db.execute(stmt)
            return res.scalar() or 0.0

        return {
            "today": await get_total(start_day),
            "week": await get_total(start_week),
            "month": await get_total(start_month),
            "year": await get_total(start_year)
        }
