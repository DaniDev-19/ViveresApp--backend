from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, index=True, nullable=False)  # CREATE, UPDATE, DELETE, LOGIN
    table_name = Column(String, index=True, nullable=True)
    details = Column(Text, nullable=True)  # JSON or text description
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
