import os
import uuid
import boto3
from PIL import Image
from io import BytesIO
from abc import ABC, abstractmethod
from fastapi import UploadFile
from app.core.config import settings

UPLOAD_DIR = "static/uploads"


class ImageStorageStrategy(ABC):
    @abstractmethod
    async def save(self, image: Image.Image, filename: str) -> str:
        pass

    @abstractmethod
    def delete(self, image_url: str):
        pass


class LocalStorageStrategy(ImageStorageStrategy):
    def __init__(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    async def save(self, image: Image.Image, filename: str) -> str:
        file_path = os.path.join(UPLOAD_DIR, filename)
        image.save(file_path, "WEBP", quality=80, optimize=True)
        return f"/static/uploads/{filename}"

    def delete(self, image_url: str):
        if not image_url or not image_url.startswith("/static/uploads/"):
            return
        filename = image_url.split("/")[-1]
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"LocalStorage: Archivo eliminado {file_path}")


class R2StorageStrategy(ImageStorageStrategy):
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY,
            aws_secret_access_key=settings.R2_SECRET_KEY,
            region_name="auto",  # R2 usa auto
        )
        self.bucket = settings.R2_BUCKET
        self.public_url = settings.R2_PUBLIC_URL.rstrip("/")

    async def save(self, image: Image.Image, filename: str) -> str:
        buffer = BytesIO()
        image.save(buffer, format="WEBP", quality=80, optimize=True)
        buffer.seek(0)

        self.s3.upload_fileobj(
            buffer,
            self.bucket,
            filename,
            ExtraArgs={"ContentType": "image/webp"}
        )
        return f"{self.public_url}/{filename}"

    def delete(self, image_url: str):
        if not image_url or self.public_url not in image_url:
            return
        filename = image_url.split("/")[-1]
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=filename)
            print(f"R2Storage: Archivo eliminado {filename}")
        except Exception as e:
            print(f"R2Storage: Error eliminando {filename}: {e}")


class ImageService:
    def __init__(self):
        if settings.STORAGE_MODE == "r2":
            self.strategy = R2StorageStrategy()
        else:
            self.strategy = LocalStorageStrategy()

    async def save_image(self, file: UploadFile, width: int = 800) -> str:
        try:
            contents = await file.read()
            image = Image.open(BytesIO(contents))

            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            aspect_ratio = image.height / image.width
            new_height = int(width * aspect_ratio)
            image = image.resize((width, new_height), Image.Resampling.LANCZOS)

            filename = f"{uuid.uuid4()}.webp"
            return await self.strategy.save(image, filename)

        except Exception as e:
            print(f"ImageService: Error procesando imagen: {e}")
            return None

    def delete_image(self, image_url: str):
        try:
            self.strategy.delete(image_url)
        except Exception as e:
            print(f"ImageService: Error eliminando imagen: {e}")


image_service = ImageService()
