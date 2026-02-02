from typing import Optional
from pydantic import BaseModel


class ProductBase(BaseModel):
    barcode: str
    name: str
    description: Optional[str] = None
    cost_price: float
    profit_margin: Optional[float] = 0.30
    tax_rate: Optional[float] = 0.16
    stock_quantity: int = 0
    min_stock_level: int = 5
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    is_public: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    barcode: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    profit_margin: Optional[float] = None
    tax_rate: Optional[float] = None
    stock_quantity: Optional[int] = None
    min_stock_level: Optional[int] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    is_public: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    price_usd: float  # Calculated field

    class Config:
        from_attributes = True
