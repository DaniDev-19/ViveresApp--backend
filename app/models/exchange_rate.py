from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String, index=True)  # BCV, USDT, COP
    rate = Column(Float, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
