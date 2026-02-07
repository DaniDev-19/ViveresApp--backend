from typing import Optional
from pydantic import BaseModel

class PurchaseItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    requested_quantity: int
    cost_price: Optional[float] = None

class PurchaseItemCreate(PurchaseItemBase):
    pass

class PurchaseItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: Optional[str]
    requested_quantity: int
    cost_price: Optional[float]
    received_quantity: int
    status: str

    class Config:
        from_attributes = True

class PurchaseItemReceipt(BaseModel):
    id: int
    received_quantity: int
    actual_cost: float
