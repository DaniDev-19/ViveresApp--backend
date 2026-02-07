from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .sale_item import SaleItemCreate, SaleItemResponse
from .payment import PaymentCreate, PaymentResponse

class SaleBase(BaseModel):
    has_delivery: bool = False
    delivery_amount_usd: float = 0.0
    customer_id: Optional[int] = None

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]
    payments: List[PaymentCreate]

class SaleResponse(BaseModel):
    id: int
    total_amount_usd: float
    total_tax_usd: float = 0.0
    has_delivery: bool = False
    delivery_amount_usd: float = 0.0
    status: str
    created_at: datetime
    items: List[SaleItemResponse] = []
    payments: List[PaymentResponse] = []
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_cedula: Optional[str] = None

    class Config:
        from_attributes = True
