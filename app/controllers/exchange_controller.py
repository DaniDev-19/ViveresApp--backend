from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.sale_exchange import SaleExchange, SaleExchangeItemOut, SaleExchangeItemIn
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.models.payment import Payment
from app.models.settings import Setting
from app.schemas.sale_exchange import ExchangeCreate, ExchangeItemOutCreate, ExchangeItemInCreate
from app.services.audit_service import AuditService
from datetime import datetime


class ExchangeController:
    @staticmethod
    async def _get_setting(db: AsyncSession, key: str, default: int = 30) -> int:
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if setting and setting.value is not None:
            try:
                val = setting.value
                if isinstance(val, str):
                    val = val.strip('"')
                return int(val)
            except (ValueError, TypeError):
                pass
        return default

    @staticmethod
    async def _validate_exchange_eligibility(db: AsyncSession, sale: Sale) -> None:
        if sale.status not in ("completed",):
            raise ValueError("Solo se pueden cambiar productos de ventas con estado 'completada'. Esta venta ya fue devuelta o tiene otro estado.")
        
        days_limit = await ExchangeController._get_setting(db, "return_exchange_days_limit", 30)
        if (datetime.now() - sale.created_at.replace(tzinfo=None)).days > days_limit:
            raise ValueError(f"Excede el límite de {days_limit} días para cambios")

        # Check if sale already has an exchange
        existing = await db.execute(
            select(func.count(SaleExchange.id)).where(SaleExchange.sale_id == sale.id)
        )
        if existing.scalar() > 0:
            raise ValueError("Esta venta ya tiene un cambio registrado. No se permiten cambios duplicados.")

    @staticmethod
    async def create_exchange(
        db: AsyncSession,
        sale_id: int,
        exchange_in: ExchangeCreate,
        user_id: int
    ) -> SaleExchange:
        sale = await db.execute(
            select(Sale)
            .where(Sale.id == sale_id)
            .options(
                selectinload(Sale.items).selectinload(SaleItem.product),
                selectinload(Sale.payments)
            )
        )
        sale = sale.scalar_one_or_none()
        if not sale:
            raise ValueError("Venta no encontrada")

        await ExchangeController._validate_exchange_eligibility(db, sale)

        sale_items_map = {item.product_id: item for item in sale.items if item.product_id}
        
        total_out = 0.0
        total_in = 0.0
        items_out_data = []
        items_in_data = []

        for item_out in exchange_in.items_out:
            original_item = sale_items_map.get(item_out.product_id)
            if not original_item:
                raise ValueError(f"Producto {item_out.product_id} no está en esta venta")
            
            if item_out.quantity > original_item.quantity:
                raise ValueError(f"Cantidad a cambiar ({item_out.quantity}) excede la vendida ({original_item.quantity})")

            product = await db.get(Product, item_out.product_id)
            if not product:
                raise ValueError(f"Producto {item_out.product_id} no encontrado")

            unit_price = original_item.unit_price_usd
            subtotal = unit_price * item_out.quantity
            total_out += subtotal

            items_out_data.append({
                "product_id": product.id,
                "quantity": item_out.quantity,
                "unit_price_usd": unit_price,
                "subtotal_usd": subtotal
            })

        for item_in in exchange_in.items_in:
            product = await db.get(Product, item_in.product_id)
            if not product:
                raise ValueError(f"Producto nuevo {item_in.product_id} no encontrado")
            
            if product.stock_quantity < item_in.quantity:
                raise ValueError(f"Stock insuficiente para producto {product.name} (disponible: {product.stock_quantity})")

            unit_price = product.price_usd
            subtotal = unit_price * item_in.quantity
            total_in += subtotal

            items_in_data.append({
                "product_id": product.id,
                "quantity": item_in.quantity,
                "unit_price_usd": unit_price,
                "subtotal_usd": subtotal
            })

        difference = total_in - total_out

        exchange_obj = SaleExchange(
            sale_id=sale.id,
            user_id=user_id,
            total_difference_usd=difference,
            payment_method=exchange_in.payment_method,
            payment_amount_usd=abs(difference) if difference != 0 else 0,
            reason=exchange_in.reason,
            status="completed"
        )
        db.add(exchange_obj)
        await db.flush()

        for item_data in items_out_data:
            exchange_item = SaleExchangeItemOut(exchange_id=exchange_obj.id, **item_data)
            db.add(exchange_item)
            
            product = await db.get(Product, item_data["product_id"])
            if product:
                product.stock_quantity += item_data["quantity"]

        for item_data in items_in_data:
            exchange_item = SaleExchangeItemIn(exchange_id=exchange_obj.id, **item_data)
            db.add(exchange_item)
            
            product = await db.get(Product, item_data["product_id"])
            if product:
                product.stock_quantity -= item_data["quantity"]

        if difference > 0 and exchange_in.payment_method:
            payment = Payment(
                sale_id=sale.id,
                method=exchange_in.payment_method,
                amount=difference,
                currency="USD",
                exchange_rate=1.0,
                amount_usd_equivalent=difference
            )
            db.add(payment)
        elif difference < 0:
            refund_amount = abs(difference)
            method = exchange_in.payment_method or "credit_note"
            if method != "credit_note":
                payment = Payment(
                    sale_id=sale.id,
                    method=f"Refund_{method}",
                    amount=refund_amount,
                    currency="USD",
                    exchange_rate=1.0,
                    amount_usd_equivalent=refund_amount
                )
                db.add(payment)

        # Update sale status
        sale.status = "exchanged"

        await AuditService.log_action(
            db,
            user_id,
            "EXCHANGE",
            "sales",
            f"Cambio venta #{sale.id} - Diff: ${difference:+.2f} - OUT: {len(items_out_data)} items - IN: {len(items_in_data)} items",
            commit=False
        )

        await db.commit()
        await db.refresh(exchange_obj, ["items_out", "items_in"])
        return exchange_obj

    @staticmethod
    async def delete_exchange(
        db: AsyncSession,
        exchange_id: int,
        user_id: int
    ) -> bool:
        """Delete an exchange and reverse its effects."""
        result = await db.execute(
            select(SaleExchange)
            .where(SaleExchange.id == exchange_id)
            .options(
                selectinload(SaleExchange.items_out),
                selectinload(SaleExchange.items_in),
                selectinload(SaleExchange.sale)
            )
        )
        exchange_obj = result.scalar_one_or_none()
        if not exchange_obj:
            return False

        # Reverse stock: items_out were added back -> subtract them
        for item in exchange_obj.items_out:
            product = await db.get(Product, item.product_id)
            if product:
                product.stock_quantity -= item.quantity

        # Reverse stock: items_in were subtracted -> add them back
        for item in exchange_obj.items_in:
            product = await db.get(Product, item.product_id)
            if product:
                product.stock_quantity += item.quantity

        # Restore sale status
        sale = await db.get(Sale, exchange_obj.sale_id)
        if sale and sale.status == "exchanged":
            sale.status = "completed"

        await AuditService.log_action(
            db, user_id, "DELETE_EXCHANGE", "sales",
            f"Eliminado cambio #{exchange_obj.id} de venta #{exchange_obj.sale_id}",
            commit=False
        )

        await db.delete(exchange_obj)
        await db.commit()
        return True

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        sale_id: Optional[int] = None,
    ) -> List[SaleExchange]:
        query = select(SaleExchange).options(
            selectinload(SaleExchange.items_out).selectinload(SaleExchangeItemOut.product),
            selectinload(SaleExchange.items_in).selectinload(SaleExchangeItemIn.product),
            selectinload(SaleExchange.sale)
        ).order_by(SaleExchange.created_at.desc())

        if search:
            term = search.strip()
            if term.isdigit():
                query = query.where(SaleExchange.id == int(term))
        
        if sale_id:
            query = query.where(SaleExchange.sale_id == sale_id)

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, exchange_id: int) -> Optional[SaleExchange]:
        result = await db.execute(
            select(SaleExchange)
            .where(SaleExchange.id == exchange_id)
            .options(
                selectinload(SaleExchange.items_out).selectinload(SaleExchangeItemOut.product),
                selectinload(SaleExchange.items_in).selectinload(SaleExchangeItemIn.product),
                selectinload(SaleExchange.sale)
            )
        )
        return result.scalar_one_or_none()