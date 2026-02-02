from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.db.base_class import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    WORKER = "worker"
    INVENTORY_MANAGER = "inventory_manager"
    DELIVERY = "delivery"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.WORKER, nullable=False)
    is_active = Column(Boolean, default=True)
