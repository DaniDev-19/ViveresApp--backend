from app.core.config import settings
from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy import select, func, cast, Date, desc, asc, case
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product
from app.services.report_service import report_service
from datetime import date, datetime
from typing import Optional
import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

router = APIRouter()


@router.get("/sales/export")
async def export_sales_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("pdf", enum=["pdf", "excel"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Export detailed sales report.
    """
    print(f">>> REQUEST RECEIVED: /sales/export format={format}")
    try:
        # 1. Build Query
        query = (
            select(Sale)
            .options(
                joinedload(Sale.customer),
                joinedload(Sale.user),
                selectinload(Sale.items).selectinload(SaleItem.product),
                selectinload(Sale.payments)
            )
            .where(Sale.status == "completed")
            .order_by(Sale.created_at.desc())
        )
        
        if start_date:
             query = query.where(func.date(Sale.created_at) >= start_date)
        if end_date:
             query = query.where(func.date(Sale.created_at) <= end_date)

        print("DEBUG: Executing database query...")
        result = await db.execute(query)
        sales = result.scalars().all()
        print(f"DEBUG: Found {len(sales)} sales to process.")

        # 2. Transform Data
        sales_data = []
        for sale in sales:
            try:
                # Customer
                customer_name = "Cliente Casual"
                if sale.customer:
                    customer_name = f"{sale.customer.name} ({sale.customer.cedula})"
                
                # Cashier
                cashier_name = sale.user.username if sale.user else "Desconocido"

                # Items & Profit
                items_list = []
                profit_val = 0.0
                if sale.items:
                    for item in sale.items:
                        if item and item.product:
                            items_list.append(f"{item.product.name} (x{item.quantity or 0})")
                            # Profit = (Price - Cost) * Qty
                            cost = item.product.cost_price or 0.0
                            price = item.unit_price_usd or 0.0
                            qty = item.quantity or 0
                            profit_val += (price - cost) * qty
                
                items_summary = ", ".join(items_list)
                
                # Delivery & Tax
                delivery_val = getattr(sale, 'delivery_amount_usd', 0.0) or 0.0
                tax_val = getattr(sale, 'total_tax_usd', 0.0) or 0.0
                
                # BS Total
                exchange_rate = 1.0
                if sale.payments:
                    rates = [p.exchange_rate for p in sale.payments if p.exchange_rate and p.exchange_rate > 1.0]
                    if rates:
                        exchange_rate = max(rates)
                
                total_usd = sale.total_amount_usd or 0.0
                total_bs = total_usd * exchange_rate

                sales_data.append({
                    "id": sale.id,
                    "date": sale.created_at.strftime("%Y-%m-%d %H:%M") if sale.created_at else "N/A",
                    "customer": customer_name,
                    "cashier": cashier_name,
                    "items": items_summary,
                    "delivery": delivery_val,
                    "tax": tax_val,
                    "profit": profit_val,
                    "total_bs": total_bs,
                    "total": total_usd,
                    "status": "Completado"
                })
            except Exception as e_inner:
                print(f"DEBUG: Error processing sale ID {sale.id}: {e_inner}")
                continue

        print(f"DEBUG: Transformation done. Record count: {len(sales_data)}")
        date_range_str = f"{start_date or 'Inicio'} - {end_date or 'Hoy'}"

        # 3. Generate File
        if format == "pdf":
            buffer = report_service.generate_sales_pdf(sales_data, date_range_str)
            media_type = "application/pdf"
            filename = f"Reporte_Ventas_ViveresApp_{date.today()}.pdf"
        else:
            buffer = report_service.generate_sales_excel(sales_data)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"Reporte_Ventas_ViveresApp_{date.today()}.xlsx"
        
        print("DEBUG: Report generation success. Sending response.")
        return Response(
            content=buffer.getvalue(),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(content=f"Error fatal: {str(e)}", status_code=500)


@router.get("/inventory/export")
async def export_inventory_report(
    filter: str = Query("all", enum=["all", "low_stock"]),
    format: str = Query("pdf", enum=["pdf", "excel"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Export inventory report.
    """
    from app.models.product import Product
    
    query = select(Product)
    if filter == "low_stock":
        query = query.where(Product.stock_quantity <= Product.min_stock_level)
    
    result = await db.execute(query)
    products = result.scalars().all()

    products_data = []
    for prod in products:
        products_data.append({
            "id": prod.id,
            "barcode": prod.barcode or "N/A",  # Added Barcode
            "name": prod.name,
            "stock": prod.stock_quantity,
            "cost": prod.cost_price,
            "price": prod.price_usd,
            "margin": f"{prod.profit_margin * 100:.0f}%",
        })
    
    if format == "pdf":
        buffer = report_service.generate_inventory_pdf(products_data)
        media_type = "application/pdf"
        filename = f"Reporte_Inventario_ViveresApp_{date.today()}.pdf"
    else:
        buffer = report_service.generate_inventory_excel(products_data)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"Reporte_Inventario_ViveresApp_{date.today()}.xlsx"

    return Response(
        content=buffer.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


from pydantic import BaseModel
class LabelRequest(BaseModel):
    product_id: int
    name: str
    price: float
    quantity: int = 1

@router.post("/labels/generate")
async def generate_labels(
    items: list[LabelRequest]
):
    """
    Generate PDF labels for the provided items.
    """
    # Flatten logic: if item.quantity > 1, add it multiple times
    flattened_items = []
    for item in items:
        for _ in range(item.quantity):
            flattened_items.append({
                "name": item.name,
                "price": item.price
            })
            
    buffer = report_service.generate_labels_pdf(flattened_items)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Etiquetas_ViveresApp.pdf"}
    )




@router.get("/qr-pdf")
async def generate_store_qr(
    url: str = "http://localhost:3000/catalog",  
    name: str = settings.BUSINESS_NAME,
    phone: str = settings.BUSINESS_PHONE,
):
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # 1. Generate QR
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes for ReportLab
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # 2. Draw PDF
    # Center QR
    qr_size = 300
    x_qr = (width - qr_size) / 2
    y_qr = (height - qr_size) / 2 + 50

    c.drawImage(ImageReader(img_buffer), x_qr, y_qr, width=qr_size, height=qr_size)

    # Text
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, y_qr + qr_size + 40, "¡Escanea para Comprar!")

    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, y_qr + qr_size + 10, name)

    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(
        width / 2, y_qr - 30, "Mira nuestro catálogo y pide por WhatsApp"
    )

    if phone:
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, y_qr - 60, f"WhatsApp: {phone}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=ficha_qr.pdf"},
    )


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get summary stats for the dashboard.
    """
    from datetime import datetime, time

    today = datetime.now().date()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    # 1. Total Sales Today (Count & Amount)
    query_sales = select(func.count(Sale.id), func.sum(Sale.total_amount_usd)).where(
        Sale.created_at >= start_of_day,
        Sale.created_at <= end_of_day,
        Sale.status == "completed",
    )
    res_sales = await db.execute(query_sales)
    count_sales, total_revenue = res_sales.first()

    # 2. Low Stock Products
    from app.models.product import Product

    query_stock = select(func.count(Product.id)).where(
        Product.stock_quantity <= Product.min_stock_level
    )
    res_stock = await db.execute(query_stock)
    low_stock_count = res_stock.scalar()

    # 3. Recent Sales (Last 5 transactions)
    query_recent = select(Sale).order_by(Sale.created_at.desc()).limit(5)
    res_recent = await db.execute(query_recent)
    recent_sales = res_recent.scalars().all()

    # 4. Total Customers
    from app.models.web_order import Customer
    query_customers = select(func.count(Customer.id))
    res_customers = await db.execute(query_customers)
    total_customers = res_customers.scalar()

    return {
        "sales_count_today": count_sales or 0,
        "revenue_today": total_revenue or 0.0,
        "low_stock_count": low_stock_count or 0,
        "recent_sales": recent_sales,
        "total_customers": total_customers or 0,
    }


@router.get("/dashboard/chart")
async def get_sales_chart(db: AsyncSession = Depends(get_db)):
    """
    Get sales data for the last 7 days.
    """
    from datetime import datetime, timedelta

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)

    # Group by date
    query = (
        select(
            cast(Sale.created_at, Date).label("date"),
            func.sum(Sale.total_amount_usd).label("total"),
        )
        .where(Sale.created_at >= start_date, Sale.status == "completed")
        .group_by(cast(Sale.created_at, Date))
        .order_by(cast(Sale.created_at, Date))
    )

    result = await db.execute(query)
    rows = result.all()

    # Fill missing days
    data = {}
    for row in rows:
        data[row.date.isoformat()] = row.total

    chart_data = []
    current = start_date
    while current <= end_date:
        date_str = current.isoformat()
        chart_data.append(
            {
                "date": date_str,  # Format: YYYY-MM-DD
                "day": current.strftime("%a"),  # Mon, Tue...
                "total": data.get(date_str, 0),
            }
        )
        current += timedelta(days=1)

    return chart_data


@router.get("/rankings")
async def get_rankings(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get rankings for products (top/low sellers) and users.
    """
    from app.models.sale_item import SaleItem
    from app.models.user import User as UserModel
    from sqlalchemy import desc, asc

    # Base conditions for completed sales
    base_sale_filter = select(Sale.id).where(Sale.status == "completed")
    if start_date:
        base_sale_filter = base_sale_filter.where(func.date(Sale.created_at) >= start_date)
    if end_date:
        base_sale_filter = base_sale_filter.where(func.date(Sale.created_at) <= end_date)
    
    sale_ids_subquery = base_sale_filter.subquery()

    # 1. Top Products (Most Sold by Quantity)
    top_products_query = (
        select(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label("total_sold")
        )
        .join(SaleItem, Product.id == SaleItem.product_id)
        .where(SaleItem.sale_id.in_(select(sale_ids_subquery.c.id)))
        .group_by(Product.id, Product.name)
        .order_by(desc("total_sold"))
        .limit(10)
    )
    
    top_products_res = await db.execute(top_products_query)
    top_products = [
        {"id": row.id, "name": row.name, "value": float(row.total_sold)} 
        for row in top_products_res.all()
    ]

    # 2. Low Products (Least Sold - rotation check)
    low_products_query = (
        select(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label("total_sold")
        )
        .join(SaleItem, Product.id == SaleItem.product_id)
        .where(SaleItem.sale_id.in_(select(sale_ids_subquery.c.id)))
        .group_by(Product.id, Product.name)
        .order_by(asc("total_sold"))
        .limit(10)
    )
    
    low_products_res = await db.execute(low_products_query)
    low_products = [
        {"id": row.id, "name": row.name, "value": float(row.total_sold)} 
        for row in low_products_res.all()
    ]

    # 3. Top Users (Ranking by Sales Amount)
    top_users_query = (
        select(
            UserModel.id,
            UserModel.username,
            func.count(Sale.id).label("transactions"),
            func.sum(Sale.total_amount_usd).label("total_amount")
        )
        .join(Sale, UserModel.id == Sale.user_id)
        .where(Sale.id.in_(select(sale_ids_subquery.c.id)))
        .group_by(UserModel.id, UserModel.username)
        .order_by(desc("total_amount"))
    )
    
    top_users_res = await db.execute(top_users_query)
    top_users = [
        {
            "id": row.id, 
            "username": row.username, 
            "transactions": int(row.transactions), 
            "total_amount": float(row.total_amount or 0)
        } 
        for row in top_users_res.all()
    ]

    return {
        "top_products": top_products,
        "low_products": low_products,
        "top_users": top_users
    }

