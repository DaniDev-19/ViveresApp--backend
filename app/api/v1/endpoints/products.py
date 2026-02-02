from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.audit_service import AuditService
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
async def read_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    public_only: bool = False,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve products with filtering.
    """
    query = select(Product)

    if search:
        search_filter = or_(
            Product.name.ilike(f"%{search}%"), Product.barcode.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    if category_id:
        query = query.where(Product.category_id == category_id)

    if public_only:
        query = query.where(Product.is_public)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ProductResponse)
async def create_product(
    *,
    db: AsyncSession = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new product.
    """
    # Calculate price_usd
    price_usd = product_in.cost_price * (1 + product_in.profit_margin)

    db_product = Product(**product_in.model_dump(), price_usd=price_usd)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    # Audit
    await AuditService.log_action(
        db, current_user.id, "CREATE", "products", f"Created product {db_product.name}"
    )

    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    *,
    db: AsyncSession = Depends(get_db),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a product.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    update_data = product_in.model_dump(exclude_unset=True)

    # Recalculate price if cost or margin changes
    new_cost = update_data.get("cost_price", product.cost_price)
    new_margin = update_data.get("profit_margin", product.profit_margin)

    if "cost_price" in update_data or "profit_margin" in update_data:
        update_data["price_usd"] = new_cost * (1 + new_margin)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Audit
    await AuditService.log_action(
        db, current_user.id, "UPDATE", "products", f"Updated product {product.id}"
    )

    return product


@router.delete("/{product_id}")
async def delete_product(
    *,
    db: AsyncSession = Depends(get_db),
    product_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a product (Hard Delete).
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Audit backup before delete
    # product_dump = json.dumps(jsonable_encoder(product))
    await AuditService.log_action(
        db,
        current_user.id,
        "DELETE",
        "products",
        f"Deleted product {product.id} ({product.name})",
    )

    await db.delete(product)
    await db.commit()
    return {"message": "Producto eliminado exitosamente", "id": product_id}
