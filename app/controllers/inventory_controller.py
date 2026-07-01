from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional
from datetime import datetime, date

from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.user import User


class InventoryController:

    @staticmethod
    async def register_movement(
        db: AsyncSession,
        product_id: int,
        movement_type: str,  # 'purchase' | 'sale' | 'return' | 'exchange_in' | 'exchange_out' | 'adjustment'
        quantity_change: int,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        notes: Optional[str] = None,
        user_id: Optional[int] = None,
        commit: bool = False
    ) -> Optional[InventoryMovement]:
        """
        Registra físicamente un movimiento en la tabla de inventario calculando
        de forma automática el stock previo y el posterior a partir del estado actual.
        """
        product = await db.get(Product, product_id)
        if not product:
            return None

        # Asumimos que product.stock_quantity ya tiene el valor nuevo (después del movimiento)
        stock_after = product.stock_quantity
        stock_before = stock_after - quantity_change

        movement = InventoryMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity_change=quantity_change,
            reference_id=reference_id,
            reference_type=reference_type,
            stock_before=stock_before,
            stock_after=stock_after,
            notes=notes,
            user_id=user_id
        )
        db.add(movement)
        if commit:
            await db.commit()
            await db.refresh(movement)
        else:
            await db.flush()
        return movement

    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        product_id: int,
        quantity_change: int,
        notes: Optional[str],
        user_id: int
    ) -> Optional[Product]:
        """
        Realiza un ajuste manual directo al stock de un producto y registra el movimiento de inventario.
        """
        product = await db.get(Product, product_id)
        if not product:
            return None

        # Modificar stock actual
        product.stock_quantity += quantity_change

        # Registrar el movimiento físico de ajuste
        await InventoryController.register_movement(
            db=db,
            product_id=product_id,
            movement_type="adjustment",
            quantity_change=quantity_change,
            reference_id=None,
            reference_type="adjustment",
            notes=notes,
            user_id=user_id,
            commit=False
        )

        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def get_movements(
        db: AsyncSession,
        product_id: Optional[int] = None,
        product_search: Optional[str] = None,
        movement_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Consulta la tabla física inventory_movements con filtros y ordenación por fecha.
        """
        stmt = (
            select(InventoryMovement)
            .join(InventoryMovement.product)
            .options(
                selectinload(InventoryMovement.product),
                selectinload(InventoryMovement.user)
            )
            .order_by(desc(InventoryMovement.created_at))
        )

        if product_id is not None:
            stmt = stmt.where(InventoryMovement.product_id == product_id)
        if product_search:
            term = f"%{product_search}%"
            stmt = stmt.where(
                Product.name.ilike(term) | Product.barcode.ilike(term)
            )
        if movement_type:
            stmt = stmt.where(InventoryMovement.movement_type == movement_type)
        if date_from:
            stmt = stmt.where(InventoryMovement.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            stmt = stmt.where(InventoryMovement.created_at <= datetime.combine(date_to, datetime.max.time()))

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginated results
        result = await db.execute(stmt.offset(skip).limit(limit))
        movements = result.scalars().all()

        # Adaptar para el formato del JSON
        formatted = []
        for m in movements:
            formatted.append({
                "id": m.id,
                "type": m.movement_type,
                "type_label": {
                    "purchase": "Compra",
                    "sale": "Venta",
                    "return": "Devolución",
                    "exchange_in": "Cambio (Entrada)",
                    "exchange_out": "Cambio (Salida)",
                    "adjustment": "Ajuste manual"
                }.get(m.movement_type, m.movement_type.capitalize()),
                "direction": "in" if m.quantity_change > 0 else "out",
                "product_id": m.product_id,
                "product_name": m.product.name if m.product else f"Producto #{m.product_id}",
                "product_barcode": m.product.barcode if m.product else None,
                "quantity": abs(m.quantity_change),
                "quantity_change": m.quantity_change,
                "unit_price_usd": m.product.price_usd if m.product else 0.0,
                "stock_before": m.stock_before,
                "stock_after": m.stock_after,
                "reference_id": m.reference_id,
                "reference_label": {
                    "sale": f"V-{str(m.reference_id).zfill(6)}",
                    "purchase": f"OC-{str(m.reference_id).zfill(6)}",
                    "return": f"DEV-{str(m.reference_id).zfill(6)}",
                    "exchange": f"CAM-{str(m.reference_id).zfill(6)}",
                    "adjustment": "AJUSTE"
                }.get(m.reference_type or "adjustment", "AJUSTE"),
                "date": m.created_at.isoformat(),
                "notes": m.notes,
                "user": m.user.username if m.user else "Sistema"
            })

        return {"total": total, "movements": formatted}

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        product_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ):
        """
        Retorna totales sumados de entradas y salidas consultando la tabla física.
        """
        stmt = select(InventoryMovement)
        if product_id is not None:
            stmt = stmt.where(InventoryMovement.product_id == product_id)
        if date_from:
            stmt = stmt.where(InventoryMovement.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            stmt = stmt.where(InventoryMovement.created_at <= datetime.combine(date_to, datetime.max.time()))

        result = await db.execute(stmt)
        movements = result.scalars().all()

        total_in = sum(m.quantity_change for m in movements if m.quantity_change > 0)
        total_out = sum(abs(m.quantity_change) for m in movements if m.quantity_change < 0)

        by_type = {}
        for m in movements:
            by_type[m.movement_type] = by_type.get(m.movement_type, 0) + abs(m.quantity_change)

        return {
            "total_entries": total_in,
            "total_exits": total_out,
            "net_change": total_in - total_out,
            "total_movements": len(movements),
            "by_type": by_type,
        }
