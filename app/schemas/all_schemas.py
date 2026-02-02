from pydantic import BaseModel
from typing import List, Optional
from .notification import NotificationCreate, NotificationResponse as Notification
from .user import User, UserCreate, UserUpdate
from datetime import datetime
from enum import Enum


# Enums (Enumeradores para opciones fijas)
class PaymentMethod(str, Enum):
    CASH_BS = "Efectivo_BS"
    CASH_USD = "Efectivo_USD"
    PAGO_MOVIL = "Pago_Movil"
    ZELLE = "Zelle"
    BINANCE = "Binance"
    CASHEA = "Cashea"
    ZINLI = "Zinli"
    PAYPAL = "Paypal"
    CASH_COP = "Efectivo_COP"
    OTHER = "Other"


# -- VENTAS --
class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int
    matched_price: Optional[float] = None  # Sobreescritura opcional de precio


class PaymentCreate(BaseModel):
    method: PaymentMethod
    amount: float
    currency: str  # VES, USD
    exchange_rate: float


class SaleCreate(BaseModel):
    items: List[SaleItemCreate]
    payments: List[PaymentCreate]
    has_delivery: bool = False
    delivery_amount_usd: float = 0.0
    customer_id: Optional[int] = None


class SaleItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price_usd: float
    name: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    method: str
    amount: float
    currency: str
    exchange_rate: float

    class Config:
        from_attributes = True


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


# -- PROVEEDORES --
class ProviderBase(BaseModel):
    name: str
    rif: Optional[str] = None
    contact_info: Optional[str] = None


class ProviderCreate(ProviderBase):
    pass


class ProviderResponse(ProviderBase):
    id: int

    class Config:
        from_attributes = True


# -- COMPRAS / PEDIDOS --
class PurchaseItemCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    requested_quantity: int
    cost_price: Optional[float] = None


class PurchaseOrderCreate(BaseModel):
    provider_id: Optional[int] = None
    expected_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[PurchaseItemCreate]


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


class PurchaseItemReceipt(BaseModel):
    id: int
    received_quantity: int
    actual_cost: float


class PurchaseOrderReceipt(BaseModel):
    items: List[PurchaseItemReceipt]
