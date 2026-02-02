from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.currency import currency_service

router = APIRouter()


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_rates(db: AsyncSession = Depends(get_db)):
    """
    Fuerza la actualización de las tasas de cambio desde APIs externas.
    Retorna las nuevas tasas obtenidas.
    """
    try:
        rates = await currency_service.update_rates(db)
        return rates
    except Exception as e:
        print(f"Error actualizando tasas: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error al conectar con servicios de cambio externos.",
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_rates(db: AsyncSession = Depends(get_db)):
    """
    Obtiene las últimas tasas de cambio registradas en la base de datos.
    """
    try:
        return await currency_service.get_latest_rates(db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener historial de tasas.",
        )
