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
    PAGO_MOVIL_ALT = "Pago Móvil"
    ZELLE = "Zelle"
    BINANCE = "Binance"
    CASHEA = "Cashea"
    ZINLI = "Zinli"
    PAYPAL = "Paypal"
    CASH_COP = "Efectivo_COP"
    OTHER = "Other"


from app.models.sale_item import SaleItem
from app.models.payment import Payment

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    total_amount_usd = Column(Float, nullable=False)
    total_tax_usd = Column(Float, default=0.0)

    has_delivery = Column(Boolean, default=False)
    delivery_amount_usd = Column(Float, default=0.0)

    user_id = Column(Integer, ForeignKey("users.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    status = Column(String, default=SaleStatus.COMPLETED)

    items = relationship("SaleItem", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")
    user = relationship("User")
    customer = relationship("app.models.customer.Customer")
