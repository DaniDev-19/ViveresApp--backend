from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import io
import openpyxl
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.controllers.product_controller import ProductController
from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate, BulkPriceUpdate
from app.models.user import User, UserRole

router = APIRouter()

@router.post("/bulk-price-update")
async def bulk_price_update(
    bulk_in: BulkPriceUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER])),
):
    """
    Actualiza masivamente los precios (costo neto y precio final en cascada) por porcentaje.
    """
    return await ProductController.bulk_price_update(db, bulk_in=bulk_in, user_id=current_user.id)


@router.post("/import/parse", dependencies=[Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER]))])
async def parse_excel_for_import(
    file: UploadFile = File(...),
):
    """
    Lee un archivo Excel y devuelve un borrador de productos intentando mapear las columnas.
    Soporta archivos exportados del propio sistema y archivos externos con miles de columnas/filas.
    """
    import unicodedata

    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx, .xls)")

    contents = await file.read()
    try:
        # Usamos read_only=True para procesar archivos grandes en milisegundos sin saturar la RAM
        wb = openpyxl.load_workbook(filename=io.BytesIO(contents), data_only=True, read_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo el archivo Excel: {str(e)}")

    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append(row)

    wb.close()

    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="El archivo no tiene suficientes datos")

    def normalize_text(text: str) -> str:
        if not text:
            return ""
        text = str(text).strip().lower()
        # Eliminar tildes/acentos
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        return text

    # Buscar automáticamente la fila de cabeceras en las primeras 10 filas
    header_row_idx = -1
    headers = []
    
    keywords_header = ["codigo", "cod", "barcode", "producto", "nombre", "descripcion", "desc", "costo", "stock", "cant", "prec", "precio"]

    for r_i, row in enumerate(rows[:10]):
        row_normalized = [normalize_text(cell) for cell in row if cell is not None]
        matches = sum(1 for cell in row_normalized if any(kw in cell for kw in keywords_header))
        if matches >= 1:
            header_row_idx = r_i
            headers = [normalize_text(cell) for cell in row]
            break

    if header_row_idx == -1:
        header_row_idx = 0
        headers = [normalize_text(cell) for cell in rows[0]]

    # Limitar a las columnas reales con cabecera (ignorar columnas vacías fantasma al final)
    max_col_idx = 0
    for idx, h in enumerate(headers):
        if h:
            max_col_idx = idx
    max_cols = max_col_idx + 1
    headers = headers[:max_cols]

    # Helper para buscar indice de columna
    def find_col(possible_names):
        for i, h in enumerate(headers):
            for name in possible_names:
                if name in h:
                    return i
        return -1

    idx_barcode = find_col(["codigo", "cod", "bar", "ean", "clave", "sku"])
    idx_explicit_name = find_col(["nombre", "producto", "articulo", "item"])
    idx_location = find_col(["ubicacion", "ubic"])
    idx_raw_desc = find_col(["descripcion", "detalle", "observacion"])

    if idx_explicit_name != -1:
        idx_name = idx_explicit_name
    elif idx_raw_desc != -1:
        idx_name = idx_raw_desc
    else:
        idx_name = -1

    # Asignar la columna para la descripción (priorizar UBICACIÓN si existe)
    if idx_location != -1:
        idx_desc = idx_location
    elif idx_raw_desc != -1 and idx_raw_desc != idx_name:
        idx_desc = idx_raw_desc
    else:
        idx_desc = idx_raw_desc

    idx_cost = find_col(["costo", "compra", "cost", "prec", "precio"])
    idx_margin = find_col(["margen", "ganancia", "margin"])
    idx_tax = find_col(["iva", "impuesto", "tax"])
    idx_offer = find_col(["precio_oferta", "oferta", "offer", "p_oferta", "precio_oferta_usd"])
    idx_stock = find_col(["stock", "cant", "cantidad", "existencia"])
    idx_min_stock = find_col(["min", "alerta", "stock_minimo"])
    idx_category = find_col(["categoria", "cat"])
    idx_provider = find_col(["proveedor", "prov"])
    idx_public = find_col(["visible", "publico"])
    idx_iva_web = find_col(["iva_web", "aplica_iva_web"])

    data_rows = rows[header_row_idx + 1:]
    drafts = []
    
    for r_offset, row in enumerate(data_rows, start=header_row_idx + 2):
        # Truncar la fila solo a las columnas activas
        row = row[:max_cols]
        if not any(row):
            continue
            
        def clean_val(col_idx, default=""):
            if col_idx == -1 or col_idx >= len(row):
                return default
            val = row[col_idx]
            if val in (None, "", "None"):
                return default
            return str(val).strip()

        def clean_float(col_idx, default=0.0):
            if col_idx == -1 or col_idx >= len(row):
                return default
            val = row[col_idx]
            if val in (None, "", "None"):
                return default
            try:
                s_val = str(val).replace("$", "").replace("%", "").replace(",", ".").strip()
                return float(s_val)
            except:
                return default

        def clean_int(col_idx, default=0):
            if col_idx == -1 or col_idx >= len(row):
                return default
            val = row[col_idx]
            if val in (None, "", "None"):
                return default
            try:
                return int(float(str(val).replace(",", ".").strip()))
            except:
                return default

        def clean_bool(col_idx, default=True):
            if col_idx == -1 or col_idx >= len(row):
                return default
            val = row[col_idx]
            if val in (None, "", "None"):
                return default
            s_val = str(val).strip().lower()
            return s_val in ("si", "sí", "true", "1", "s", "v", "verdadero")

        barcode = clean_val(idx_barcode)
        name = clean_val(idx_name)
        description_val = clean_val(idx_desc)

        # Si no hay codigo ni nombre en esta fila, omitirla
        if not barcode and not name:
            continue

        cost = clean_float(idx_cost, 0.0)
        margin = clean_float(idx_margin, 0.30)
        if margin > 1.0:
            margin = margin / 100.0

        def clean_tax_rate(col_idx, cost_val):
            if col_idx == -1 or col_idx >= len(row):
                return 0.16
            val = row[col_idx]
            if val in (None, "", "None"):
                return 0.16
            s_val = str(val).strip().lower()
            if "exent" in s_val or s_val in ("0", "0%", "0.0", "no", "false"):
                return 0.0
            try:
                has_percent = "%" in s_val
                s_clean = s_val.replace("$", "").replace("%", "").replace(",", ".").strip()
                num = float(s_clean)
                if num == 0.0:
                    return 0.0

                # 1. Si la celda trae el símbolo '%' explícito (ej: "16%", "9%"):
                if has_percent:
                    return round(num / 100.0, 4) if num >= 1.0 else round(num, 4)

                # 2. Si hay costo > 0, chequear si num es el monto en $ del IVA (ej: 0.42 de IVA sobre costo de 2.61)
                if cost_val > 0:
                    calc_ratio = num / cost_val
                    # Probar si el ratio num/costo coincide con tasas estándar (16%, 12%, 9%, 8%, 5%)
                    standard_rates = [0.16, 0.12, 0.09, 0.08, 0.05]
                    for std in standard_rates:
                        if abs(calc_ratio - std) < 0.015:
                            return std

                # 3. Si num es un porcentaje directo sin costo o no coincidió con fórmula (ej: 16 -> 16%, 9 -> 9%, 0.16 -> 16%)
                if num == 0.16 or num == 16.0:
                    return 0.16
                if num == 0.09 or num == 9.0:
                    return 0.09
                if num == 0.12 or num == 12.0:
                    return 0.12
                if num == 0.08 or num == 8.0:
                    return 0.08

                if 0.0 < num < 1.0:
                    return round(num, 4)
                if 1.0 <= num <= 100.0:
                    return round(num / 100.0, 4)

                return 0.16
            except:
                return 0.16

        tax = clean_tax_rate(idx_tax, cost)

        offer_val = clean_float(idx_offer, -1.0)
        if idx_offer != -1 and offer_val >= 0:
            offer_price_usd = round(offer_val, 2)
        else:
            # Si no hay columna explícita de oferta, igualar al precio de costo (sin margen)
            offer_price_usd = round(cost, 2) if cost > 0 else 0.0

        draft = {
            "row_index": r_offset,
            "barcode": barcode,
            "name": name,
            "description": description_val,
            "cost_price": cost,
            "profit_margin": margin,
            "tax_rate": tax,
            "offer_price_usd": offer_price_usd,
            "stock_quantity": clean_int(idx_stock, 0),
            "min_stock_level": clean_int(idx_min_stock, 5),
            "category_id": clean_int(idx_category, None) if idx_category != -1 else None,
            "provider_id": clean_int(idx_provider, None) if idx_provider != -1 else None,
            "is_public": clean_bool(idx_public, True),
            "apply_iva_web": clean_bool(idx_iva_web, True),
        }
        drafts.append(draft)

    return {"headers": headers, "drafts": drafts}

