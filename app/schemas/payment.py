from pydantic import BaseModel
from enum import Enum

class PaymentMethod(str, Enum):
    CASH_BS = "Efectivo_BS"
    CASH_USD = "Efectivo_USD"
    PAGO_MOVIL = "Pago_Movil"
    PAGO_MOVIL_ALT = "Pago Móvil"
    ZELLE = "Zelle"
    BINANCE = "Binance"
    CASHEA = "Cashea"
    ZINLI = "Zinli"
    PAYPAL = "Paypal"
    CASH_COP = "Efectivo_COP"
    OTHER = "Other"

class PaymentBase(BaseModel):
    method: PaymentMethod
    amount: float
    currency: str
    exchange_rate: float

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    class Config:
        from_attributes = True
