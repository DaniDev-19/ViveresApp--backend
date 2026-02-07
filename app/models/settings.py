from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
