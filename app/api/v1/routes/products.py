from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import io
import openpyxl
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.product_controller import ProductController
from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate
from app.models.user import User, UserRole

router = APIRouter()

@router.post("/import/parse")
async def parse_excel_for_import(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    """
    Lee un archivo Excel y devuelve un borrador de productos intentando mapear las columnas.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx, .xls)")

    contents = await file.read()
    try:
        wb = openpyxl.load_workbook(filename=io.BytesIO(contents), data_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo el archivo Excel: {str(e)}")

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="El archivo no tiene suficientes datos")

    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    
    # Heurística simple para encontrar columnas
    def find_col(possible_names):
        for i, h in enumerate(headers):
            for name in possible_names:
                if name in h:
                    return i
        return -1

    idx_barcode = find_col(["cód", "cod", "bar", "ean"])
    idx_name = find_col(["nombre", "producto", "desc"])
    idx_cost = find_col(["costo", "compra"])
    idx_margin = find_col(["margen", "ganancia"])
    idx_stock = find_col(["stock", "cant"])
    idx_min_stock = find_col(["min", "alerta"])
    
    drafts = []
    for r_idx, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue
            
        def clean_val(val, default=""):
            return str(val).strip() if val not in (None, "") else default

        def clean_float(val, default=0.0):
            try:
                return float(val) if val not in (None, "") else default
            except:
                return default

        def clean_int(val, default=0):
            try:
                return int(float(val)) if val not in (None, "") else default
            except:
                return default

        draft = {
            "row_index": r_idx,
            "barcode": clean_val(row[idx_barcode] if idx_barcode != -1 else ""),
            "name": clean_val(row[idx_name] if idx_name != -1 else ""),
            "cost_price": clean_float(row[idx_cost] if idx_cost != -1 else 0.0),
            "profit_margin": clean_float(row[idx_margin] if idx_margin != -1 else 0.30, 0.30),
            "stock_quantity": clean_int(row[idx_stock] if idx_stock != -1 else 0),
            "min_stock_level": clean_int(row[idx_min_stock] if idx_min_stock != -1 else 5, 5),
            "description": "",
        }
        
        # Eliminar 'None' explícito
        if draft["barcode"] == "None": draft["barcode"] = ""
        if draft["name"] == "None": draft["name"] = ""
        
        drafts.append(draft)
        
    return {"headers": headers, "drafts": drafts}

@router.post("/import/bulk")
async def bulk_import_products(
    products_in: List[ProductCreate],
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    """
    Recibe un arreglo de productos validados y los registra o actualiza masivamente.
    """
    from sqlalchemy import select
    from app.models.product import Product
    from app.controllers.product_controller import ProductController
    
    created = 0
    updated = 0
    errors = []

    for idx, p_in in enumerate(products_in):
        try:
            stmt = select(Product).where(Product.barcode == p_in.barcode)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            margin = p_in.profit_margin if p_in.profit_margin is not None else 0.30
            price_usd = ProductController._calc_price_usd(p_in.cost_price, margin)

            if existing:
                for field, value in p_in.model_dump(exclude_unset=True).items():
                    setattr(existing, field, value)
                existing.price_usd = price_usd
                updated += 1
            else:
                new_product = Product(**p_in.model_dump(), price_usd=price_usd)
                db.add(new_product)
                created += 1
        except Exception as e:
            errors.append(f"Código {p_in.barcode}: {str(e)}")
            
    await db.commit()
    return {
        "success": True,
        "created": created,
        "updated": updated,
        "errors": errors
    }


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    in_stock_only: bool = False,
    stock_eq: int | None = None,
    stock_lt: int | None = None,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER])),
):
    return await ProductController.get_multi(
        db,
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        provider_id=provider_id,
        in_stock_only=in_stock_only,
        stock_eq=stock_eq,
        stock_lt=stock_lt,
    )

@router.get("/public", response_model=List[ProductResponse])
async def get_public_products(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
):
    return await ProductController.get_multi(db, skip=skip, limit=limit, search=search, public_only=True)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    *,
    db: AsyncSession = Depends(deps.get_db),
    product_in: ProductCreate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    return await ProductController.create(db, product_in=product_in, user_id=current_user.id)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    *,
    db: AsyncSession = Depends(deps.get_db),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    product = await ProductController.update(db, product_id=product_id, product_in=product_in, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.delete("/{product_id}")
async def delete_product(
    *,
    db: AsyncSession = Depends(deps.get_db),
    product_id: int,
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN])),
):
    product = await ProductController.delete(db, product_id=product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado", "id": product_id}

