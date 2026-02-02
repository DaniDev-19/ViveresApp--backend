from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
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


class PurchaseItemStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    MISMATCH = "mismatch"


class Provider(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    rif = Column(String, unique=True, index=True, nullable=True)
    contact_info = Column(String, nullable=True)

    orders = relationship("PurchaseOrder", back_populates="provider")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expected_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default=PurchaseStatus.DRAFT)
    notes = Column(Text, nullable=True)

    provider = relationship("Provider", back_populates="orders")
    items = relationship("PurchaseItem", back_populates="order")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchase_orders.id"))
    product_id = Column(
        Integer, ForeignKey("products.id"), nullable=True
    )  # Nullable if new product

    product_name = Column(String, nullable=True)  # Snapshot name or for new products
    requested_quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, default=0)
    cost_price = Column(Float, nullable=True)  # Actual cost upon purchase

    status = Column(String, default=PurchaseItemStatus.PENDING)

    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
