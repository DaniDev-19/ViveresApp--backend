from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.image_service import image_service

router = APIRouter()


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):
    """
    Sube y optimiza una imagen a formato WebP.
    Retorna la URL relativa para ser guardada en la BD.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen válida.",
        )

    url = await image_service.save_image(file)

    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar la imagen.",
        )

    return {"url": url}
