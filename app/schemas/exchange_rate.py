from pydantic import BaseModel
from datetime import datetime

class ExchangeRateBase(BaseModel):
    currency: str
    rate: float

class ExchangeRateResponse(ExchangeRateBase):
    id: int
    fetched_at: datetime

    class Config:
        from_attributes = True
