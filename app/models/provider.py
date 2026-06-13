from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    rif = Column(String, unique=True, index=True, nullable=True)
    contact_info = Column(String, nullable=True)
    is_delivery = Column(Boolean, default=False, nullable=False)

    orders = relationship("PurchaseOrder", back_populates="provider")
    products = relationship("app.models.product.Product", back_populates="provider")
