from typing import Any, Optional
from pydantic import BaseModel
from datetime import datetime

class SettingBase(BaseModel):
    key: str
    value: Any

    class Config:
        from_attributes = True

class SettingResponse(SettingBase):
    updated_at: Optional[datetime] = None
