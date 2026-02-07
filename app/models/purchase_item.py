from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base

class PurchaseItemStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    MISMATCH = "mismatch"

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchase_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    product_name = Column(String, nullable=True)
    requested_quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, default=0)
    cost_price = Column(Float, nullable=True)

    status = Column(String, default=PurchaseItemStatus.PENDING)

    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("app.models.product.Product")
