from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base_class import Base

class PurchaseStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expected_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default=PurchaseStatus.DRAFT)
    notes = Column(Text, nullable=True)

    provider = relationship("app.models.provider.Provider", back_populates="orders")
    items = relationship("app.models.purchase_item.PurchaseItem", back_populates="order")
