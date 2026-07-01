from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(String(50), nullable=False)  # 'purchase', 'sale', 'return', 'exchange_in', 'exchange_out', 'adjustment'
    quantity_change = Column(Integer, nullable=False)    # positive = in, negative = out
    reference_id = Column(Integer, nullable=True)        # ID of sale, purchase, etc.
    reference_type = Column(String(50), nullable=True)    # 'sale', 'purchase', 'return', 'exchange', 'adjustment'
    stock_before = Column(Integer, nullable=False)
    stock_after = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    product = relationship("app.models.product.Product")
    user = relationship("app.models.user.User")
