from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    items_detail = Column(Text, nullable=True)
    cost_usd = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    delivery_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    provider_id = Column(Integer, ForeignKey("providers.id", ondelete="SET NULL"), nullable=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    delivery_user = relationship("User", foreign_keys=[delivery_user_id])
    provider = relationship("Provider")
    sale = relationship("Sale")
