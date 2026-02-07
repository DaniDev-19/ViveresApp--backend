from sqlalchemy import Column, Integer, String, Float, Boolean
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

    stock_quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=5)


    image_url = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)  # Visible en catálogo web
    apply_iva_web = Column(Boolean, default=True)  # Si aplica IVA en pedidos web
