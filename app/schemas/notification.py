from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class NotificationBase(BaseModel):
    title: str
    message: str
    type: str = "info"  # info, success, warning, danger


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
