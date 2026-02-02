from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.all_schemas import PurchaseOrderResponse, PurchaseOrderCreate, PurchaseOrderReceipt
from app.models.purchase import PurchaseOrder, PurchaseItem
from app.models.user import User
from app.services.audit_service import AuditService
from app.api import deps

router = APIRouter()


from sqlalchemy.orm import selectinload

@router.post("/", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_in: PurchaseOrderCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new purchase order with items.
    """
    # 1. Create Header
    order = PurchaseOrder(
        provider_id=order_in.provider_id,
        expected_date=order_in.expected_date,
        notes=order_in.notes,
        status="pending"
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # 2. Add Items
    for item_data in order_in.items:
        item = PurchaseItem(
            purchase_id=order.id,
            product_id=item_data.product_id,
            product_name=item_data.product_name,
            requested_quantity=item_data.requested_quantity,
            cost_price=item_data.cost_price,
            status="pending"
        )
        db.add(item)
    
    await db.commit()
    
    q = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == order.id)
        .options(selectinload(PurchaseOrder.items), selectinload(PurchaseOrder.provider))
    )
    res = await db.execute(q)
    return res.scalars().first()


@router.get("/", response_model=List[PurchaseOrderResponse])
async def read_purchases(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve purchase orders.
    """
    query = (
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items), selectinload(PurchaseOrder.provider))
        .offset(skip)
        .limit(limit)
        .order_by(PurchaseOrder.created_at.desc())
    )
    result = await db.execute(query)
    sales = result.scalars().all()
    return sales


@router.put("/{order_id}/receive", response_model=PurchaseOrderResponse)
async def receive_purchase_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    receipt_in: PurchaseOrderReceipt,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Finalizar la compra: Actualiza stock y costos reales.
    """
    query = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == order_id)
        .options(selectinload(PurchaseOrder.provider), selectinload(PurchaseOrder.items).selectinload(PurchaseItem.product))
    )
    result = await db.execute(query)
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "completed":
        raise HTTPException(status_code=400, detail="Order already completed")

    # Mapear datos recibidos por ID de item para acceso rápido
    receipt_map = {item.id: item for item in receipt_in.items}

    # 3. Update Items & Products
    for item in order.items:
        receipt_data = receipt_map.get(item.id)
        
        # Si no viene en el recibo, asumimos que no llegó nada o usamos valor por defecto
        # Pero lo ideal es que el frontend envíe todos.
        received_qty = receipt_data.received_quantity if receipt_data else 0
        actual_cost = receipt_data.actual_cost if receipt_data else item.cost_price or 0.0

        item.received_quantity = received_qty
        item.cost_price = actual_cost
        item.status = "verified" if received_qty == item.requested_quantity else "mismatch"
        db.add(item)

        if item.product_id:
            product = item.product # Ya cargado con selectinload
            if product:
                # Actualizar Inventario
                product.stock_quantity += received_qty
                
                # Actualizar Costo y Precio de Venta
                product.cost_price = actual_cost
                # Recalcular precio de venta usando margen y tax del producto
                product.price_usd = actual_cost * (1 + product.profit_margin) * (1 + product.tax_rate)
                
                db.add(product)

    order.status = "completed"
    db.add(order)

    await db.commit()
    await db.refresh(order)

    # Audit
    await AuditService.log_action(
        db, current_user.id, "RECEIVE", "purchases", f"Received order {order.id} with detailed receipt"
    )

    return order


from pydantic import BaseModel
class PurchaseItemLink(BaseModel):
    product_id: int

@router.put("/items/{item_id}/link")
async def link_purchase_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    link_in: PurchaseItemLink,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Link a manual purchase item to a real product ID.
    """
    item = await db.get(PurchaseItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.product_id = link_in.product_id
    # Optionally update name to match product if desired, but maybe keep original note?
    # Let's keep original name as record of what was ordered, but now it points to real product.
    
    db.add(item)
    await db.commit()
    return {"message": "Item linked successfully"}


@router.delete("/{order_id}")
async def delete_purchase_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a purchase order.
    """
    query = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    result = await db.execute(query)
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Optional: Prevent deleting completed orders? 
    # if order.status == 'completed':
    #     raise HTTPException(status_code=400, detail="Cannot delete completed order")
    
    # Check items to delete manually if no cascade
    q_items = select(PurchaseItem).where(PurchaseItem.purchase_id == order_id)
    res_items = await db.execute(q_items)
    items = res_items.scalars().all()
    for item in items:
        await db.delete(item)

    await db.delete(order)
    await db.commit()

    return {"message": "Order deleted successfully"}
