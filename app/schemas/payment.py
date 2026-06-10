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
    # Refund methods (created by return/exchange flows)
    REFUND_CASH = "Refund_Cash"
    REFUND_EFECTIVO_BS = "Refund_Efectivo_BS"
    REFUND_EFECTIVO_USD = "Refund_Efectivo_USD"
    REFUND_PAGO_MOVIL = "Refund_Pago_Movil"
    REFUND_PAGO_MOVIL_ALT = "Refund_Pago Móvil"
    REFUND_ZELLE = "Refund_Zelle"
    REFUND_BINANCE = "Refund_Binance"
    REFUND_CASHEA = "Refund_Cashea"
    REFUND_ZINLI = "Refund_Zinli"
    REFUND_PAYPAL = "Refund_Paypal"
    REFUND_EFECTIVO_COP = "Refund_Efectivo_COP"
    REFUND_ORIGINAL = "Refund_Original"

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
