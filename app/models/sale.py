from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base_class import Base


class SaleStatus(str, enum.Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH_BS = "Efectivo_BS"
    CASH_USD = "Efectivo_USD"
    PAGO_MOVIL = "Pago_Movil"
    ZELLE = "Zelle"
    BINANCE = "Binance"
    CASHEA = "Cashea"
    ZINLI = "Zinli"
    PAYPAL = "Paypal"
    CASH_COP = "Efectivo_COP"
    OTHER = "Other"


class Sale(Base):
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    total_amount_usd = Column(Float, nullable=False)  # Subtotal + Tax
    total_tax_usd = Column(Float, default=0.0)

    # Delivery fields
    has_delivery = Column(Boolean, default=False)
    delivery_amount_usd = Column(Float, default=0.0)

    user_id = Column(Integer, ForeignKey("users.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    status = Column(String, default=SaleStatus.COMPLETED)

    items = relationship("SaleItem", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")
    user = relationship("User")
    customer = relationship("app.models.web_order.Customer")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)  # Price at moment of sale
    tax_rate = Column(Float, nullable=False)  # Tax at moment of sale
    applied_margin = Column(Float, nullable=True)  # Margin at moment of sale

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")


class Payment(Base):
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))

    method = Column(String, nullable=False)  # Store as string for flexibility or Enum
    amount = Column(Float, nullable=False)  # Original currency amount
    currency = Column(String, nullable=False)  # VES, USD
    exchange_rate = Column(Float, default=1.0)  # Rate used
    amount_usd_equivalent = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="payments")
