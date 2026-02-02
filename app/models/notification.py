from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.db.base_class import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String(500), nullable=False)
    type = Column(String(50), default="info")  # info, success, warning, danger
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional: Link to a specific user (if it's not global for all workers/admins)
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Optional: Link to a specific resource (e.g., an order_id)
    # resource_id = Column(Integer, nullable=True)
    # resource_type = Column(String(50), nullable=True) # "web_order", "low_stock"
