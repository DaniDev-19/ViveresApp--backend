from PIL import Image
from io import BytesIO
import os
import uuid
from fastapi import UploadFile

UPLOAD_DIR = "static/uploads"


class ImageService:
    def __init__(self):
        # Asegurar que directorio de subida existe
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    async def save_image(self, file: UploadFile, width: int = 800) -> str:
        """
        Optimiza y guarda una imagen como WebP.
        Redimensiona al ancho máximo manteniendo el aspecto.
        """
        try:
            contents = await file.read()
            image = Image.open(BytesIO(contents))

            # Convertir a RGB (en caso de RGBA/P palette)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Lógica de Redimensionado
            aspect_ratio = image.height / image.width
            new_height = int(width * aspect_ratio)
            image = image.resize((width, new_height), Image.Resampling.LANCZOS)

            # Generar nombre único
            filename = f"{uuid.uuid4()}.webp"
            file_path = os.path.join(UPLOAD_DIR, filename)

            # Guardar como WebP optimizado
            image.save(file_path, "WEBP", quality=80, optimize=True)

            # Retornar URL relativa (asumiendo que los estáticos se sirven correctamente)
            return f"/static/uploads/{filename}"

        except Exception as e:
            print(f"Error procesando imagen: {e}")
            return None


image_service = ImageService()
