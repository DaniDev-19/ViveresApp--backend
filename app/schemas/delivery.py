from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.schemas.user import UserResponse
from app.schemas.provider import ProviderResponse

class DeliveryBase(BaseModel):
    description: str
    address: Optional[str] = None
    items_detail: Optional[str] = None
    cost_usd: Optional[float] = None
    status: str = "pending"
    delivery_user_id: Optional[int] = None
    provider_id: Optional[int] = None
    sale_id: Optional[int] = None

class DeliveryCreate(DeliveryBase):
    pass

class DeliveryUpdate(BaseModel):
    description: Optional[str] = None
    address: Optional[str] = None
    items_detail: Optional[str] = None
    cost_usd: Optional[float] = None
    status: Optional[str] = None
    delivery_user_id: Optional[int] = None
    provider_id: Optional[int] = None
    sale_id: Optional[int] = None

class DeliveryResponse(DeliveryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    delivery_user: Optional[UserResponse] = None
    provider: Optional[ProviderResponse] = None

    class Config:
        from_attributes = True