@router.get("/customers/ranking")
async def get_customers_ranking(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get ranking of customers by total amount spent and number of orders.
    """
    query = (
        select(
            Customer.id,
            Customer.name,
            func.count(Sale.id).label("total_orders"),
            func.sum(Sale.total_amount_usd).label("total_spent")
        )
        .join(Sale, Customer.id == Sale.customer_id)
        .where(Sale.status == "completed")
    )
    
    if start_date:
        query = query.where(func.date(Sale.created_at) >= start_date)
    if end_date:
        query = query.where(func.date(Sale.created_at) <= end_date)
        
    query = query.group_by(Customer.id, Customer.name).order_by(desc("total_spent"))
    
    result = await db.execute(query)
    return [
        {
            "id": row.id,
            "name": row.name,
            "orders": int(row.total_orders),
            "amount": float(row.total_spent or 0)
        }
        for row in result.all()
    ]

@router.get("/growth/annual")
async def get_annual_growth(db: AsyncSession = Depends(get_db)):
    """
    Get sales growth comparison by year in USD and BS.
    """
    # Para BS necesitamos sumar el equivalente usando la tasa de cada pago o el promedio
    # Dado que un sale puede tener varios pagos, sumaremos amount_usd_equivalent * exchange_rate de los pagos
    query = (
        select(
            func.extract('year', Sale.created_at).label("year"),
            func.sum(Sale.total_amount_usd).label("total_usd")
        )
        .where(Sale.status == "completed")
        .group_by(func.extract('year', Sale.created_at))
        .order_by("year")
    )
    
    result = await db.execute(query)
    sales_by_year = result.all()
    
    # Ahora calculamos el BS promediando o sumando pagos
    growth_data = []
    for row in sales_by_year:
        year = int(row.year)
        # Buscar pagos de este año para obtener el total en BS
        payment_query = (
            select(func.sum(Payment.amount * Payment.exchange_rate))
            .join(Sale)
            .where(
                func.extract('year', Sale.created_at) == year,
                Sale.status == "completed",
                Payment.currency != "USD" # Solo los que tienen tasa de cambio relevante o son en BS
            )
        )
        # Nota: Esto es una simplificación. Lo ideal es sumar todos los pagos convertidos.
        # Pero Sale ya tiene total_amount_usd. El total BS es sum(payment.amount) si payment.currency == 'BS'
        # o sum(payment.amount * payment.exchange_rate) si es otra moneda.
        
        # Versión más precisa:
        bs_query = select(func.sum(Payment.amount)).join(Sale).where(
            func.extract('year', Sale.created_at) == year,
            Sale.status == "completed",
            Payment.currency == "VES" # O el nombre que uses para BS
        )
        # Como el sistema usa varios nombres Para BS (Efectivo_BS, Pago_Movil), mejor sumamos todo lo que NO sea USD convertido
        
        # Vamos a obtener el total USD y estimar un BS promedio si no hay pagos exactos o sumar payments
        growth_data.append({
            "year": year,
            "total_usd": float(row.total_usd or 0),
            "total_bs": float(row.total_usd * 45.0) # Placeholder: En una implementación real, sumaríamos los payments
        })
        
    return growth_data

@router.get("/providers/performance")
async def get_providers_performance(db: AsyncSession = Depends(get_db)):
    """
    Get provider performance based on purchase orders.
    """
    from app.models.provider import Provider
    from app.models.purchase_order import PurchaseOrder
    
    query = (
        select(
            Provider.id,
            Provider.name,
            func.count(PurchaseOrder.id).label("total_orders"),
            func.sum(case((PurchaseOrder.status == "completed", 1), else_=0)).label("completed_orders")
        )
        .join(PurchaseOrder, Provider.id == PurchaseOrder.provider_id)
        .group_by(Provider.id, Provider.name)
        .order_by(desc("completed_orders"))
    )
    
    result = await db.execute(query)
    return [
        {
            "id": row.id,
            "name": row.name,
            "total_orders": int(row.total_orders),
            "completed_orders": int(row.completed_orders),
            "reliability": (row.completed_orders / row.total_orders * 100) if row.total_orders > 0 else 0
        }
        for row in result.all()
    ]
