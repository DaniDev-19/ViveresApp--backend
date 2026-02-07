from pydantic import BaseModel
from typing import Optional

class CustomerBase(BaseModel):
    cedula: str
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    cedula: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int

    class Config:
        from_attributes = True
