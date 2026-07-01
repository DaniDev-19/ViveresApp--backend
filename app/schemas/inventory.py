from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class InventoryMovementBase(BaseModel):
    product_id: int
    movement_type: str
    quantity_change: int
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None


class InventoryAdjustmentCreate(BaseModel):
    product_id: int
    quantity_change: int = Field(..., description="Cambio en la cantidad. Positivo para entrada, negativo para salida.")
    notes: Optional[str] = Field(None, description="Motivo del ajuste")

    @field_validator("quantity_change")
    @classmethod
    def quantity_change_not_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("quantity_change no puede ser 0")
        return v


class ProductSummary(BaseModel):
    id: int
    name: str
    barcode: Optional[str] = None


class UserSummary(BaseModel):
    id: int
    username: str


class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    movement_type: str
    quantity_change: int
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    stock_before: int
    stock_after: int
    notes: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    product: Optional[ProductSummary] = None
    user: Optional[UserSummary] = None

    class Config:
        from_attributes = True
