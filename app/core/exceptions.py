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
    Extrae mensajes personalizados de validadores y los retorna de manera amigable.
    """
    errors = exc.errors()
    
    # Intentar extraer el primer mensaje de error personalizado
    if errors and len(errors) > 0:
        first_error = errors[0]
        
        # Caso especial: customer_id es null o falta
        if first_error.get('loc') == ('body', 'customer_id'):
            error_type = first_error.get('type', '')
            # Si el error es por campo faltante o null
            if error_type in ['missing', 'int_parsing', 'int_type']:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Debe seleccionar un cliente para realizar la venta"},
                )
        
        # Si el error tiene un mensaje personalizado (de un validador), usarlo
        if 'msg' in first_error:
            error_msg = first_error['msg']
            # Si es un ValueError de nuestro validador, extraer el mensaje
            if 'Value error,' in error_msg:
                error_msg = error_msg.replace('Value error, ', '')
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": error_msg},
            )
    
    # Fallback al comportamiento por defecto
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors, "message": "Datos de entrada inválidos."},
    )
