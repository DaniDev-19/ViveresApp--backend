from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    table_name: Optional[str] = None
    details: Optional[str] = None

class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
