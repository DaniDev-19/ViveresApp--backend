from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from .web_order_item import WebOrderItemCreate, WebOrderItemResponse
from .customer import CustomerCreate

class WebOrderBase(BaseModel):
    customer: CustomerCreate
    payment_method: Optional[str] = None
    payment_proof_url: Optional[str] = None
    transaction_ref: Optional[str] = None
    delivery_type: Optional[str] = None
    delivery_cost: float = 0.0
    total_tax_usd: float = 0.0
    collect_tax: bool = True

class WebOrderCreate(WebOrderBase):
    items: List[WebOrderItemCreate]

class WebOrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_data: dict
    status: str
    total_estimated_usd: float
    payment_method: Optional[str]
    payment_proof_url: Optional[str]
    transaction_ref: Optional[str]
    delivery_type: Optional[str]
    delivery_cost: float
    total_tax_usd: float
    collect_tax: bool
    sale_id: Optional[int] = None
    created_at: datetime
    items: List[WebOrderItemResponse] = []

    class Config:
        from_attributes = True

class WebOrderPagination(BaseModel):
    items: List[WebOrderResponse]
    total: int
