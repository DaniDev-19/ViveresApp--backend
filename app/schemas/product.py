from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.schemas.category import CategoryResponse


class ProductBase(BaseModel):
    barcode: str
    name: str
    description: Optional[str] = None
    cost_price: float
    profit_margin: Optional[float] = 0.30
    tax_rate: Optional[float] = 0.16
    stock_quantity: int = Field(0, ge=0)
    min_stock_level: int = Field(5, ge=0)
    category_id: Optional[int] = None
    provider_id: Optional[int] = None
    offer_price_usd: Optional[float] = None
    image_url: Optional[str] = None
    is_public: bool = True
    apply_iva_web: bool = True

    @field_validator("cost_price")
    def validate_cost_price_base(cls, v):
        if v < 0:
            raise ValueError("El costo no puede ser negativo")
        return v

    @field_validator("offer_price_usd")
    def validate_offer_price_base(cls, v):
        if v is not None and v < 0:
            raise ValueError("El precio de oferta no puede ser negativo")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    barcode: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    profit_margin: Optional[float] = None
    tax_rate: Optional[float] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    provider_id: Optional[int] = None
    offer_price_usd: Optional[float] = None

    @field_validator("cost_price")
    def validate_cost_price(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError("El costo no puede ser negativo")
        return v

    @field_validator("offer_price_usd")
    def validate_offer_price(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError("El precio de oferta no puede ser negativo")
        return v
    image_url: Optional[str] = None
    is_public: Optional[bool] = None
    apply_iva_web: Optional[bool] = None


class BulkPriceUpdate(BaseModel):
    percentage: float = Field(..., description="Porcentaje de ajuste. Ej: 10 para +10%, -5 para -5%")
    scope: str = Field("all", description="'all', 'category', o 'selective'")
    category_id: Optional[int] = None
    product_ids: Optional[List[int]] = None
    update_offers: bool = True


class ProductResponse(ProductBase):
    id: int
    price_usd: float
    provider_id: Optional[int] = None
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True

