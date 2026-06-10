from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from app.db.base_class import Base


class SaleReturn(Base):
    __tablename__ = "sale_returns"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    total_refund_usd = Column(Float, nullable=False, default=0)
    refund_method = Column(String(50), nullable=False, default="credit_note")
    credit_note_code = Column(String(50), unique=True)
    reason = Column(Text)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sale = relationship("app.models.sale.Sale")
    user = relationship("app.models.user.User")
    items = relationship("SaleReturnItem", back_populates="return_", cascade="all, delete-orphan")


class SaleReturnItem(Base):
    __tablename__ = "sale_return_items"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"))
    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    subtotal_usd = Column(Float, nullable=False)

    return_ = relationship("SaleReturn", back_populates="items")
    product = relationship("app.models.product.Product", lazy="joined")

    @hybrid_property
    def product_name(self) -> str:
        return self.product.name if self.product else f"Producto #{self.product_id}"

    @hybrid_property
    def barcode(self) -> str:
        return self.product.barcode if self.product else ""