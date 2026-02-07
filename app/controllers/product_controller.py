from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.audit_service import AuditService
from app.services.image_service import image_service

class ProductController:
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100, search: str = None, public_only: bool = False):
        query = select(Product)
        if search:
            search_filter = or_(Product.name.ilike(f"%{search}%"), Product.barcode.ilike(f"%{search}%"))
            query = query.where(search_filter)
        if public_only:
            query = query.where(Product.is_public == True)
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, product_in: ProductCreate, user_id: int):
        price_usd = product_in.cost_price * (1 + product_in.profit_margin)
        db_obj = Product(**product_in.model_dump(), price_usd=price_usd)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        await AuditService.log_action(db, user_id, "CREATE", "products", f"Creado producto {db_obj.name}")
        return db_obj

    @staticmethod
    async def update(db: AsyncSession, product_id: int, product_in: ProductUpdate, user_id: int):
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            return None
        
        update_data = product_in.model_dump(exclude_unset=True)
        if "image_url" in update_data and product.image_url:
            # Si se está cambiando la imagen, borrar la anterior
            if update_data["image_url"] != product.image_url:
                image_service.delete_image(product.image_url)

        if "cost_price" in update_data or "profit_margin" in update_data:
            new_cost = update_data.get("cost_price", product.cost_price)
            new_margin = update_data.get("profit_margin", product.profit_margin)
            update_data["price_usd"] = new_cost * (1 + new_margin)
            
        for field, value in update_data.items():
            setattr(product, field, value)
            
        db.add(product)
        await db.commit()
        await db.refresh(product)
        await AuditService.log_action(db, user_id, "UPDATE", "products", f"Actualizado producto {product.id}")
        return product

    @staticmethod
    async def delete(db: AsyncSession, product_id: int, user_id: int):
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            return None
        # Borrar la imagen física antes de borrar el registro
        if product.image_url:
            image_service.delete_image(product.image_url)

        await AuditService.log_action(db, user_id, "DELETE", "products", f"Eliminado producto {product.id} ({product.name})")
        await db.delete(product)
        await db.commit()
        return product
