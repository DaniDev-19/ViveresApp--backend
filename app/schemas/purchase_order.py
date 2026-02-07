from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from .purchase_item import PurchaseItemCreate, PurchaseItemResponse, PurchaseItemReceipt
from .provider import ProviderResponse

class PurchaseOrderBase(BaseModel):
    provider_id: Optional[int] = None
    expected_date: Optional[datetime] = None
    notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseItemCreate]

class PurchaseOrderResponse(BaseModel):
    id: int
    provider_id: Optional[int] = None
    expected_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: str
    created_at: datetime
    provider: Optional[ProviderResponse] = None
    items: List[PurchaseItemResponse] = []
    
    class Config:
        from_attributes = True

class PurchaseOrderReceipt(BaseModel):
    items: List[PurchaseItemReceipt]
