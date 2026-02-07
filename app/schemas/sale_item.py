from typing import Optional
from pydantic import BaseModel

class SaleItemBase(BaseModel):
    product_id: int
    quantity: int
    matched_price: Optional[float] = None

class SaleItemCreate(SaleItemBase):
    pass

class SaleItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price_usd: float
    name: Optional[str] = None

    class Config:
        from_attributes = True
