from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Product(Base):
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Pricing fields
    cost_price = Column(Float, nullable=False)  # In USD
    profit_margin = Column(Float, default=0.30)  # 30% default
    tax_rate = Column(Float, default=0.16)  # 16% default
    price_usd = Column(Float, nullable=False)
    offer_price_usd = Column(Float, nullable=True)  # Precio oferta fijo (sin margen)

    stock_quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=5)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("app.models.category.Category", back_populates="products")

    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True, index=True)
    provider = relationship("app.models.provider.Provider", back_populates="products")

    image_url = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)  # Visible en catálogo web
    apply_iva_web = Column(Boolean, default=True)  # Si aplica IVA en pedidos web
