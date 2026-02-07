from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    rif = Column(String, unique=True, index=True, nullable=True)
    contact_info = Column(String, nullable=True)

    orders = relationship("PurchaseOrder", back_populates="provider")
