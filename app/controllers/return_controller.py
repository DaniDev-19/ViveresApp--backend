from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String
from sqlalchemy.orm import selectinload
from app.models.sale_return import SaleReturn, SaleReturnItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.models.payment import Payment
from app.models.settings import Setting
from app.schemas.sale_return import ReturnCreate, ReturnItemCreate
from app.services.audit_service import AuditService
from datetime import datetime


class ReturnController:
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
    async def _validate_return_eligibility(db: AsyncSession, sale: Sale) -> None:
        if sale.status not in ("completed",):
            raise ValueError("Solo se pueden devolver ventas con estado 'completada'. Esta venta ya fue devuelta o tiene otro estado.")
        
        days_limit = await ReturnController._get_setting(db, "return_exchange_days_limit", 30)
        if (datetime.now() - sale.created_at.replace(tzinfo=None)).days > days_limit:
            raise ValueError(f"Excede el límite de {days_limit} días para devoluciones")

        # Check if sale already has a return
        existing = await db.execute(
            select(func.count(SaleReturn.id)).where(SaleReturn.sale_id == sale.id)
        )
        if existing.scalar() > 0:
            raise ValueError("Esta venta ya tiene una devolución registrada. No se permiten devoluciones duplicadas.")

    @staticmethod
    async def _generate_credit_note_code(db: AsyncSession) -> str:
        year = datetime.now().year
        result = await db.execute(
            select(func.count(SaleReturn.id)).where(
                func.extract('year', SaleReturn.created_at) == year
            )
        )
        count = result.scalar() or 0
        return f"NC-{year}-{count + 1:04d}"

    @staticmethod
    async def create_return(
        db: AsyncSession,
        sale_id: int,
        return_in: ReturnCreate,
        user_id: int
    ) -> SaleReturn:
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

        await ReturnController._validate_return_eligibility(db, sale)

        sale_items_map = {item.product_id: item for item in sale.items if item.product_id}
        
        total_refund = 0.0
        return_items_data = []
        all_items_returned = True

        for item_in in return_in.items:
            original_item = sale_items_map.get(item_in.product_id)
            if not original_item:
                raise ValueError(f"Producto {item_in.product_id} no está en esta venta")
            
            if item_in.quantity > original_item.quantity:
                raise ValueError(f"Cantidad a devolver ({item_in.quantity}) excede la vendida ({original_item.quantity})")

            if item_in.quantity < original_item.quantity:
                all_items_returned = False

            product = await db.get(Product, item_in.product_id)
            if not product:
                raise ValueError(f"Producto {item_in.product_id} no encontrado")

            unit_price = original_item.unit_price_usd
            subtotal = unit_price * item_in.quantity
            total_refund += subtotal

            return_items_data.append({
                "product_id": product.id,
                "quantity": item_in.quantity,
                "unit_price_usd": unit_price,
                "subtotal_usd": subtotal
            })

        # Check if some products from the sale were not included in the return
        if len(return_in.items) < len(sale_items_map):
            all_items_returned = False

        credit_note_code = None
        if return_in.refund_method == "credit_note":
            credit_note_code = await ReturnController._generate_credit_note_code(db)

        return_obj = SaleReturn(
            sale_id=sale.id,
            user_id=user_id,
            total_refund_usd=total_refund,
            refund_method=return_in.refund_method,
            credit_note_code=credit_note_code,
            reason=return_in.reason,
            status="completed"
        )
        db.add(return_obj)
        await db.flush()

        for item_data in return_items_data:
            return_item = SaleReturnItem(return_id=return_obj.id, **item_data)
            db.add(return_item)
            
            # Restore stock
            product = await db.get(Product, item_data["product_id"])
            if product:
                product.stock_quantity += item_data["quantity"]

        # Create refund payment record
        if return_in.refund_method == "cash":
            payment = Payment(
                sale_id=sale.id,
                method="Refund_Cash",
                amount=total_refund,
                currency="USD",
                exchange_rate=1.0,
                amount_usd_equivalent=total_refund
            )
            db.add(payment)
        elif return_in.refund_method == "original":
            original_payment = sale.payments[0] if sale.payments else None
            if original_payment:
                method = original_payment.method
                currency = original_payment.currency
                rate = original_payment.exchange_rate
                amount = total_refund * rate if currency == "VES" else total_refund
            else:
                method = "Original"
                currency = "USD"
                rate = 1.0
                amount = total_refund
                
            payment = Payment(
                sale_id=sale.id,
                method=f"Refund_{method}",
                amount=amount,
                currency=currency,
                exchange_rate=rate,
                amount_usd_equivalent=total_refund
            )
            db.add(payment)

        # Update sale status
        if all_items_returned:
            sale.status = "returned"
        else:
            sale.status = "partially_returned"

        await AuditService.log_action(
            db,
            user_id,
            "RETURN",
            "sales",
            f"Devolución venta #{sale.id} - ${total_refund:.2f} - {return_in.refund_method} - {len(return_items_data)} items - Nota: {credit_note_code or 'N/A'}",
            commit=False
        )

        await db.commit()
        await db.refresh(return_obj, ["items"])
        return return_obj

    @staticmethod
    async def delete_return(
        db: AsyncSession,
        return_id: int,
        user_id: int
    ) -> bool:
        """Delete a return and reverse its effects (restore sale status, adjust stock back)."""
        result = await db.execute(
            select(SaleReturn)
            .where(SaleReturn.id == return_id)
            .options(
                selectinload(SaleReturn.items),
                selectinload(SaleReturn.sale)
            )
        )
        return_obj = result.scalar_one_or_none()
        if not return_obj:
            return False

        # Reverse stock changes (remove stock that was added back)
        for item in return_obj.items:
            product = await db.get(Product, item.product_id)
            if product:
                product.stock_quantity -= item.quantity

        # Restore sale status to completed
        sale = await db.get(Sale, return_obj.sale_id)
        if sale and sale.status in ("returned", "partially_returned"):
            sale.status = "completed"

        # Remove refund payment records
        refund_payments = await db.execute(
            select(Payment).where(
                Payment.sale_id == return_obj.sale_id,
                Payment.method.like("Refund_%")
            )
        )
        for payment in refund_payments.scalars().all():
            await db.delete(payment)

        await AuditService.log_action(
            db, user_id, "DELETE_RETURN", "sales",
            f"Eliminada devolución #{return_obj.id} de venta #{return_obj.sale_id}",
            commit=False
        )

        await db.delete(return_obj)
        await db.commit()
        return True

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        sale_id: Optional[int] = None,
    ) -> List[SaleReturn]:
        query = select(SaleReturn).options(
            selectinload(SaleReturn.items).selectinload(SaleReturnItem.product),
            selectinload(SaleReturn.sale)
        ).order_by(SaleReturn.created_at.desc())

        if search:
            term = search.strip()
            if term.isdigit():
                query = query.where(
                    (SaleReturn.id == int(term)) | 
                    (SaleReturn.credit_note_code.ilike(f"%{term}%"))
                )
            else:
                query = query.where(SaleReturn.credit_note_code.ilike(f"%{term}%"))
        
        if sale_id:
            query = query.where(SaleReturn.sale_id == sale_id)

        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, return_id: int) -> Optional[SaleReturn]:
        result = await db.execute(
            select(SaleReturn)
            .where(SaleReturn.id == return_id)
            .options(
                selectinload(SaleReturn.items).selectinload(SaleReturnItem.product),
                selectinload(SaleReturn.sale)
            )
        )
        return result.scalar_one_or_none()