from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO


class PDFService:
    def generate_invoice(
        self,
        sale_data: dict,
        include_rif: bool = False,
        include_signature: bool = False,
    ):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Header
        elements.append(Paragraph("ViveresApp - Factura", styles["Title"]))
        elements.append(Spacer(1, 12))

        # Metadata
        if include_rif:
            elements.append(Paragraph("RIF: J-00000000-0", styles["Normal"]))

        elements.append(
            Paragraph(f"Fecha: {sale_data.get('created_at', 'N/A')}", styles["Normal"])
        )
        elements.append(Spacer(1, 12))

        # Items Table
        data = [["Producto", "Cant", "Precio Unit", "Total"]]
        for item in sale_data.get("items", []):
            data.append(
                [
                    item.get("product_name", "Item"),
                    str(item.get("quantity", 0)),
                    f"${item.get('price', 0):.2f}",
                    f"${item.get('total', 0):.2f}",
                ]
            )

        t = Table(data)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(t)
        elements.append(Spacer(1, 24))

        # Totals
        elements.append(
            Paragraph(
                f"Total USD: ${sale_data.get('total_usd', 0):.2f}", styles["Heading2"]
            )
        )

        if sale_data.get("has_delivery"):
            elements.append(
                Paragraph(
                    f"Delivery: ${sale_data.get('delivery_amount', 0):.2f}",
                    styles["Normal"],
                )
            )

        elements.append(Spacer(1, 40))

        # Signature
        if include_signature:
            elements.append(Paragraph("__________________________", styles["Normal"]))
            elements.append(Paragraph("Firma Autorizada", styles["Normal"]))

        doc.build(elements)
        buffer.seek(0)
        return buffer


pdf_service = PDFService()
