from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.web_order import WebOrder
from app.models.web_order_item import WebOrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.schemas.web_order import WebOrderCreate
from app.services.notification_service import NotificationService
from app.services.audit_service import AuditService

class WebOrderController:
    @staticmethod
    async def create(db: AsyncSession, order_in: WebOrderCreate):
        query_cust = select(Customer).where(Customer.cedula == order_in.customer.cedula)
        res_cust = await db.execute(query_cust)
        customer = res_cust.scalars().first()
        if not customer:
            customer = Customer(**order_in.customer.model_dump())
            db.add(customer)
            await db.flush()
        else:
            customer.phone = order_in.customer.phone
            customer.name = order_in.customer.name
            customer.address = order_in.customer.address
            customer.email = order_in.customer.email
            db.add(customer)

        total_tax = 0.0
        total_usd = 0.0
        db_items = []
        for item_in in order_in.items:
            product = await db.get(Product, item_in.product_id)
            if product:
                line_subtotal = product.price_usd * item_in.quantity
                line_tax = line_subtotal * (product.tax_rate or 0.0) if getattr(product, 'apply_iva_web', True) else 0.0
                total_usd += line_subtotal
                total_tax += line_tax
                db_items.append(WebOrderItem(
                    product_id=product.id, 
                    product_name=product.name, 
                    quantity=item_in.quantity, 
                    price_usd=product.price_usd
                ))

        db_order = WebOrder(
            customer_id=customer.id, customer_data=order_in.customer.model_dump(),
            status="pending_review", 
            total_estimated_usd=total_usd + order_in.delivery_cost + total_tax,
            total_tax_usd=total_tax,
            collect_tax=order_in.collect_tax,
            payment_method=order_in.payment_method, payment_proof_url=order_in.payment_proof_url,
            transaction_ref=order_in.transaction_ref,
            delivery_type=order_in.delivery_type,
            delivery_cost=order_in.delivery_cost
        )
        db.add(db_order)
        await db.flush()
        for item in db_items:
            item.web_order_id = db_order.id
            db.add(item)
        
        await db.commit()
        await NotificationService.create_notification(db, title="Nuevo Pedido Web", message=f"Pedido #{db_order.id} recibido de {customer.name} por ${total_usd:.2f}", type="warning")
        await db.commit()
        await db.refresh(db_order, ["items"])
        return db_order

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100, status_filter: str = None):
        # 1. Total count query
        count_query = select(func.count(WebOrder.id))
        if status_filter:
            count_query = count_query.where(WebOrder.status == status_filter)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 2. Data query
        query = select(WebOrder).options(selectinload(WebOrder.items)).order_by(WebOrder.created_at.desc()).offset(skip).limit(limit)
        if status_filter:
            query = query.where(WebOrder.status == status_filter)
        
        result = await db.execute(query)
        orders = result.scalars().all()

        return {"items": orders, "total": total}

    @staticmethod
    async def update_status(db: AsyncSession, order_id: int, status: str, user_id: int):
        result = await db.execute(select(WebOrder).where(WebOrder.id == order_id).options(selectinload(WebOrder.items).selectinload(WebOrderItem.product)))
        order = result.scalars().first()
        if not order:
            return None
        
        if status == "approved" and order.status != "approved":
            # 1. Bloquear los productos necesarios para evitar carreras concurrentes
            product_ids = [item.product_id for item in order.items]
            stmt = select(Product).where(Product.id.in_(product_ids)).with_for_update()
            product_result = await db.execute(stmt)
            locked_products = {product.id: product for product in product_result.scalars().all()}

            # 2. Validar stock de TODOS los productos primero
            for item in order.items:
                product = locked_products.get(item.product_id)
                if not product:
                    raise HTTPException(status_code=400, detail=f"Producto '{item.product_name}' no encontrado en inventario")
                if product.stock_quantity < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Stock insuficiente para '{product.name}': Solicitado {item.quantity}, Disponible {product.stock_quantity}"
                    )

            # 3. Crear Venta usando los montos ya calculados en el pedido
            from app.models.sale import Sale, SaleStatus
            from app.models.sale_item import SaleItem
            from app.models.payment import Payment as PaymentModel

            final_total_usd = order.total_estimated_usd

            new_sale = Sale(
                total_amount_usd=final_total_usd,
                total_tax_usd=order.total_tax_usd,
                has_delivery=(order.delivery_type != "pickup"),
                delivery_amount_usd=order.delivery_cost,
                user_id=user_id,
                customer_id=order.customer_id,
                status=SaleStatus.COMPLETED
            )
            db.add(new_sale)
            await db.flush() # Para obtener el ID de la venta

            for item in order.items:
                product = locked_products[item.product_id]
                # Descontar stock
                product.stock_quantity -= item.quantity
                db.add(product)

                # Crear item de venta
                sale_item = SaleItem(
                    sale_id=new_sale.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price_usd=item.price_usd,
                    tax_rate=(getattr(product, 'tax_rate', 0.0) or 0.0) if getattr(product, 'apply_iva_web', True) else 0.0,
                    applied_margin=getattr(product, 'profit_margin', 0.0)
                )
                db.add(sale_item)

            # Registrar el pago
            payment = PaymentModel(
                sale_id=new_sale.id,
                method=order.payment_method or "Other",
                amount=final_total_usd,
                currency="USD",
                exchange_rate=1.0,
                amount_usd_equivalent=final_total_usd
            )
            db.add(payment)

            # Guardar vínculo
            order.sale_id = new_sale.id

        order.status = status
        db.add(order)
        await db.commit()
        await AuditService.log_action(db, user_id, "UPDATE_STATUS", "web_orders", f"Pedido {order.id} cambió a {status}")
        return order