@router.post("/import/bulk", dependencies=[Depends(deps.verify_roles([UserRole.ADMIN, UserRole.INVENTORY_MANAGER]))])
async def bulk_import_products(
    products_in: List[ProductCreate],
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Recibe un arreglo de productos validados y los registra o actualiza masivamente.
    Optimizado en batch (sin N+1 queries) para procesar miles de registros en ms.
    """
    from sqlalchemy import select
    from app.models.product import Product
    from app.controllers.product_controller import ProductController
    
    created = 0
    updated = 0
    errors = []

    if not products_in:
        return {"success": True, "created": 0, "updated": 0, "errors": []}

    # 1. Extraer todos los codigos de barra para consulta en bloque
    barcodes = [p.barcode for p in products_in if p.barcode]
    
    # 2. Consultar todos los productos existentes en un solo SELECT (IN)
    stmt = select(Product).where(Product.barcode.in_(barcodes))
    res = await db.execute(stmt)
    existing_map = {p.barcode: p for p in res.scalars().all()}

    # 3. Iterar y actualizar/crear en memoria
    for idx, p_in in enumerate(products_in):
        try:
            margin = p_in.profit_margin if p_in.profit_margin is not None else 0.30
            price_usd = ProductController._calc_price_usd(p_in.cost_price, margin)

            existing = existing_map.get(p_in.barcode)
            if existing:
                for field, value in p_in.model_dump(exclude_unset=True).items():
                    setattr(existing, field, value)
                existing.price_usd = price_usd
                updated += 1
            else:
                new_product = Product(**p_in.model_dump(), price_usd=price_usd)
                db.add(new_product)
                existing_map[p_in.barcode] = new_product
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


@router.get("/", response_model=List[ProductResponse], dependencies=[Depends(deps.verify_roles([UserRole.ADMIN, UserRole.WORKER, UserRole.INVENTORY_MANAGER]))])
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

