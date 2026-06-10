from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ReturnItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class ReturnCreate(BaseModel):
    items: List[ReturnItemCreate]
    refund_method: str = Field(default="credit_note", pattern="^(cash|credit_note|original)$")
    reason: Optional[str] = None


class ReturnItemResponse(BaseModel):
    product_id: int
    product_name: str
    barcode: Optional[str] = None
    quantity: int
    unit_price_usd: float
    subtotal_usd: float

    class Config:
        from_attributes = True


class ReturnResponse(BaseModel):
    id: int
    sale_id: int
    total_refund_usd: float
    refund_method: str
    credit_note_code: Optional[str]
    reason: Optional[str]
    status: str
    items: List[ReturnItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True