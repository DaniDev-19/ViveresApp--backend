from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from .sale_item import SaleItemCreate, SaleItemResponse
from .payment import PaymentCreate, PaymentResponse

class SaleBase(BaseModel):
    has_delivery: bool = False
    delivery_amount_usd: float = 0.0
    charge_binance_tax: bool = False
    customer_id: int
    
    @field_validator('customer_id')
    @classmethod
    def validate_customer_id(cls, v):
        if v == 0:
            raise ValueError('Debe seleccionar un cliente para realizar la venta')
        if v < 0:
            raise ValueError('El ID del cliente debe ser un número positivo')
        return v

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]
    payments: List[PaymentCreate]

class SaleResponse(BaseModel):
    id: int
    total_amount_usd: float
    total_tax_usd: float = 0.0
    net_amount_usd: Optional[float] = None
    has_delivery: bool = False
    delivery_amount_usd: float = 0.0
    status: str
    created_at: datetime
    items: List[SaleItemResponse] = []
    payments: List[PaymentResponse] = []
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_cedula: Optional[str] = None
    customer_email: Optional[str] = None


    class Config:
        from_attributes = True


class SaleEmailSend(BaseModel):
    email: str
    html_content: str


class CustomEmailSend(BaseModel):
    email: str
    subject: str
    html_content: str


