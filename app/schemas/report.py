from pydantic import BaseModel
from typing import List

class LabelRequest(BaseModel):
    product_id: int
    name: str
    price: float
    quantity: int = 1
