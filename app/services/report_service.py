from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import List, Dict, Any
from io import BytesIO
from datetime import datetime
from app.core.config import settings

class ReportService:
    def _get_header_style(self):
        return ParagraphStyle(
            'Header',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4F46E5'), # Indigo 600
            alignment=TA_CENTER,
            spaceAfter=20
        )

    def _get_sub_header_style(self):
         return ParagraphStyle(
            'SubHeader',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=30
        )

    def generate_sales_pdf(self, sales_data: List[Dict[str, Any]], date_range: str) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
        elements = []
        
        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        elements.append(Paragraph(f"Reporte de Ventas Detallado", self._get_sub_header_style()))
        elements.append(Paragraph(f"Periodo: {date_range} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))

        # Columns: ID, Fecha, Cliente, Deliv, IVA, Ganancia, Total BS, Total USD
        headers = ["ID", "Fecha", "Cliente", "Deliv.", "IVA", "Ganancia", "Total (BS)", "Total ($)"]
        data = [headers]
        
        # Totals
        sum_delivery = 0
        sum_tax = 0
        sum_profit = 0
        sum_bs = 0
        sum_usd = 0

        for sale in sales_data:
            d = sale.get("delivery", 0)
            t = sale.get("tax", 0)
            p = sale.get("profit", 0)
            bs = sale.get("total_bs", 0)
            usd = sale.get("total", 0)

            data.append([
                str(sale.get("id", "")),
                sale.get("date", ""),
                sale.get("customer", "Cliente Casual")[:15],
                f"${d:.2f}",
                f"${t:.2f}",
                f"${p:.2f}",
                f"{bs:,.2f}",
                f"${usd:.2f}",
            ])
            
            sum_delivery += d
            sum_tax += t
            sum_profit += p
            sum_bs += bs
            sum_usd += usd

        # Summary Row
        data.append([
            "TOTALES", "", "",
            f"${sum_delivery:.2f}",
            f"${sum_tax:.2f}",
            f"${sum_profit:.2f}",
            f"{sum_bs:,.2f}",
            f"${sum_usd:.2f}"
        ])

        col_widths = [30, 80, 110, 50, 50, 60, 90, 80]

        t = Table(data, colWidths=col_widths)
        
        # Styles
        styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#F3F4F6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')), # Extended to -1 (footer)
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F9FAFB')]),
            
            # Footer Style (Last Row)
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E0E7FF')), # Light Indigo
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('ALIGN', (0, -1), (0, -1), 'RIGHT'), # Align "TOTALES" to right of the spanned cell
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
            ('SPAN', (0, -1), (2, -1)), # Merge first 3 cols for "TOTALES" label (UPPERCASE)
        ]
        
        t.setStyle(TableStyle(styles))
        elements.append(t)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_sales_excel(self, sales_data: List[Dict[str, Any]]) -> BytesIO:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Ventas"

        ws.merge_cells('A1:K1')
        ws['A1'] = settings.BUSINESS_NAME.upper()
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = Alignment(horizontal="center")
        
        headers = ["ID", "Fecha", "Cliente", "Cajero", "Items", "Delivery", "IVA", "Ganancia", "Total (BS)", "Total (USD)", "Estado"]
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=2, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = 15

        ws.column_dimensions['E'].width = 40 
        ws.column_dimensions['C'].width = 25

        last_row = 3
        for row_num, sale in enumerate(sales_data, 3):
            try:
                ws.cell(row=row_num, column=1, value=sale.get("id"))
                ws.cell(row=row_num, column=2, value=str(sale.get("date")))
                ws.cell(row=row_num, column=3, value=str(sale.get("customer", "")))
                ws.cell(row=row_num, column=4, value=str(sale.get("cashier", "")))
                ws.cell(row=row_num, column=5, value=str(sale.get("items", "")))
                
                # Numeric fields
                ws.cell(row=row_num, column=6, value=sale.get("delivery", 0)).number_format = '"$"#,##0.00'
                ws.cell(row=row_num, column=7, value=sale.get("tax", 0)).number_format = '"$"#,##0.00'
                ws.cell(row=row_num, column=8, value=sale.get("profit", 0)).number_format = '"$"#,##0.00'
                ws.cell(row=row_num, column=9, value=sale.get("total_bs", 0)).number_format = '#,##0.00'
                ws.cell(row=row_num, column=10, value=sale.get("total", 0)).number_format = '"$"#,##0.00'
                
                ws.cell(row=row_num, column=11, value=str(sale.get("status", "")))

                for i in range(1, 12):
                    ws.cell(row=row_num, column=i).border = border
                
                last_row = row_num
            except Exception as e:
                print(f"Error processing row {row_num}: {e}")
                continue
        
        # Totals Row
        total_row = last_row + 1
        ws.cell(row=total_row, column=1, value="TOTALES").font = Font(bold=True)
        # Sum Delivery (F) to Total USD (J)
        cols_to_sum = ['F', 'G', 'H', 'I', 'J']
        
        for col in cols_to_sum:
            cell = ws.cell(row=total_row, column=openpyxl.utils.column_index_from_string(col))
            cell.value = f"=SUM({col}3:{col}{last_row})"
            cell.font = Font(bold=True)
            if col == 'I':
                cell.number_format = '#,##0.00'
            else:
                cell.number_format = '"$"#,##0.00'

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    def generate_inventory_pdf(self, products_data: List[Dict[str, Any]], report_type: str = "standard") -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        
        if report_type == "code_name":
            title_text = "Reporte de Catálogo (Código y Nombre)"
            headers = ["Código", "Producto"]
            col_widths = [150, 402]
        elif report_type == "prices":
            title_text = "Reporte de Precios de Productos"
            headers = ["Código", "Producto", "Precio Oferta", "Precio Final"]
            col_widths = [120, 252, 90, 90]
        else:
            title_text = "Reporte de Inventario General"
            headers = ["ID", "Código", "Producto", "Stock", "Precio", "Valor Total"]
            col_widths = [30, 90, 190, 60, 80, 80]

        elements.append(Paragraph(title_text, self._get_sub_header_style()))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))

        data = [headers]
        total_value = 0

        for prod in products_data:
            if report_type == "code_name":
                data.append([
                    prod.get("barcode", "N/A"),
                    prod.get("name", "Producto")[:50]
                ])
            elif report_type == "prices":
                off_price = prod.get("offer_price", 0.0)
                off_price_str = f"${off_price:.2f}" if off_price > 0 else "-"
                data.append([
                    prod.get("barcode", "N/A"),
                    prod.get("name", "Producto")[:35],
                    off_price_str,
                    f"${prod.get('price', 0):.2f}"
                ])
            else:
                val = prod.get("stock", 0) * prod.get("price", 0)
                data.append([
                    str(prod.get("id", "")),
                    prod.get("barcode", "N/A")[:15],
                    prod.get("name", "Producto")[:30],
                    str(prod.get("stock", 0)),
                    f"${prod.get('price', 0):.2f}",
                    f"${val:.2f}"
                ])
                total_value += val

        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECFDF5')]),
        ]))
        elements.append(t)
        
        if report_type == "standard":
            elements.append(Spacer(1, 24))
            elements.append(Paragraph(f"Valor Total Inventario: ${total_value:.2f}", ParagraphStyle('Total', parent=getSampleStyleSheet()['Heading2'], alignment=TA_RIGHT, textColor=colors.HexColor('#065F46'))))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_inventory_excel(self, products_data: List[Dict[str, Any]], report_type: str = "standard") -> BytesIO:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventario"

        if report_type == "code_name":
            headers = ["Código", "Producto"]
            max_col = 2
        elif report_type == "prices":
            headers = ["Código", "Producto", "Precio Oferta", "Precio Final"]
            max_col = 4
        else:
            headers = ["ID", "Código", "Producto", "Stock", "Costo", "Precio", "Margen", "Valor Total"]
            max_col = 8

        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col)
        ws.cell(row=1, column=1, value=settings.BUSINESS_NAME.upper())
        ws.cell(row=1, column=1).font = Font(bold=True, size=16)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")

        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=2, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = 15

        if report_type in ["code_name", "prices"]:
            ws.column_dimensions['B'].width = 40  # Name
        else:
            ws.column_dimensions['C'].width = 40  # Name

        for row_num, prod in enumerate(products_data, 3):
            if report_type == "code_name":
                ws.cell(row=row_num, column=1, value=prod.get("barcode", "N/A"))
                ws.cell(row=row_num, column=2, value=prod.get("name"))
            elif report_type == "prices":
                off_price = prod.get("offer_price", 0.0)
                ws.cell(row=row_num, column=1, value=prod.get("barcode", "N/A"))
                ws.cell(row=row_num, column=2, value=prod.get("name"))
                ws.cell(row=row_num, column=3, value=off_price if off_price > 0 else "-").number_format = '"$"#,##0.00' if off_price > 0 else '@'
                ws.cell(row=row_num, column=4, value=prod.get("price")).number_format = '"$"#,##0.00'
            else:
                val = prod.get("stock", 0) * prod.get("price", 0)
                ws.cell(row=row_num, column=1, value=prod.get("id"))
                ws.cell(row=row_num, column=2, value=prod.get("barcode", "N/A"))
                ws.cell(row=row_num, column=3, value=prod.get("name"))
                ws.cell(row=row_num, column=4, value=prod.get("stock"))
                ws.cell(row=row_num, column=5, value=prod.get("cost")).number_format = '"$"#,##0.00'
                ws.cell(row=row_num, column=6, value=prod.get("price")).number_format = '"$"#,##0.00'
                ws.cell(row=row_num, column=7, value=prod.get("margin"))
                ws.cell(row=row_num, column=8, value=val).number_format = '"$"#,##0.00'

            for i in range(1, max_col + 1):
                ws.cell(row=row_num, column=i).border = border

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    def generate_labels_pdf(self, products_to_print: List[Dict[str, Any]]) -> BytesIO:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        cols = 3
        rows = 8
        margin_x = 20
        margin_y = 20
        
        col_width = (width - 2 * margin_x) / cols
        row_height = (height - 2 * margin_y) / rows
        
        x_idx = 0
        y_idx = 0

        name_style = ParagraphStyle(
            'LabelProductName',
            parent=getSampleStyleSheet()['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.black
        )

        for item in products_to_print:
            x = margin_x + x_idx * col_width
            y = height - margin_y - (y_idx + 1) * row_height
            
            # Border
            c.setStrokeColor(colors.lightgrey)
            c.setDash(1, 2)
            c.rect(x + 5, y + 5, col_width - 10, row_height - 10)
            c.setDash([])
            c.setStrokeColor(colors.black)

            # Content
            # 1. Product Name (Top) - Wrapped using Paragraph to support multi-line wrap cleanly
            name = item.get("name", "")
            if len(name) > 60:
                name = name[:57] + "..."

            p = Paragraph(name, name_style)
            p_width, p_height = p.wrap(col_width - 20, row_height - 30)
            
            # Draw name at the top inside cell margins
            p.drawOn(c, x + 10, y + row_height - p_height - 10)
            
            # 2. Price (Dynamic position based on remaining space to prevent overlap)
            # Center of the remaining space between the bottom of name and top of business footer (y + 20)
            remaining_top = row_height - p_height - 10
            price_y_offset = (remaining_top + 20) / 2
            
            c.setFont("Helvetica-Bold", 26)
            c.drawCentredString(x + col_width / 2, y + price_y_offset - 10, f"${item.get('price', 0):.2f}")
            
            # 3. Footer (Bottom)
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.HexColor('#4F46E5'))
            c.drawCentredString(x + col_width / 2, y + 15, settings.BUSINESS_NAME.upper())

            x_idx += 1
            if x_idx >= cols:
                x_idx = 0
                y_idx += 1
                if y_idx >= rows:
                    c.showPage()
                    y_idx = 0
                    
        c.save()
        buffer.seek(0)
        return buffer
        
    def generate_monthly_growth_pdf(self, monthly_data: List[Dict[str, Any]], year: int) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        elements.append(Paragraph(f"Reporte de Crecimiento y Ganancia Mensual - Año {year}", self._get_sub_header_style()))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))
        elements.append(Spacer(1, 15))
        
        headers = ["Mes", "Ventas USD", "Ganancia USD", "Ventas BCV", "Ganancia BCV", "Ventas USDT", "Ganancia USDT"]
        rows = []
        
        total_sales_usd = 0.0
        total_profit_usd = 0.0
        
        for m in monthly_data:
            rows.append([
                m.get("month_name", ""),
                f"${m.get('total_usd', 0.0):,.2f}",
                f"${m.get('profit_usd', 0.0):,.2f}",
                f"Bs. {m.get('total_bs_bcv', 0.0):,.2f}",
                f"Bs. {m.get('profit_bs_bcv', 0.0):,.2f}",
                f"Bs. {m.get('total_bs_usdt', 0.0):,.2f}",
                f"Bs. {m.get('profit_bs_usdt', 0.0):,.2f}",
            ])
            total_sales_usd += m.get('total_usd', 0.0)
            total_profit_usd += m.get('profit_usd', 0.0)
            
        total_sales_bs_bcv = sum(m.get('total_bs_bcv', 0.0) for m in monthly_data)
        total_profit_bs_bcv = sum(m.get('profit_bs_bcv', 0.0) for m in monthly_data)
        total_sales_bs_usdt = sum(m.get('total_bs_usdt', 0.0) for m in monthly_data)
        total_profit_bs_usdt = sum(m.get('profit_bs_usdt', 0.0) for m in monthly_data)
        
        rows.append([
            "TOTAL ANUAL",
            f"${total_sales_usd:,.2f}",
            f"${total_profit_usd:,.2f}",
            f"Bs. {total_sales_bs_bcv:,.2f}",
            f"Bs. {total_profit_bs_bcv:,.2f}",
            f"Bs. {total_sales_bs_usdt:,.2f}",
            f"Bs. {total_profit_bs_usdt:,.2f}",
        ])
        
        col_widths = [72, 75, 75, 85, 85, 80, 80]
        
        t = Table([headers] + rows, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F9FAFB')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EEF2F6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 8),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
        ]))
        
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_rankings_pdf(self, rankings_data: Dict[str, Any], date_range: str) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        elements.append(Paragraph("Reporte de Rankings y Rendimiento", self._get_sub_header_style()))
        elements.append(Paragraph(f"Periodo: {date_range} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4F46E5'),
            spaceBefore=15,
            spaceAfter=8,
            keepWithNext=True
        )
        
        def make_table(headers, rows, col_widths, bg_color):
            table_data = [headers] + rows
            t = Table(table_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(bg_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
            ]))
            return t

        # 1. Líderes de Ventas
        elements.append(Paragraph("Líderes de Ventas (Usuarios / Cajeros)", section_style))
        users_headers = ["ID", "Usuario", "Transacciones", "Total Generado ($)"]
        users_rows = [
            [str(u.get("id", "")), u.get("username", ""), str(u.get("transactions", 0)), f"${u.get('total_amount', 0.0):,.2f}"]
            for u in rankings_data.get("top_users", [])
        ]
        if not users_rows:
            users_rows = [["-", "No hay datos", "-", "-"]]
        elements.append(make_table(users_headers, users_rows, [50, 150, 150, 202], '#4F46E5'))
        elements.append(Spacer(1, 15))

        # 2. Productos Más Vendidos
        elements.append(Paragraph("Top 10 Productos Más Vendidos (Unidades)", section_style))
        prod_headers = ["ID Producto", "Nombre del Producto", "Unidades Vendidas"]
        prod_rows = [
            [str(p.get("id", "")), p.get("name", ""), f"{p.get('value', 0):,.0f} uds"]
            for p in rankings_data.get("top_products", [])
        ]
        if not prod_rows:
            prod_rows = [["-", "No hay datos", "-"]]
        elements.append(make_table(prod_headers, prod_rows, [80, 322, 150], '#10B981'))
        elements.append(Spacer(1, 15))

        # 3. Productos de Baja Rotación
        elements.append(Paragraph("Productos de Baja Rotación (Menos Vendidos)", section_style))
        low_prod_headers = ["ID Producto", "Nombre del Producto", "Unidades Vendidas"]
        low_prod_rows = [
            [str(p.get("id", "")), p.get("name", ""), f"{p.get('value', 0):,.0f} uds"]
            for p in rankings_data.get("low_products", [])
        ]
        if not low_prod_rows:
            low_prod_rows = [["-", "No hay datos", "-"]]
        elements.append(make_table(low_prod_headers, low_prod_rows, [80, 322, 150], '#EF4444'))
        elements.append(Spacer(1, 15))

        # 4. Mejores Clientes
        elements.append(Paragraph("Ranking de Mejores Clientes (Mayor Compra)", section_style))
        cust_headers = ["ID Cliente", "Nombre", "Total Pedidos", "Total Gastado ($)"]
        cust_rows = [
            [str(c.get("id", "")), c.get("name", ""), str(c.get("orders", 0)), f"${c.get('amount', 0.0):,.2f}"]
            for c in rankings_data.get("top_customers", [])
        ]
        if not cust_rows:
            cust_rows = [["-", "No hay datos", "-", "-"]]
        elements.append(make_table(cust_headers, cust_rows, [80, 222, 100, 150], '#F59E0B'))
        elements.append(Spacer(1, 15))

        # 5. Desempeño de Proveedores
        elements.append(Paragraph("Desempeño de Proveedores", section_style))
        prov_headers = ["Proveedor", "Órdenes Totales", "Órdenes Completadas", "Fiabilidad"]
        prov_rows = [
            [p.get("name", ""), str(p.get("total_orders", 0)), str(p.get("completed_orders", 0)), f"{p.get('reliability', 0.0):.1f}%"]
            for p in rankings_data.get("top_providers", [])
        ]
        if not prov_rows:
            prov_rows = [["-", "No hay datos", "-", "-"]]
        elements.append(make_table(prov_headers, prov_rows, [222, 100, 130, 100], '#8B5CF6'))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_cash_close_pdf(self, cash_data: Dict[str, Any], date_str: str) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        # Header
        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        elements.append(Paragraph("Reporte de Arqueo y Cierre de Caja", self._get_sub_header_style()))
        elements.append(Paragraph(f"Fecha de Cierre: {date_str} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))
        elements.append(Spacer(1, 15))

        section_style = ParagraphStyle(
            'SectionHeaderClose',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        )

        # 1. Resumen General
        elements.append(Paragraph("1. Resumen General de Operaciones", section_style))
        
        metrics_headers = ["Transacciones", "Facturación Total ($)", "Total IVA ($)", "Ganancia Neta ($)"]
        metrics_row = [
            str(cash_data.get("total_sales_count", 0)),
            f"${cash_data.get('total_revenue_usd', 0.0):,.2f}",
            f"${cash_data.get('total_tax_usd', 0.0):,.2f}",
            f"${cash_data.get('total_profit_usd', 0.0):,.2f}",
        ]
        
        t_metrics = Table([metrics_headers, metrics_row], colWidths=[130, 130, 130, 130])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8FAFC')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#10B981')),
        ]))
        
        elements.append(t_metrics)
        elements.append(Spacer(1, 20))

        # 2. Desglose por Método de Pago
        elements.append(Paragraph("2. Desglose de Ventas por Método de Pago", section_style))
        
        pm_headers = ["Método de Pago", "Cant. Operaciones", "Monto Recaudado", "Monto en USD Eq."]
        pm_rows = []
        for pm in cash_data.get("payment_breakdown", []):
            cur = pm.get("currency", "USD")
            sym = "Bs. " if cur == "VES" else "$"
            pm_rows.append([
                pm.get("name", ""),
                str(pm.get("count", 0)),
                f"{sym}{pm.get('amount', 0.0):,.2f}",
                f"${pm.get('amount_usd', 0.0):,.2f}"
            ])
            
        if not pm_rows:
            pm_rows.append(["Sin transacciones en la fecha", "-", "-", "-"])

        t_pm = Table([pm_headers] + pm_rows, colWidths=[180, 100, 120, 120])
        t_pm.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(t_pm)
        elements.append(Spacer(1, 25))

        # 3. Conciliación y Firmas
        elements.append(Paragraph("3. Control de Auditoría y Conciliación", section_style))
        
        audit_text = (
            "Este reporte resume el arqueo de los fondos digitales y en efectivo recibidos durante la jornada laboral. "
            "El cajero y el supervisor de la tienda deben firmar a continuación para dar conformidad al cuadre físico realizado contra los totales sugeridos por este sistema."
        )
        elements.append(Paragraph(audit_text, ParagraphStyle('AuditStyle', parent=getSampleStyleSheet()['Normal'], fontSize=9, textColor=colors.HexColor('#6B7280'), spaceAfter=50)))
        
        # Signatures
        sig_data = [
            ["_____________________________________", "_____________________________________"],
            ["Firma Cajero", "Firma Supervisor / Administrador"],
            ["Nombre:", "Nombre:"]
        ]
        t_sig = Table(sig_data, colWidths=[260, 260])
        t_sig.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
        ]))
        elements.append(t_sig)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_low_stock_pdf(self, products_data: List[Dict[str, Any]]) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
        elements = []

        # Header
        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        elements.append(Paragraph("Reporte de Alerta de Stock y Sugerencia de Reposición", self._get_sub_header_style()))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))
        elements.append(Spacer(1, 15))

        # Summary Metrics
        total_items_low = len(products_data)
        total_investment = sum(p["total_cost_usd"] for p in products_data)
        
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1E293B')
        )
        
        summary_text = (
            f"<b>Resumen de Alertas:</b> Se encontraron <b>{total_items_low}</b> productos con stock crítico (bajo o igual al nivel mínimo de seguridad). "
            f"La inversión total estimada para el reabastecimiento sugerido es de <b>${total_investment:,.2f} USD</b>."
        )
        elements.append(Paragraph(summary_text, summary_style))
        elements.append(Spacer(1, 15))

        # Table Headers
        headers = ["Código de Barra", "Nombre del Producto", "Stock Act.", "Stock Mín.", "Sugerido", "Costo U. ($)", "Total Est. ($)", "Proveedor Sugerido"]
        
        rows = []
        for p in products_data:
            rows.append([
                p.get("barcode", ""),
                p.get("name", ""),
                f"{p.get('stock', 0)}",
                f"{p.get('min_stock', 0)}",
                f"+{p.get('suggested_refill', 0)}",
                f"${p.get('cost_usd', 0.0):,.2f}",
                f"${p.get('total_cost_usd', 0.0):,.2f}",
                p.get("provider_name", "Sin Proveedor")
            ])

        col_widths = [100, 200, 60, 60, 60, 80, 80, 130]
        
        t = Table([headers] + rows, colWidths=col_widths)
        
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
        ]
        
        for i, p in enumerate(products_data):
            if p.get("stock", 0) == 0:
                t_style.append(('BACKGROUND', (0, i + 1), (-1, i + 1), colors.HexColor('#FEE2E2')))
            else:
                bg = colors.white if i % 2 == 0 else colors.HexColor('#F9FAFB')
                t_style.append(('BACKGROUND', (0, i + 1), (-1, i + 1), bg))
                
        t.setStyle(TableStyle(t_style))
        elements.append(t)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_deliveries_pdf(self, deliveries_data: List[Dict[str, Any]], summary_stats: Dict[str, Any]) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        elements.append(Paragraph("Reporte de Control de Envíos y Diligencias (Delivery)", self._get_sub_header_style()))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))
        elements.append(Spacer(1, 15))

        section_style = ParagraphStyle(
            'SectionHeaderDeliv',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        )

        elements.append(Paragraph("1. Resumen de Gastos Operativos de Delivery", section_style))
        
        metrics_headers = ["Viajes Totales", "Viajes Completados", "Viajes Pendientes / En Ruta", "Inversión Operativa Total ($)"]
        metrics_row = [
            str(summary_stats.get("total_trips", 0)),
            str(summary_stats.get("completed_trips", 0)),
            str(summary_stats.get("pending_trips", 0)),
            f"${summary_stats.get('total_cost_usd', 0.0):,.2f}",
        ]
        
        t_metrics = Table([metrics_headers, metrics_row], colWidths=[180, 180, 180, 180])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8FAFC')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#4F46E5')),
        ]))
        
        elements.append(t_metrics)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("2. Detalle de Viajes y Carreras", section_style))

        detail_headers = ["Descripción", "Destino", "Productos", "Proveedor", "Repartidor", "Costo ($)", "Estado", "Registro", "Entrega"]

        cell_style = ParagraphStyle(
            'CellStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName='Helvetica',
            fontSize=7,
            leading=9,
            wordWrap='CJK',
        )

        rows = []
        for d in deliveries_data:
            rows.append([
                Paragraph(str(d.get("description", "")), cell_style),
                Paragraph(str(d.get("address", "") or "-"), cell_style),
                Paragraph(str(d.get("items_detail", "") or "-"), cell_style),
                Paragraph(str(d.get("provider_name", "Sin Proveedor")), cell_style),
                Paragraph(str(d.get("delivery_user_name", "") or "Sin Asignar"), cell_style),
                f"${d.get('cost_usd', 0.0):,.2f}",
                d.get("status", ""),
                d.get("created_at", "") or "-",
                d.get("completed_at", "") or "-"
            ])
            
        if not rows:
            rows.append(["-", "No se encontraron envíos o viajes en el período", "-", "-", "-", "-", "-", "-", "-"])

        col_widths = [90, 80, 120, 75, 75, 50, 58, 80, 80]
        
        t = Table([detail_headers] + rows, colWidths=col_widths, repeatRows=1)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (5, 1), (8, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
        ]
        
        for i, d in enumerate(deliveries_data):
            st = d.get("status", "")
            if st == "Completado":
                bg = colors.HexColor('#ECFDF5')
            elif st == "Cancelado":
                bg = colors.HexColor('#FEF2F2')
            else:
                bg = colors.white if i % 2 == 0 else colors.HexColor('#F8FAFC')
            t_style.append(('BACKGROUND', (0, i + 1), (-1, i + 1), bg))
            
        t.setStyle(TableStyle(t_style))
        elements.append(t)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

report_service = ReportService()
