from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_  # <--- Importamos and_ para la intersección de palabras
from sqlalchemy.orm import selectinload
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.audit_service import AuditService
from app.services.image_service import image_service

class ProductController:
    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        public_only: bool = False,
        category_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        in_stock_only: bool = False,
        stock_eq: Optional[int] = None,
        stock_lt: Optional[int] = None,
    ):
        query = select(Product).options(selectinload(Product.category))
        
        if search:
            term = search.strip()
            
            # Si es puramente un código numérico largo (ej. código de barras)
            if term.isdigit() and len(term) >= 4:
                search_filter = or_(
                    Product.barcode == term,
                    Product.barcode.ilike(f"%{term}%"),
                    Product.name.ilike(f"%{term}%"),
                )
                query = query.where(search_filter)
            else:
                # TRUCO MULTI-PALABRA: Dividimos por espacios ("muñon yaris" -> ["muñon", "yaris"])
                words = [w for w in term.split() if len(w) > 0]
                
                if words:
                    word_filters = []
                    for word in words:
                        # Para cada palabra individual, exigimos que combine con el nombre o código de barras
                        word_filters.append(
                            or_(
                                Product.name.ilike(f"%{word}%"),
                                Product.barcode.ilike(f"%{word}%")
                            )
                        )
                    # Forzamos con AND a que todas las palabras de la lista sumen condiciones obligatorias
                    query = query.where(and_(*word_filters))

        if public_only:
            query = query.where(Product.is_public == True)
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if provider_id is not None:
            query = query.where(Product.provider_id == provider_id)
        if in_stock_only:
            query = query.where(Product.stock_quantity > 0)
        if stock_eq is not None:
            query = query.where(Product.stock_quantity == stock_eq)
        if stock_lt is not None:
            query = query.where(Product.stock_quantity < stock_lt)

        query = query.order_by(Product.name.asc())
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    def _calc_price_usd(cost: float, margin: float | None) -> float:
        return cost * (1 + (margin if margin is not None else 0.30))

    @staticmethod
    async def _get_with_category(db: AsyncSession, product_id: int):
        result = await db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
        )
        return result.scalars().first()

    @staticmethod
    async def create(db: AsyncSession, product_in: ProductCreate, user_id: int):
        from fastapi import HTTPException, status
        if product_in.barcode:
            stmt = select(Product).where(Product.barcode == product_in.barcode)
            result = await db.execute(stmt)
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El código de barras '{product_in.barcode}' ya está registrado para otro producto."
                )

        margin = product_in.profit_margin if product_in.profit_margin is not None else 0.30
        price_usd = ProductController._calc_price_usd(product_in.cost_price, margin)
        db_obj = Product(**product_in.model_dump(), price_usd=price_usd)
        db.add(db_obj)
        await db.flush()

        if db_obj.stock_quantity > 0:
            from app.controllers.inventory_controller import InventoryController
            await InventoryController.register_movement(
                db=db,
                product_id=db_obj.id,
                movement_type="adjustment",
                quantity_change=db_obj.stock_quantity,
                reference_id=None,
                reference_type="adjustment",
                notes="Stock inicial en creación de producto",
                user_id=user_id,
                commit=False
            )

        await db.commit()
        product = await ProductController._get_with_category(db, db_obj.id)
        await AuditService.log_action(db, user_id, "CREATE", "products", f"Creado producto {product.name}")
        return product

    @staticmethod
    async def update(db: AsyncSession, product_id: int, product_in: ProductUpdate, user_id: int):
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            return None

        update_data = product_in.model_dump(exclude_unset=True)
        if "image_url" in update_data and product.image_url:
            if update_data["image_url"] != product.image_url:
                image_service.delete_image(product.image_url)

        if "cost_price" in update_data or "profit_margin" in update_data:
            new_cost = update_data.get("cost_price", product.cost_price)
            new_margin = update_data.get(
                "profit_margin",
                product.profit_margin if product.profit_margin is not None else 0.30,
            )
            update_data["price_usd"] = ProductController._calc_price_usd(new_cost, new_margin)

        old_stock = product.stock_quantity
        for field, value in update_data.items():
            setattr(product, field, value)

        db.add(product)
        await db.flush()

        if old_stock != product.stock_quantity:
            from app.controllers.inventory_controller import InventoryController
            await InventoryController.register_movement(
                db=db,
                product_id=product.id,
                movement_type="adjustment",
                quantity_change=product.stock_quantity - old_stock,
                reference_id=None,
                reference_type="adjustment",
                notes="Ajuste de stock en edición de producto",
                user_id=user_id,
                commit=False
            )

        await db.commit()
        product = await ProductController._get_with_category(db, product_id)
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

        await AuditService.log_action(db, user_id, "DELETE", "products", f"Eliminado producto {product.id} ({product.name})", commit=False)
        await db.delete(product)
        await db.commit()
        return product

    @staticmethod
    async def bulk_price_update(db: AsyncSession, bulk_in, user_id: int):
        query = select(Product)
        if bulk_in.scope == "category" and bulk_in.category_id is not None:
            query = query.where(Product.category_id == bulk_in.category_id)
        elif bulk_in.scope == "selective" and bulk_in.product_ids:
            query = query.where(Product.id.in_(bulk_in.product_ids))
        elif bulk_in.scope != "all":
            return {"updated_count": 0, "message": "Ámbito de ajuste no válido"}

        result = await db.execute(query)
        products = result.scalars().all()

        if not products:
            return {"updated_count": 0, "message": "No se encontraron productos para actualizar"}

        factor = 1.0 + (bulk_in.percentage / 100.0)
        updated_count = 0

        for product in products:
            new_cost = round(max(0.0, product.cost_price * factor), 4)
            product.cost_price = new_cost
            
            margin = product.profit_margin if product.profit_margin is not None else 0.30
            product.price_usd = round(ProductController._calc_price_usd(new_cost, margin), 4)
            
            if bulk_in.update_offers and product.offer_price_usd is not None and product.offer_price_usd > 0:
                product.offer_price_usd = round(max(0.0, product.offer_price_usd * factor), 4)

            db.add(product)
            updated_count += 1

        await db.commit()

        details = (
            f"Ajuste masivo de precios del {bulk_in.percentage:+}% en ámbito '{bulk_in.scope}'. "
            f"Productos afectados: {updated_count}."
        )
        await AuditService.log_action(db, user_id, "BULK_UPDATE", "products", details)

        return {
            "success": True,
            "updated_count": updated_count,
            "percentage": bulk_in.percentage,
            "scope": bulk_in.scope,
            "message": f"Se actualizaron {updated_count} productos exitosamente."
        }

    @staticmethod
    async def bulk_web_settings_update(db: AsyncSession, bulk_in, user_id: int):
        query = select(Product)
        if bulk_in.scope == "category" and bulk_in.category_id is not None:
            query = query.where(Product.category_id == bulk_in.category_id)
        elif bulk_in.scope == "selective" and bulk_in.product_ids:
            query = query.where(Product.id.in_(bulk_in.product_ids))
        elif bulk_in.scope != "all":
            return {"updated_count": 0, "message": "Ámbito de ajuste no válido"}

        result = await db.execute(query)
        products = result.scalars().all()

        if not products:
            return {"updated_count": 0, "message": "No se encontraron productos para actualizar"}

        updated_count = 0
        for product in products:
            changed = False
            if bulk_in.update_is_public:
                product.is_public = bulk_in.is_public_value
                changed = True
            if bulk_in.update_apply_iva_web:
                product.apply_iva_web = bulk_in.apply_iva_web_value
                changed = True

            if changed:
                db.add(product)
                updated_count += 1

        await db.commit()

        details = (
            f"Ajuste masivo de configuración web en ámbito '{bulk_in.scope}'. "
            f"Productos afectados: {updated_count}."
        )
        await AuditService.log_action(db, user_id, "BULK_UPDATE_WEB", "products", details)

        return {
            "success": True,
            "updated_count": updated_count,
            "scope": bulk_in.scope,
            "message": f"Se actualizó la configuración web de {updated_count} productos exitosamente."
        }