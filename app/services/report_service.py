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

    def generate_inventory_pdf(self, products_data: List[Dict[str, Any]]) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        elements.append(Paragraph(settings.BUSINESS_NAME.upper(), self._get_header_style()))
        elements.append(Paragraph(f"Reporte de Inventario General", self._get_sub_header_style()))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self._get_sub_header_style()))

        # REPLACED Category with Barcode
        headers = ["ID", "Código", "Producto", "Stock", "Precio", "Valor Total"]
        data = [headers]

        total_value = 0

        for prod in products_data:
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

        col_widths = [30, 90, 190, 60, 80, 80]
        
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
        elements.append(Spacer(1, 24))
        
        elements.append(Paragraph(f"Valor Total Inventario: ${total_value:.2f}", ParagraphStyle('Total', parent=getSampleStyleSheet()['Heading2'], alignment=TA_RIGHT, textColor=colors.HexColor('#065F46'))))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_inventory_excel(self, products_data: List[Dict[str, Any]]) -> BytesIO:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventario"

        ws.merge_cells('A1:H1')
        ws['A1'] = settings.BUSINESS_NAME.upper()
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = Alignment(horizontal="center")

        # REPLACED Category with Barcode
        headers = ["ID", "Código", "Producto", "Stock", "Costo", "Precio", "Margen", "Valor Total"]
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

        ws.column_dimensions['C'].width = 40 # Name

        for row_num, prod in enumerate(products_data, 3):
            val = prod.get("stock", 0) * prod.get("price", 0)
            ws.cell(row=row_num, column=1, value=prod.get("id"))
            ws.cell(row=row_num, column=2, value=prod.get("barcode", "N/A"))
            ws.cell(row=row_num, column=3, value=prod.get("name"))
            ws.cell(row=row_num, column=4, value=prod.get("stock"))
            
            ws.cell(row=row_num, column=5, value=prod.get("cost")).number_format = '"$"#,##0.00'
            ws.cell(row=row_num, column=6, value=prod.get("price")).number_format = '"$"#,##0.00'
            ws.cell(row=row_num, column=7, value=prod.get("margin"))
            
            ws.cell(row=row_num, column=8, value=val).number_format = '"$"#,##0.00'

            for i in range(1, 9):
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
            # 1. Product Name (Top) - Increased Y position
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.black)
            
            name = item.get("name", "")
            if len(name) > 25:
                # Two lines
                name_line1 = name[:25]
                name_line2 = name[25:50] + "..." if len(name) > 50 else name[25:]
                c.drawCentredString(x + col_width / 2, y + row_height - 25, name_line1)
                c.drawCentredString(x + col_width / 2, y + row_height - 38, name_line2)
            else:
                c.drawCentredString(x + col_width / 2, y + row_height - 30, name)
            
            # 2. Price (Middle/Center) - Adjusted Y position to be clearer
            # Using a very large font as requested, but ensuring no overlap
            c.setFont("Helvetica-Bold", 26)
            c.drawCentredString(x + col_width / 2, y + row_height / 2 - 10, f"${item.get('price', 0):.2f}")
            
            # 3. Footer (Bottom) - Moved closer to bottom
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

report_service = ReportService()
