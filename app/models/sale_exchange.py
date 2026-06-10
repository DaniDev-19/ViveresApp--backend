from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from app.db.base_class import Base


class SaleExchange(Base):
    __tablename__ = "sale_exchanges"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    total_difference_usd = Column(Float, nullable=False, default=0)
    payment_method = Column(String(50))
    payment_amount_usd = Column(Float, default=0)
    reason = Column(Text)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sale = relationship("app.models.sale.Sale")
    user = relationship("app.models.user.User")
    items_out = relationship("SaleExchangeItemOut", back_populates="exchange", cascade="all, delete-orphan")
    items_in = relationship("SaleExchangeItemIn", back_populates="exchange", cascade="all, delete-orphan")


class SaleExchangeItemOut(Base):
    __tablename__ = "sale_exchange_items_out"

    id = Column(Integer, primary_key=True, index=True)
    exchange_id = Column(Integer, ForeignKey("sale_exchanges.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"))
    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    subtotal_usd = Column(Float, nullable=False)

    exchange = relationship("SaleExchange", back_populates="items_out")
    product = relationship("app.models.product.Product", lazy="joined")

    @hybrid_property
    def product_name(self) -> str:
        return self.product.name if self.product else f"Producto #{self.product_id}"

    @hybrid_property
    def barcode(self) -> str:
        return self.product.barcode if self.product else ""


class SaleExchangeItemIn(Base):
    __tablename__ = "sale_exchange_items_in"

    id = Column(Integer, primary_key=True, index=True)
    exchange_id = Column(Integer, ForeignKey("sale_exchanges.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"))
    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    subtotal_usd = Column(Float, nullable=False)

    exchange = relationship("SaleExchange", back_populates="items_in")
    product = relationship("app.models.product.Product", lazy="joined")

    @hybrid_property
    def product_name(self) -> str:
        return self.product.name if self.product else f"Producto #{self.product_id}"

    @hybrid_property
    def barcode(self) -> str:
        return self.product.barcode if self.product else ""