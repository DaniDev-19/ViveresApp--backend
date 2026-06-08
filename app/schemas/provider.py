from pydantic import BaseModel
from typing import Optional

class ProviderBase(BaseModel):
    name: str
    rif: Optional[str] = None
    contact_info: Optional[str] = None
    is_delivery: Optional[bool] = False

class ProviderCreate(ProviderBase):
    pass

class ProviderResponse(ProviderBase):
    id: int

    class Config:
        from_attributes = True
