from app.core.config import settings
from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy import select, func, cast, Date, desc, asc, case
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.api import deps
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
from reportlab.lib import colors

router = APIRouter()


@router.get("/sales/export")
async def export_sales_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("pdf", enum=["pdf", "excel"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
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
            content_disposition = f"inline; filename={filename}"
        else:
            buffer = report_service.generate_sales_excel(sales_data)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"Reporte_Ventas_ViveresApp_{date.today()}.xlsx"
            content_disposition = f"attachment; filename={filename}"
        
        print("DEBUG: Report generation success. Sending response.")
        return Response(
            content=buffer.getvalue(),
            media_type=media_type,
            headers={"Content-Disposition": content_disposition}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(content=f"Error fatal: {str(e)}", status_code=500)


@router.get("/inventory/export")
async def export_inventory_report(
    filter: str = Query("all", enum=["all", "low_stock"]),
    format: str = Query("pdf", enum=["pdf", "excel"]),
    type: str = Query("standard", enum=["standard", "code_name", "prices"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
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
            "offer_price": prod.offer_price_usd or 0.0,
            "margin": f"{prod.profit_margin * 100:.0f}%",
        })
    
    if format == "pdf":
        buffer = report_service.generate_inventory_pdf(products_data, report_type=type)
        media_type = "application/pdf"
        filename = f"Reporte_Inventario_ViveresApp_{date.today()}.pdf"
        content_disposition = f"inline; filename={filename}"
    else:
        buffer = report_service.generate_inventory_excel(products_data, report_type=type)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"Reporte_Inventario_ViveresApp_{date.today()}.xlsx"
        content_disposition = f"attachment; filename={filename}"

    return Response(
        content=buffer.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": content_disposition}
    )


from pydantic import BaseModel
class LabelRequest(BaseModel):
    product_id: int
    name: str
    price: float
    quantity: int = 1

@router.post("/labels/generate")
async def generate_labels(
    items: list[LabelRequest],
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
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
        headers={"Content-Disposition": "inline; filename=Etiquetas_ViveresApp.pdf"}
    )




@router.get("/qr-pdf")
async def generate_store_qr(
    url: str = "http://localhost:3000/catalog",  
    name: str = settings.BUSINESS_NAME,
    phone: str = settings.BUSINESS_PHONE,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
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
    img.save(img_buffer)
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
        headers={"Content-Disposition": "inline; filename=ficha_qr.pdf"},
    )


@router.get("/payment-qr/pago-movil")
async def generate_pago_movil_qr(
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Format data for QR
    qr_data = f"pagomovil:banco={settings.PAGO_MOVIL_BANCO}&telf={settings.PAGO_MOVIL_TELEFONO}&rif={settings.PAGO_MOVIL_RIF_CI}"
    
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_buffer = io.BytesIO()
    img.save(img_buffer)
    img_buffer.seek(0)

    # Draw layout
    c.setFillColor(colors.HexColor("#4F46E5"))
    c.rect(0, height - 120, width, 120, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 60, "FICHA DE PAGO MÓVIL")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 90, settings.BUSINESS_NAME.upper())

    # QR code
    qr_size = 280
    x_qr = (width - qr_size) / 2
    y_qr = height - 160 - qr_size
    c.drawImage(ImageReader(img_buffer), x_qr, y_qr, width=qr_size, height=qr_size)

    # Details panel background
    c.setFillColor(colors.HexColor("#F9FAFB"))
    c.roundRect(80, 80, width - 160, 180, 15, fill=True, stroke=True)
    c.setStrokeColor(colors.HexColor("#E5E7EB"))

    # Details text
    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, 230, "DATOS DE PAGO")

    y_text = 200
    
    bank_names = {
        "0102": "Banco de Venezuela (0102)",
        "0108": "Provincial (0108)",
        "0105": "Mercantil (0105)",
        "0134": "Banesco (0134)",
        "0191": "BNC (0191)",
        "0172": "Bancamiga (0172)",
        "0114": "Bancaribe (0114)",
        "0115": "Exterior (0115)",
        "0128": "Caroní (0128)",
        "0151": "Fondo Común (0151)",
        "0163": "Del Tesoro (0163)",
        "0166": "Agrícola (0166)",
        "0168": "Bancrecer (0168)",
        "0171": "Activo (0171)",
        "0174": "Banplus (0174)",
        "0175": "Bicentenario (0175)",
        "0177": "Banfanb (0177)",
        "0196": "Mi Banco (0196)",
    }
    bank_display = bank_names.get(settings.PAGO_MOVIL_BANCO, f"Código Banco: {settings.PAGO_MOVIL_BANCO}")

    details = [
        ("Banco:", bank_display),
        ("Teléfono:", settings.PAGO_MOVIL_TELEFONO),
        ("C.I. / RIF:", settings.PAGO_MOVIL_RIF_CI),
        ("Titular:", settings.PAGO_MOVIL_NOMBRE),
    ]

    for label, val in details:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#4F46E5"))
        c.drawString(120, y_text, label)
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor("#1F2937"))
        c.drawString(240, y_text, val)
        y_text -= 25

    # Footer
    c.setFillColor(colors.HexColor("#9CA3AF"))
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(width / 2, 40, "¡Gracias por su compra! Por favor envíe el capture del pago para verificar.")

    c.showPage()
    c.save()

    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=pago_movil_qr.pdf"},
    )


@router.get("/payment-qr/digital")
async def generate_digital_qr(
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # 1. Paypal QR
    paypal_data = f"https://www.paypal.com/paypalme/{settings.PAYPAL_CORREO.split('@')[0]}" if "@" in settings.PAYPAL_CORREO else settings.PAYPAL_CORREO
    if not paypal_data.startswith("http"):
        paypal_data = f"mailto:{settings.PAYPAL_CORREO}"
        
    qr_paypal = qrcode.QRCode(box_size=5, border=2)
    qr_paypal.add_data(paypal_data)
    qr_paypal.make(fit=True)
    img_paypal = qr_paypal.make_image(fill_color="black", back_color="white")
    
    img_buffer_paypal = io.BytesIO()
    img_paypal.save(img_buffer_paypal)
    img_buffer_paypal.seek(0)

    # 2. Binance QR
    binance_data = settings.BINANCE_PAY_ID
    qr_binance = qrcode.QRCode(box_size=5, border=2)
    qr_binance.add_data(binance_data)
    qr_binance.make(fit=True)
    img_binance = qr_binance.make_image(fill_color="black", back_color="white")
    
    img_buffer_binance = io.BytesIO()
    img_binance.save(img_buffer_binance)
    img_buffer_binance.seek(0)

    # 3. Zinli QR
    zinli_data = f"mailto:{settings.ZINLI_CORREO}"
    qr_zinli = qrcode.QRCode(box_size=5, border=2)
    qr_zinli.add_data(zinli_data)
    qr_zinli.make(fit=True)
    img_zinli = qr_zinli.make_image(fill_color="black", back_color="white")
    
    img_buffer_zinli = io.BytesIO()
    img_zinli.save(img_buffer_zinli)
    img_buffer_zinli.seek(0)

    # 4. Airtm QR
    airtm_data = f"mailto:{settings.AIRTM_CORREO}"
    qr_airtm = qrcode.QRCode(box_size=5, border=2)
    qr_airtm.add_data(airtm_data)
    qr_airtm.make(fit=True)
    img_airtm = qr_airtm.make_image(fill_color="black", back_color="white")
    
    img_buffer_airtm = io.BytesIO()
    img_airtm.save(img_buffer_airtm)
    img_buffer_airtm.seek(0)

    # Draw layout
    c.setFillColor(colors.HexColor("#0F172A"))
    c.rect(0, height - 100, width, 100, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 50, "MÉTODOS DE PAGO INTERNACIONAL")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 75, settings.BUSINESS_NAME.upper())

    col_width = width / 2
    qr_size = 140

    # ---- FILA 1: PayPal & Binance Pay ----
    # PayPal (Col 1, Fila 1)
    c.setFillColor(colors.HexColor("#003087"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(col_width / 2, height - 130, "PayPal")
    
    x_paypal = (col_width - qr_size) / 2
    y_paypal = height - 145 - qr_size
    c.drawImage(ImageReader(img_buffer_paypal), x_paypal, y_paypal, width=qr_size, height=qr_size)
    
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(col_width / 2, y_paypal - 15, "Correo PayPal:")
    c.setFont("Helvetica", 10)
    c.drawCentredString(col_width / 2, y_paypal - 30, settings.PAYPAL_CORREO)

    # Binance Pay (Col 2, Fila 1)
    c.setFillColor(colors.HexColor("#F0B90B"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(col_width + (col_width / 2), height - 130, "Binance Pay")
    
    x_binance = col_width + (col_width - qr_size) / 2
    y_binance = height - 145 - qr_size
    c.drawImage(ImageReader(img_buffer_binance), x_binance, y_binance, width=qr_size, height=qr_size)
    
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(col_width + (col_width / 2), y_binance - 15, "Binance Pay ID:")
    c.setFont("Helvetica", 10)
    c.drawCentredString(col_width + (col_width / 2), y_binance - 30, settings.BINANCE_PAY_ID)

    # ---- FILA 2: Zinli & Airtm ----
    # Zinli (Col 1, Fila 2)
    c.setFillColor(colors.HexColor("#5D3FD3"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(col_width / 2, y_paypal - 70, "Zinli")
    
    x_zinli = (col_width - qr_size) / 2
    y_zinli = y_paypal - 85 - qr_size
    c.drawImage(ImageReader(img_buffer_zinli), x_zinli, y_zinli, width=qr_size, height=qr_size)
    
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(col_width / 2, y_zinli - 15, "Correo Zinli:")
    c.setFont("Helvetica", 10)
    c.drawCentredString(col_width / 2, y_zinli - 30, settings.ZINLI_CORREO)

    # Airtm (Col 2, Fila 2)
    c.setFillColor(colors.HexColor("#007A87"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(col_width + (col_width / 2), y_paypal - 70, "Airtm")
    
    x_airtm = col_width + (col_width - qr_size) / 2
    y_airtm = y_paypal - 85 - qr_size
    c.drawImage(ImageReader(img_buffer_airtm), x_airtm, y_airtm, width=qr_size, height=qr_size)
    
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(col_width + (col_width / 2), y_airtm - 15, "Correo Airtm:")
    c.setFont("Helvetica", 10)
    c.drawCentredString(col_width + (col_width / 2), y_airtm - 30, settings.AIRTM_CORREO)

    # Line dividers
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.setLineWidth(1)
    c.line(col_width, height - 100, col_width, 160)
    c.line(40, y_paypal - 45, width - 40, y_paypal - 45)

    # Info box at bottom
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.roundRect(50, 45, width - 100, 85, 10, fill=True, stroke=True)
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, 105, "INSTRUCCIONES DE PAGO")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 85, "1. Abre la aplicación de tu billetera y escanea el código correspondiente.")
    c.drawCentredString(width / 2, 68, "2. Introduce el monto a pagar en dólares y envía el capture al comercio.")

    c.showPage()
    c.save()

    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=pagos_digitales_qr.pdf"},
    )


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
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
async def get_sales_chart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
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
async def get_annual_growth(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    """
    Get sales growth and profit comparison by year in USD, BCV, and USDT rates.
    """
    from app.services.currency import currency_service
    rates = await currency_service.get_latest_rates(db)
    bcv_val = 45.0
    usdt_val = 48.0
    for r in rates:
        if r.currency == "BCV":
            bcv_val = r.rate
        elif r.currency == "USDT":
            usdt_val = r.rate

    # Subquery to calculate profit per sale
    profit_subquery = (
        select(
            SaleItem.sale_id,
            func.sum((SaleItem.unit_price_usd - Product.cost_price) * SaleItem.quantity).label("sale_profit")
        )
        .join(Product, Product.id == SaleItem.product_id)
        .group_by(SaleItem.sale_id)
        .subquery()
    )

    query = (
        select(
            func.extract('year', Sale.created_at).label("year"),
            func.sum(Sale.total_amount_usd).label("total_usd"),
            func.sum(func.coalesce(profit_subquery.c.sale_profit, 0)).label("total_profit")
        )
        .outerjoin(profit_subquery, profit_subquery.c.sale_id == Sale.id)
        .where(Sale.status == "completed")
        .group_by(func.extract('year', Sale.created_at))
        .order_by("year")
    )
    
    result = await db.execute(query)
    sales_by_year = result.all()
    
    growth_data = []
    for row in sales_by_year:
        year = int(row.year)
        total_usd = float(row.total_usd or 0)
        total_profit = float(row.total_profit or 0)
        
        growth_data.append({
            "year": year,
            "total_usd": total_usd,
            "total_bs_bcv": total_usd * bcv_val,
            "total_bs_usdt": total_usd * usdt_val,
            "profit_usd": total_profit,
            "profit_bs_bcv": total_profit * bcv_val,
            "profit_bs_usdt": total_profit * usdt_val
        })
        
    return growth_data


@router.get("/growth/monthly")
async def get_monthly_growth(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    """
    Get monthly sales and profit for the selected year in USD, BCV, and USDT rates.
    """
    if not year:
        year = datetime.now().year
    
    # Subquery to calculate profit per sale
    profit_subquery = (
        select(
            SaleItem.sale_id,
            func.sum((SaleItem.unit_price_usd - Product.cost_price) * SaleItem.quantity).label("sale_profit")
        )
        .join(Product, Product.id == SaleItem.product_id)
        .group_by(SaleItem.sale_id)
        .subquery()
    )
    
    query = (
        select(
            func.extract('month', Sale.created_at).label("month"),
            func.sum(Sale.total_amount_usd).label("total_usd"),
            func.sum(func.coalesce(profit_subquery.c.sale_profit, 0)).label("total_profit")
        )
        .outerjoin(profit_subquery, profit_subquery.c.sale_id == Sale.id)
        .where(
            Sale.status == "completed",
            func.extract('year', Sale.created_at) == year
        )
        .group_by(func.extract('month', Sale.created_at))
        .order_by("month")
    )
    
    result = await db.execute(query)
    sales_by_month = result.all()
    
    from app.services.currency import currency_service
    rates = await currency_service.get_latest_rates(db)
    bcv_val = 45.0
    usdt_val = 48.0
    for r in rates:
        if r.currency == "BCV":
            bcv_val = r.rate
        elif r.currency == "USDT":
            usdt_val = r.rate
            
    months_names = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    monthly_data = []
    sales_map = {int(row.month): row for row in sales_by_month}
    
    for m in range(1, 13):
        row = sales_map.get(m)
        total_usd = float(row.total_usd or 0) if row else 0.0
        total_profit = float(row.total_profit or 0) if row else 0.0
        
        monthly_data.append({
            "month_num": m,
            "month_name": months_names[m],
            "total_usd": total_usd,
            "total_bs_bcv": total_usd * bcv_val,
            "total_bs_usdt": total_usd * usdt_val,
            "profit_usd": total_profit,
            "profit_bs_bcv": total_profit * bcv_val,
            "profit_bs_usdt": total_profit * usdt_val
        })
        
    return monthly_data


@router.get("/growth/monthly/export")
async def export_monthly_growth_report(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    """
    Export monthly growth report for the selected year as a PDF.
    """
    if not year:
        year = datetime.now().year
        
    monthly_data = await get_monthly_growth(year=year, db=db, current_user=current_user)
    
    buffer = report_service.generate_monthly_growth_pdf(monthly_data, year)
    
    filename = f"Reporte_Mensual_{year}_{date.today()}.pdf"
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/rankings/export")
async def export_rankings_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    """
    Export all rankings and performance metrics as a single PDF.
    """
    from app.models.sale_item import SaleItem
    from app.models.user import User as UserModel
    from app.models.provider import Provider
    from app.models.purchase_order import PurchaseOrder
    
    base_sale_filter = select(Sale.id).where(Sale.status == "completed")
    if start_date:
        base_sale_filter = base_sale_filter.where(func.date(Sale.created_at) >= start_date)
    if end_date:
        base_sale_filter = base_sale_filter.where(func.date(Sale.created_at) <= end_date)
    
    sale_ids_subquery = base_sale_filter.subquery()

    # Top Products
    top_products_query = (
        select(Product.id, Product.name, func.sum(SaleItem.quantity).label("total_sold"))
        .join(SaleItem, Product.id == SaleItem.product_id)
        .where(SaleItem.sale_id.in_(select(sale_ids_subquery.c.id)))
        .group_by(Product.id, Product.name)
        .order_by(desc("total_sold")).limit(10)
    )
    top_products_res = await db.execute(top_products_query)
    top_products = [{"id": row.id, "name": row.name, "value": float(row.total_sold)} for row in top_products_res.all()]

    # Low Products
    low_products_query = (
        select(Product.id, Product.name, func.sum(SaleItem.quantity).label("total_sold"))
        .join(SaleItem, Product.id == SaleItem.product_id)
        .where(SaleItem.sale_id.in_(select(sale_ids_subquery.c.id)))
        .group_by(Product.id, Product.name)
        .order_by(asc("total_sold")).limit(10)
    )
    low_products_res = await db.execute(low_products_query)
    low_products = [{"id": row.id, "name": row.name, "value": float(row.total_sold)} for row in low_products_res.all()]

    # Top Users
    top_users_query = (
        select(UserModel.id, UserModel.username, func.count(Sale.id).label("transactions"), func.sum(Sale.total_amount_usd).label("total_amount"))
        .join(Sale, UserModel.id == Sale.user_id)
        .where(Sale.id.in_(select(sale_ids_subquery.c.id)))
        .group_by(UserModel.id, UserModel.username)
        .order_by(desc("total_amount"))
    )
    top_users_res = await db.execute(top_users_query)
    top_users = [
        {"id": row.id, "username": row.username, "transactions": int(row.transactions), "total_amount": float(row.total_amount or 0)}
        for row in top_users_res.all()
    ]

    # Top Customers
    top_customers_query = (
        select(Customer.id, Customer.name, func.count(Sale.id).label("total_orders"), func.sum(Sale.total_amount_usd).label("total_spent"))
        .join(Sale, Customer.id == Sale.customer_id)
        .where(Sale.status == "completed")
    )
    if start_date:
        top_customers_query = top_customers_query.where(func.date(Sale.created_at) >= start_date)
    if end_date:
        top_customers_query = top_customers_query.where(func.date(Sale.created_at) <= end_date)
    top_customers_query = top_customers_query.group_by(Customer.id, Customer.name).order_by(desc("total_spent")).limit(10)
    top_customers_res = await db.execute(top_customers_query)
    top_customers = [
        {"id": row.id, "name": row.name, "orders": int(row.total_orders), "amount": float(row.total_spent or 0)}
        for row in top_customers_res.all()
    ]

    # Top Providers
    providers_query = (
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
    providers_res = await db.execute(providers_query)
    top_providers = [
        {
            "id": row.id,
            "name": row.name,
            "total_orders": int(row.total_orders),
            "completed_orders": int(row.completed_orders),
            "reliability": (row.completed_orders / row.total_orders * 100) if row.total_orders > 0 else 0
        }
        for row in providers_res.all()
    ]

    rankings_data = {
        "top_products": top_products,
        "low_products": low_products,
        "top_users": top_users,
        "top_customers": top_customers,
        "top_providers": top_providers
    }

    date_range_str = f"{start_date or 'Inicio'} - {end_date or 'Hoy'}"
    buffer = report_service.generate_rankings_pdf(rankings_data, date_range_str)
    
    filename = f"Reporte_Rankings_{date.today()}.pdf"
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

@router.get("/providers/performance")
async def get_providers_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
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


@router.get("/cash-close")
async def export_cash_close_report(
    date_str: Optional[str] = Query(None, description="Fecha en formato YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    from datetime import time
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now().date()
    else:
        target_date = datetime.now().date()

    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)

    stmt = (
        select(Sale)
        .options(
            selectinload(Sale.payments),
            selectinload(Sale.items).selectinload(SaleItem.product)
        )
        .where(
            Sale.created_at >= start_of_day,
            Sale.created_at <= end_of_day,
            Sale.status == "completed"
        )
    )
    res = await db.execute(stmt)
    sales = res.scalars().all()

    total_sales_count = len(sales)
    total_revenue_usd = sum(s.total_amount_usd for s in sales)
    total_tax_usd = sum(s.tax_amount_usd for s in sales)
    
    total_profit_usd = 0.0
    for s in sales:
        sale_profit = 0.0
        for item in s.items:
            cost = item.product.cost_price if item.product else 0.0
            sale_profit += (item.price_usd - cost) * item.quantity
        total_profit_usd += sale_profit

    payment_methods_info = {
        "efectivo_usd": {"name": "Efectivo (USD)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "USD"},
        "efectivo_ves": {"name": "Efectivo (VES)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "VES"},
        "pago_movil": {"name": "Pago Móvil (VES)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "VES"},
        "punto": {"name": "Punto de Venta (VES)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "VES"},
        "paypal": {"name": "PayPal (USD)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "USD"},
        "binance": {"name": "Binance Pay (USD)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "USD"},
        "zinli": {"name": "Zinli (USD)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "USD"},
        "airtm": {"name": "Airtm (USD)", "count": 0, "amount": 0.0, "amount_usd": 0.0, "currency": "USD"},
    }

    for s in sales:
        for p in s.payments:
            method_key = p.method.lower()
            if "efectivo" in method_key:
                if p.currency.upper() == "USD":
                    key = "efectivo_usd"
                else:
                    key = "efectivo_ves"
            elif "pago" in method_key or "movil" in method_key:
                key = "pago_movil"
            elif "punto" in method_key or "tarjeta" in method_key or "pos" in method_key:
                key = "punto"
            elif "paypal" in method_key:
                key = "paypal"
            elif "binance" in method_key:
                key = "binance"
            elif "zinli" in method_key:
                key = "zinli"
            elif "airtm" in method_key:
                key = "airtm"
            else:
                key = None
            
            if key and key in payment_methods_info:
                payment_methods_info[key]["count"] += 1
                payment_methods_info[key]["amount"] += p.amount
                payment_methods_info[key]["amount_usd"] += p.amount_usd_equivalent
            elif key is None:
                dyn_key = p.method
                if dyn_key not in payment_methods_info:
                    payment_methods_info[dyn_key] = {
                        "name": p.method.capitalize(),
                        "count": 0,
                        "amount": 0.0,
                        "amount_usd": 0.0,
                        "currency": p.currency.upper()
                    }
                payment_methods_info[dyn_key]["count"] += 1
                payment_methods_info[dyn_key]["amount"] += p.amount
                payment_methods_info[dyn_key]["amount_usd"] += p.amount_usd_equivalent

    cash_data = {
        "total_sales_count": total_sales_count,
        "total_revenue_usd": total_revenue_usd,
        "total_tax_usd": total_tax_usd,
        "total_profit_usd": total_profit_usd,
        "payment_breakdown": [val for val in payment_methods_info.values() if val["count"] > 0 or val["amount"] > 0]
    }

    pdf_buffer = report_service.generate_cash_close_pdf(cash_data, target_date.strftime("%d/%m/%Y"))

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=cierre_caja_{target_date.strftime('%Y%m%d')}.pdf"},
    )


@router.get("/low-stock/export")
async def export_low_stock_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    stmt = select(Product).where(Product.stock_quantity <= Product.min_stock_level).order_by(Product.stock_quantity.asc())
    res = await db.execute(stmt)
    products = res.scalars().all()

    products_data = []
    for p in products:
        provider_name = "Sin Proveedor"
        from app.models.purchase_item import PurchaseItem
        from app.models.purchase_order import PurchaseOrder
        from app.models.provider import Provider
        
        prov_stmt = (
            select(Provider.name)
            .join(PurchaseOrder, PurchaseOrder.provider_id == Provider.id)
            .join(PurchaseItem, PurchaseItem.purchase_id == PurchaseOrder.id)
            .where(PurchaseItem.product_id == p.id, PurchaseOrder.status == "received")
            .order_by(PurchaseOrder.created_at.desc())
            .limit(1)
        )
        prov_res = await db.execute(prov_stmt)
        latest_prov = prov_res.scalar_one_or_none()
        if latest_prov:
            provider_name = latest_prov

        refill_qty = max(10, (p.min_stock_level * 3) - p.stock_quantity)
        
        products_data.append({
            "barcode": p.barcode,
            "name": p.name,
            "stock": p.stock_quantity,
            "min_stock": p.min_stock_level,
            "suggested_refill": refill_qty,
            "cost_usd": p.cost_price,
            "total_cost_usd": refill_qty * p.cost_price,
            "provider_name": provider_name
        })

    pdf_buffer = report_service.generate_low_stock_pdf(products_data)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=alerta_bajo_stock.pdf"},
    )


@router.get("/deliveries")
async def export_deliveries_report(
    start_date: Optional[str] = Query(None, description="Fecha de inicio YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin YYYY-MM-DD"),
    delivery_user_id: Optional[int] = Query(None, description="ID del repartidor para filtrar"),
    status_filter: Optional[str] = Query(None, description="Estado del envío"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER])),
):
    from datetime import time
    from app.models.delivery import Delivery
    from sqlalchemy.orm import selectinload
    
    query = select(Delivery).options(selectinload(Delivery.delivery_user), selectinload(Delivery.provider)).order_by(Delivery.created_at.desc())
    
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.where(Delivery.created_at >= datetime.combine(sd, time.min))
        except ValueError:
            pass
            
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.where(Delivery.created_at <= datetime.combine(ed, time.max))
        except ValueError:
            pass
            
    if delivery_user_id is not None:
        query = query.where(Delivery.delivery_user_id == delivery_user_id)
        
    if status_filter:
        query = query.where(Delivery.status == status_filter)
        
    result = await db.execute(query)
    deliveries = result.scalars().all()
    
    # Calculate stats
    total_trips = len(deliveries)
    completed_trips = sum(1 for d in deliveries if d.status == "completed")
    pending_trips = sum(1 for d in deliveries if d.status in ("pending", "in_transit"))
    total_cost_usd = sum(d.cost_usd or 0.0 for d in deliveries)
    
    summary_stats = {
        "total_trips": total_trips,
        "completed_trips": completed_trips,
        "pending_trips": pending_trips,
        "total_cost_usd": total_cost_usd
    }
    
    # Format data for PDF
    import json as json_lib
    
    status_labels = {
        "pending": "Pendiente",
        "in_transit": "En Ruta",
        "completed": "Completado",
        "cancelled": "Cancelado"
    }
    
    deliveries_data = []
    for d in deliveries:
        created_str = d.created_at.strftime("%d/%m/%Y %H:%M") if d.created_at else "-"
        completed_str = d.completed_at.strftime("%d/%m/%Y %H:%M") if d.completed_at else "-"
        
        # Parse items_detail JSON into readable text: "Producto x Cantidad"
        items_text = "-"
        if d.items_detail:
            try:
                items_list = json_lib.loads(d.items_detail)
                if isinstance(items_list, list) and len(items_list) > 0:
                    items_text = ", ".join(
                        f"{item.get('name', 'Producto')} x{item.get('quantity', 1)}"
                        for item in items_list
                    )
                else:
                    items_text = d.items_detail
            except (json_lib.JSONDecodeError, TypeError):
                items_text = d.items_detail or "-"
        
        provider_name = d.provider.name if d.provider else "Sin Proveedor"
        repartidor_name = d.delivery_user.username if d.delivery_user else "Sin Asignar"
            
        deliveries_data.append({
            "id": d.id,
            "description": d.description,
            "address": d.address,
            "items_detail": items_text,
            "cost_usd": d.cost_usd or 0.0,
            "status": status_labels.get(d.status, d.status),
            "provider_name": provider_name,
            "delivery_user_name": repartidor_name,
            "created_at": created_str,
            "completed_at": completed_str
        })
        
    pdf_buffer = report_service.generate_deliveries_pdf(deliveries_data, summary_stats)
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=reporte_entregas.pdf"},
    )
