from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.web_order import WebOrder, WebOrderItem, Customer
from app.models.product import Product
from app.models.user import User
from app.schemas.web_order import WebOrderCreate, WebOrderResponse
from app.services.audit_service import AuditService
from app.api import deps
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/", response_model=WebOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_web_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_in: WebOrderCreate,
) -> Any:
    """
    Registrar un nuevo pedido web (Público).
    Busca o crea el cliente basado en Cédula.
    """
    # 1. Handle Customer (Find or Create)
    query_cust = select(Customer).where(Customer.cedula == order_in.customer.cedula)
    res_cust = await db.execute(query_cust)
    customer = res_cust.scalars().first()

    if not customer:
        customer = Customer(**order_in.customer.model_dump())
        db.add(customer)
        await db.flush()  # Get ID
    else:
        # Update info if changed? Optional.
        customer.phone = order_in.customer.phone  # Ensure latest contact
        customer.name = order_in.customer.name
        customer.address = order_in.customer.address
        customer.email = order_in.customer.email
        db.add(customer)
        pass

    # 2. Calculate Total & Prepare Items
    total_usd = 0.0
    db_items = []

    for item_in in order_in.items:
        product = await db.get(Product, item_in.product_id)
        if not product:
            continue  # Skip invalid items or raise error

        line_total = product.price_usd * item_in.quantity
        total_usd += line_total

        db_items.append(
            WebOrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=item_in.quantity,
                price_usd=product.price_usd,
            )
        )

    # 3. Create Order
    db_order = WebOrder(
        customer_id=customer.id,
        customer_data=order_in.customer.model_dump(),
        status="pending_review",
        total_estimated_usd=total_usd,
        payment_method=order_in.payment_method,
        payment_proof_url=order_in.payment_proof_url,
        transaction_ref=order_in.transaction_ref,
    )
    db.add(db_order)
    await db.flush()

    for item in db_items:
        item.web_order_id = db_order.id
        db.add(item)

    await db.commit()

    # Notify Admin
    await NotificationService.create_notification(
        db,
        title="Nuevo Pedido Web",
        message=f"Pedido #{db_order.id} recibido de {customer.name} por ${total_usd:.2f}",
        type="warning",
    )
    await db.commit()

    await db.refresh(db_order)

    # Needs explicit load for response model
    result = await db.execute(
        select(WebOrder)
        .where(WebOrder.id == db_order.id)
        .options(selectinload(WebOrder.items))
    )
    return result.scalars().first()


@router.get("/", response_model=List[WebOrderResponse])
async def read_web_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Listar pedidos web (Admin).
    """
    query = (
        select(WebOrder)
        .options(selectinload(WebOrder.items))
        .order_by(WebOrder.created_at.desc())
    )
    if status_filter:
        query = query.where(WebOrder.status == status_filter)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{order_id}/status", response_model=WebOrderResponse)
async def update_order_status(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    status: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Actualizar estado (approved, rejected, completed).
    """
    query = (
        select(WebOrder)
        .where(WebOrder.id == order_id)
        .options(selectinload(WebOrder.items).selectinload(WebOrderItem.product))
    )
    result = await db.execute(query)
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # Stock Deduction Logic
    if status == "approved" and order.status != "approved":
        for item in order.items:
            product = item.product
            if not product:
                continue # Should ideally error, but skip for safety if product deleted
            
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Stock insuficiente para {product.name}. Stock actual: {product.stock_quantity}"
                )
            
            product.stock_quantity -= item.quantity
            db.add(product)

    order.status = status
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Audit
    await AuditService.log_action(
        db,
        current_user.id,
        "UPDATE_STATUS",
        "web_orders",
        f"Order {order.id} status changed to {status}",
    )

    return order
