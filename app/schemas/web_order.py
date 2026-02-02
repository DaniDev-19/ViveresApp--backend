from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime


# --- Customer ---
class CustomerBase(BaseModel):
    cedula: str
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int

    class Config:
        from_attributes = True


# --- Web Order Items ---
class WebOrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    # Price is fetched from backend for security


class WebOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price_usd: float

    class Config:
        from_attributes = True


# --- Web Order ---
class WebOrderCreate(BaseModel):
    customer: CustomerCreate
    items: List[WebOrderItemCreate]
    payment_method: str
    transaction_ref: Optional[str] = None
    payment_proof_url: Optional[str] = None


class WebOrderResponse(BaseModel):
    id: int
    created_at: datetime
    status: str
    total_estimated_usd: float
    customer_data: Any  # JSON
    payment_method: str
    payment_proof_url: Optional[str]
    transaction_ref: Optional[str]
    items: List[WebOrderItemResponse]

    class Config:
        from_attributes = True
