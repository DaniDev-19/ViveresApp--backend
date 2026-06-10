from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ExchangeItemOutCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class ExchangeItemInCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price_usd: Optional[float] = Field(default=None, gt=0)


class ExchangeCreate(BaseModel):
    items_out: List[ExchangeItemOutCreate]
    items_in: List[ExchangeItemInCreate]
    payment_method: Optional[str] = None
    reason: Optional[str] = None


class ExchangeItemResponse(BaseModel):
    product_id: int
    product_name: str
    barcode: Optional[str] = None
    quantity: int
    unit_price_usd: float
    subtotal_usd: float

    class Config:
        from_attributes = True


class ExchangeResponse(BaseModel):
    id: int
    sale_id: int
    total_difference_usd: float
    payment_method: Optional[str]
    payment_amount_usd: float
    reason: Optional[str]
    status: str
    items_out: List[ExchangeItemResponse]
    items_in: List[ExchangeItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True