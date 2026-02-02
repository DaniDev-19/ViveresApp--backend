from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.all_schemas import SaleCreate, SaleResponse
from app.models.sale import Sale, SaleItem, Payment
from app.models.product import Product
from app.models.user import User
from app.api import deps

router = APIRouter()


@router.get("/", response_model=list[SaleResponse])
async def get_sales(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Obtiene el historial de ventas.
    """
    from sqlalchemy import select, desc, cast, String
    
    stmt = select(Sale).order_by(desc(Sale.created_at))
    
    if search:
        # Search by ID (cast to string) or potentially other fields
        stmt = stmt.where(cast(Sale.id, String).like(f"%{search}%"))
        
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    sales = result.scalars().all()
    
    # Cargar relaciones y enriquecer con nombres
    for sale in sales:
        await db.refresh(sale, ["items", "payments"])
        for item in sale.items:
            product = await db.get(Product, item.product_id)
            if product:
                item.name = product.name
    
    return sales


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_in: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Crea una nueva venta con pagos mixtos y opción de delivery.
    Valida el stock disponible antes de procesar.
    """
    # 1. Calcular totales
    subtotal_usd = 0.0
    total_tax_usd = 0.0
    db_items = []

    try:
        # Verificar productos y stock
        for item in sale_in.items:
            product = await db.get(Product, item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con ID {item.product_id} no encontrado",
                )

            # Validar stock
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para '{product.name}'. Disponible: {product.stock_quantity}",
                )

            # Descontar stock
            product.stock_quantity -= item.quantity

            # Determinar precio final (usar precio del producto si no se sobreescribe)
            price = item.matched_price if item.matched_price else product.price_usd
            item_subtotal = price * item.quantity
            
            # Calcular IVA del item
            item_tax = item_subtotal * product.tax_rate
            
            subtotal_usd += item_subtotal
            total_tax_usd += item_tax

            db_items.append(
                SaleItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price_usd=price,
                    tax_rate=product.tax_rate,
                    applied_margin=product.profit_margin,
                )
            )

        # Calcular total final (subtotal + IVA + delivery)
        total_usd = subtotal_usd + total_tax_usd
        
        # Añadir Costo de Delivery
        if sale_in.has_delivery:
            total_usd += sale_in.delivery_amount_usd

        # Crear registro de Venta
        db_sale = Sale(
            total_amount_usd=total_usd,
            total_tax_usd=total_tax_usd,
            has_delivery=sale_in.has_delivery,
            delivery_amount_usd=sale_in.delivery_amount_usd,
            user_id=current_user.id,
            customer_id=sale_in.customer_id,
            status="completed",  # Por defecto completada si se paga al momento
        )
        db.add(db_sale)
        await db.flush()  # Obtener ID generado

        # Guardar items de la venta
        for item in db_items:
            item.sale_id = db_sale.id
            db.add(item)

        # Registrar Pagos
        for payment in sale_in.payments:
            db_payment = Payment(
                sale_id=db_sale.id,
                method=payment.method,
                amount=payment.amount,
                currency=payment.currency,
                exchange_rate=payment.exchange_rate,
                amount_usd_equivalent=payment.amount / payment.exchange_rate
                if payment.currency == "VES"
                else payment.amount,
            )
            db.add(db_payment)

        await db.commit()
        await db.refresh(db_sale, ["items", "payments", "customer"])
        
        # Enriquecer items con nombres de productos para la factura
        for item in db_sale.items:
            product = await db.get(Product, item.product_id)
            if product:
                item.name = product.name
        
        # Añadir datos del cliente si existe
        if db_sale.customer:
            db_sale.customer_name = db_sale.customer.name
            db_sale.customer_phone = db_sale.customer.phone
            db_sale.customer_cedula = db_sale.customer.cedula
        
        return db_sale

    except HTTPException:
        raise  # Re-lanzar excepciones HTTP conocidas
    except Exception as e:
        await db.rollback()  # Revertir cambios en caso de error inesperado
        print(f"Error procesando venta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la venta.",
        )
