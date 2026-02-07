from pydantic import BaseModel

class WebOrderItemBase(BaseModel):
    product_id: int
    quantity: int

class WebOrderItemCreate(WebOrderItemBase):
    pass

class WebOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price_usd: float

    class Config:
        from_attributes = True
