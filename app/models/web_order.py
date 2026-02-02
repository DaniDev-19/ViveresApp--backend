from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # WhatsApp formatted
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)

    orders = relationship("WebOrder", back_populates="customer")


class WebOrder(Base):
    __tablename__ = "web_orders"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Customer Link (Optional: User can be guest, but we store their data in customer_data json too)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Snapshot of customer data at time of order (in case profile changes)
    customer_data = Column(JSON, nullable=False)  # {name, phone, cedula, address}

    status = Column(
        String, default="pending_review"
    )  # pending_review, approved, rejected, completed

    total_estimated_usd = Column(Float, nullable=False)

    # Payment Info
    payment_method = Column(String, nullable=True)  # pago_movil, zinli, binance, zelle
    payment_proof_url = Column(String, nullable=True)  # S3/R2 URL
    transaction_ref = Column(String, nullable=True)

    # Items (One-to-Many? Or simple JSON for web orders to avoid heavy relational overhead before conversion?)
    # Strong relationship is better for reporting.
    items = relationship(
        "WebOrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    customer = relationship("Customer", back_populates="orders")


class WebOrderItem(Base):
    __tablename__ = "web_order_items"

    id = Column(Integer, primary_key=True, index=True)
    web_order_id = Column(Integer, ForeignKey("web_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    product_name = Column(String)  # Backup name
    quantity = Column(Integer)
    price_usd = Column(Float)  # Snapshot price

    order = relationship("WebOrder", back_populates="items")
    product = relationship("app.models.product.Product")
