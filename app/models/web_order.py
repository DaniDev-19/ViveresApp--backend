from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


from app.models.customer import Customer


from app.models.web_order_item import WebOrderItem

class WebOrder(Base):
    __tablename__ = "web_orders"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_data = Column(JSON, nullable=False)

    status = Column(String, default="pending_review")
    total_estimated_usd = Column(Float, nullable=False)
    total_tax_usd = Column(Float, default=0.0)
    collect_tax = Column(Boolean, default=True)

    payment_method = Column(String, nullable=True)
    payment_proof_url = Column(String, nullable=True)
    transaction_ref = Column(String, nullable=True)

    delivery_type = Column(String, nullable=True)
    delivery_cost = Column(Float, default=0.0)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)

    items = relationship("WebOrderItem", back_populates="order", cascade="all, delete-orphan")
    customer = relationship("app.models.customer.Customer", back_populates="orders")
