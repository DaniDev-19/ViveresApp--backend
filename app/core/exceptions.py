from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError


async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global para excepciones no controladas.
    Devuelve un error 500 genérico pero loguea el error real.
    """
    print(f"Error No Controlado: {exc}")  # Idealmente usar logger
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor. Por favor contacte al soporte."
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Manejador para errores de base de datos.
    """
    print(f"Error de Base de Datos: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error en la operación de base de datos."},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Manejador personalizado para errores de validación de Pydantic.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Datos de entrada inválidos."},
    )
