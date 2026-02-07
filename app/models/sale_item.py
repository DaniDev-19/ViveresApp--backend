from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    tax_rate = Column(Float, nullable=False)
    applied_margin = Column(Float, nullable=True)

    sale = relationship("Sale", back_populates="items")
    product = relationship("app.models.product.Product")
