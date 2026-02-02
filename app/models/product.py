from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Pricing fields
    cost_price = Column(Float, nullable=False)  # In USD
    profit_margin = Column(Float, default=0.30)  # 30% default
    tax_rate = Column(Float, default=0.16)  # 16% default

    # We store the calculated price to make querying easier (e.g. filter by price)
    # This must be updated whenever cost or margin changes.
    price_usd = Column(Float, nullable=False)

    stock_quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=5)

    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)  # Visible en catálogo web

    category = relationship("Category", back_populates="products")
