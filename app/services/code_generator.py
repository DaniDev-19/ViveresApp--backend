import barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO


class CodeService:
    def generate_barcode(self, code_data: str):
        """Generates EAN13 barcode image"""
        try:
            # EAN13 requires 12 digits + checksum.
            # For simplicity, we assume code_data is valid or use Code128 for flexibility
            EAN = barcode.get_barcode_class("code128")
            my_ean = EAN(code_data, writer=ImageWriter())
            buffer = BytesIO()
            my_ean.write(buffer)
            buffer.seek(0)
            return buffer
        except Exception as e:
            print(f"Error generating barcode: {e}")
            return None

    def generate_qr(self, data: str):
        """Generates QR Code image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer


code_service = CodeService()
