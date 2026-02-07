from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
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
    sales = relationship("Sale", back_populates="customer")
