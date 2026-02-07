from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class WebOrderItem(Base):
    __tablename__ = "web_order_items"

    id = Column(Integer, primary_key=True, index=True)
    web_order_id = Column(Integer, ForeignKey("web_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    product_name = Column(String)
    quantity = Column(Integer)
    price_usd = Column(Float)

    order = relationship("WebOrder", back_populates="items")
    product = relationship("app.models.product.Product")
