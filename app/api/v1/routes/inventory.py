from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.api.deps import get_db, get_current_user
from app.controllers.inventory_controller import InventoryController
from app.schemas.inventory import InventoryAdjustmentCreate

router = APIRouter()


@router.get("/movements")
async def get_inventory_movements(
    product_id: Optional[int] = Query(None, description="Filtrar por ID de producto"),
    product_search: Optional[str] = Query(None, description="Buscar por nombre o código de barra"),
    movement_type: Optional[str] = Query(None, description="sale | purchase | return | exchange_in | exchange_out | adjustment"),
    date_from: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retorna el listado unificado de movimientos de inventario de la tabla física.
    """
    return await InventoryController.get_movements(
        db,
        product_id=product_id,
        product_search=product_search,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )


@router.get("/movements/summary")
async def get_inventory_summary(
    product_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retorna los totales de entradas, salidas y variaciones de inventario.
    """
    return await InventoryController.get_summary(
        db,
        product_id=product_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/adjust")
async def adjust_inventory_stock(
    adjustment: InventoryAdjustmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Realiza un ajuste manual al inventario físico de un producto (+/- unidades).
    """
    product = await InventoryController.adjust_stock(
        db=db,
        product_id=adjustment.product_id,
        quantity_change=adjustment.quantity_change,
        notes=adjustment.notes,
        user_id=current_user.id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado."
        )
    return {"message": "Ajuste de inventario realizado con éxito.", "product_id": product.id, "new_stock": product.stock_quantity}


@router.get("/movements/export")
async def export_inventory_movements(
    product_id: Optional[int] = Query(None),
    product_search: Optional[str] = Query(None),
    movement_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    format: str = Query("pdf", enum=["pdf", "excel"]),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Exporta el Kardex / movimientos de inventario en formato PDF o Excel.
    """
    from app.services.report_service import report_service
    from fastapi import Response

    res = await InventoryController.get_movements(
        db,
        product_id=product_id,
        product_search=product_search,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        skip=0,
        limit=10000,
    )
    movements_list = res.get("movements", [])

    date_range_str = f"{date_from or 'Inicio'} - {date_to or 'Hoy'}"

    if format == "pdf":
        buffer = report_service.generate_movements_pdf(movements_list, date_range_str)
        media_type = "application/pdf"
        filename = f"Kardex_Inventario_{date.today()}.pdf"
        content_disposition = f"inline; filename={filename}"
    else:
        buffer = report_service.generate_movements_excel(movements_list)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"Kardex_Inventario_{date.today()}.xlsx"
        content_disposition = f"attachment; filename={filename}"

    return Response(
        content=buffer.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": content_disposition}
    )

